"""
PactManager - Consumer-driven contract testing module

Implements Pact contract creation, publishing, verification, and Can-I-Deploy
workflows for consumer-driven contract testing with Pact broker integration.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class PactError(Exception):
    """Base exception for Pact-related errors."""

    pass


class BrokerError(PactError):
    """Exception for Pact broker connectivity/authentication errors."""

    pass


class ContractError(PactError):
    """Exception for invalid contract format errors."""

    pass


class VerificationError(PactError):
    """Exception for provider verification failures."""

    pass


class StateSetupError(PactError):
    """Exception for provider state setup errors."""

    pass


class DeploymentStatus(Enum):
    """Deployment status for Can-I-Deploy checks."""

    DEPLOYABLE = "deployable"
    NOT_DEPLOYABLE = "not_deployable"
    UNKNOWN = "unknown"


@dataclass
class Interaction:
    """Represents a Pact interaction between consumer and provider."""

    description: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    state: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert interaction to dictionary format."""
        result = {
            "description": self.description,
            "request": self.request,
            "response": self.response,
        }
        if self.state:
            result["providerState"] = self.state
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Interaction":
        """Create Interaction from dictionary."""
        return cls(
            description=data["description"],
            request=data["request"],
            response=data["response"],
            state=data.get("providerState"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PactContract:
    """Represents a Pact contract between consumer and provider."""

    consumer: str
    provider: str
    interactions: List[Interaction]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary format."""
        return {
            "consumer": {"name": self.consumer},
            "provider": {"name": self.provider},
            "interactions": [i.to_dict() for i in self.interactions],
            "metadata": {
                "pactSpecification": {"version": "3.0.0"},
                **self.metadata,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PactContract":
        """Create PactContract from dictionary."""
        return cls(
            consumer=data["consumer"]["name"],
            provider=data["provider"]["name"],
            interactions=[
                Interaction.from_dict(i) for i in data.get("interactions", [])
            ],
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        """Convert contract to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def save(self, path: Path) -> None:
        """Save contract to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())
        logger.info(f"Saved contract to {path}")


@dataclass
class VerificationResult:
    """Result of provider verification."""

    success: bool
    provider: str
    consumer: str
    pact_version: str
    timestamp: str
    failures: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "provider": self.provider,
            "consumer": self.consumer,
            "pactVersion": self.pact_version,
            "timestamp": self.timestamp,
            "failures": self.failures,
            "metadata": self.metadata,
        }


@dataclass
class CanIDeployResult:
    """Result of Can-I-Deploy check."""

    status: DeploymentStatus
    participant: str
    version: str
    environment: str
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)

    def is_deployable(self) -> bool:
        """Check if deployment is safe."""
        return self.status == DeploymentStatus.DEPLOYABLE


class PactManager:
    """
    Manager for consumer-driven contract testing with Pact.

    Provides functionality for creating Pact contracts, publishing to broker,
    verifying providers, and Can-I-Deploy checks.
    """

    def __init__(
        self,
        consumer: Optional[str] = None,
        provider: Optional[str] = None,
        broker_url: Optional[str] = None,
        broker_username: Optional[str] = None,
        broker_password: Optional[str] = None,
        broker_token: Optional[str] = None,
        pacts_dir: Optional[Path] = None,
    ):
        """
        Initialize PactManager.

        Args:
            consumer: Consumer application name
            provider: Provider application name
            broker_url: Pact broker URL
            broker_username: Broker username for basic auth
            broker_password: Broker password for basic auth
            broker_token: Broker token for bearer auth
            pacts_dir: Directory for storing pact files
        """
        self.consumer = consumer
        self.provider = provider
        self.broker_url = broker_url.rstrip("/") if broker_url else None
        self.broker_username = broker_username
        self.broker_password = broker_password
        self.broker_token = broker_token
        self.pacts_dir = pacts_dir or Path.cwd() / "pacts"
        self.interactions: List[Interaction] = []
        self.state_handlers: Dict[str, Callable] = {}

        # Setup auth
        self._auth: Optional[Union[HTTPBasicAuth, str]] = None
        if broker_token:
            self._auth = f"Bearer {broker_token}"
        elif broker_username and broker_password:
            self._auth = HTTPBasicAuth(broker_username, broker_password)

    def add_interaction(self, interaction: Union[Interaction, Dict[str, Any]]) -> None:
        """
        Add an interaction to the current contract.

        Args:
            interaction: Interaction object or dictionary

        Raises:
            ContractError: If interaction format is invalid
        """
        try:
            if isinstance(interaction, dict):
                interaction = Interaction.from_dict(interaction)
            self.interactions.append(interaction)
            logger.debug(f"Added interaction: {interaction.description}")
        except (KeyError, TypeError) as e:
            raise ContractError(f"Invalid interaction format: {e}") from e

    def create_consumer_contract(
        self,
        consumer: Optional[str] = None,
        provider: Optional[str] = None,
        interactions: Optional[List[Union[Interaction, Dict[str, Any]]]] = None,
    ) -> PactContract:
        """
        Create a Pact contract from consumer tests.

        Args:
            consumer: Consumer name (overrides instance consumer)
            provider: Provider name (overrides instance provider)
            interactions: List of interactions (uses added interactions if None)

        Returns:
            PactContract object

        Raises:
            ContractError: If consumer/provider not specified or no interactions
        """
        consumer_name = consumer or self.consumer
        provider_name = provider or self.provider

        if not consumer_name or not provider_name:
            raise ContractError("Consumer and provider names must be specified")

        interaction_list = []
        if interactions:
            for item in interactions:
                if isinstance(item, dict):
                    interaction_list.append(Interaction.from_dict(item))
                else:
                    interaction_list.append(item)
        else:
            interaction_list = self.interactions

        if not interaction_list:
            raise ContractError("At least one interaction must be specified")

        contract = PactContract(
            consumer=consumer_name,
            provider=provider_name,
            interactions=interaction_list,
            metadata={"createdAt": datetime.utcnow().isoformat()},
        )

        logger.info(
            f"Created contract between {consumer_name} and {provider_name} "
            f"with {len(interaction_list)} interactions"
        )
        return contract

    def publish_to_broker(
        self,
        pact: Union[PactContract, Path, str],
        version: str,
        tags: Optional[List[str]] = None,
        branch: Optional[str] = None,
        build_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish Pact contract to broker.

        Args:
            pact: PactContract object, file path, or JSON string
            version: Consumer version
            tags: Version tags (e.g., ['main', 'prod'])
            branch: Git branch name
            build_url: CI build URL

        Returns:
            Broker response data

        Raises:
            BrokerError: If broker URL not configured or publish fails
            ContractError: If pact format is invalid
        """
        if not self.broker_url:
            raise BrokerError("Broker URL not configured")

        # Parse pact
        if isinstance(pact, PactContract):
            contract = pact
            pact_data = contract.to_dict()
        elif isinstance(pact, (Path, str)):
            path = Path(pact)
            if not path.exists():
                raise ContractError(f"Pact file not found: {path}")
            pact_data = json.loads(path.read_text())
            contract = PactContract.from_dict(pact_data)
        else:
            raise ContractError("Invalid pact type")

        consumer_name = contract.consumer
        provider_name = contract.provider

        # Publish pact
        url = (
            f"{self.broker_url}/pacts/provider/{provider_name}"
            f"/consumer/{consumer_name}/version/{version}"
        )

        headers = {"Content-Type": "application/json"}
        if isinstance(self._auth, str):
            headers["Authorization"] = self._auth

        try:
            response = requests.put(
                url,
                json=pact_data,
                headers=headers,
                auth=self._auth if isinstance(self._auth, HTTPBasicAuth) else None,
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"Published pact to broker: {url}")
        except requests.RequestException as e:
            raise BrokerError(f"Failed to publish pact: {e}") from e

        # Tag version
        if tags:
            for tag in tags:
                self._tag_version(consumer_name, version, tag)

        # Set branch (Pactflow feature)
        if branch:
            self._set_branch(consumer_name, version, branch)

        return {
            "consumer": consumer_name,
            "provider": provider_name,
            "version": version,
            "tags": tags or [],
            "branch": branch,
            "broker_url": url,
            "published_at": datetime.utcnow().isoformat(),
        }

    def _tag_version(self, participant: str, version: str, tag: str) -> None:
        """Tag a participant version."""
        url = (
            f"{self.broker_url}/pacticipants/{participant}"
            f"/versions/{version}/tags/{tag}"
        )
        headers = {}
        if isinstance(self._auth, str):
            headers["Authorization"] = self._auth

        try:
            response = requests.put(
                url,
                headers=headers,
                auth=self._auth if isinstance(self._auth, HTTPBasicAuth) else None,
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"Tagged {participant} version {version} with '{tag}'")
        except requests.RequestException as e:
            logger.warning(f"Failed to tag version: {e}")

    def _set_branch(self, participant: str, version: str, branch: str) -> None:
        """Set branch for a participant version (Pactflow feature)."""
        url = (
            f"{self.broker_url}/pacticipants/{participant}"
            f"/branches/{branch}/versions/{version}"
        )
        headers = {}
        if isinstance(self._auth, str):
            headers["Authorization"] = self._auth

        try:
            response = requests.put(
                url,
                headers=headers,
                auth=self._auth if isinstance(self._auth, HTTPBasicAuth) else None,
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"Set {participant} version {version} to branch '{branch}'")
        except requests.RequestException as e:
            logger.warning(f"Failed to set branch: {e}")

    def get_pacts_for_verification(
        self,
        provider: Optional[str] = None,
        consumer_version_selectors: Optional[List[Dict[str, str]]] = None,
        enable_pending: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Fetch Pact contracts for provider verification.

        Args:
            provider: Provider name (uses instance provider if None)
            consumer_version_selectors: Version selectors for consumers
                e.g., [{"tag": "main"}, {"branch": "develop"}]
            enable_pending: Include pending pacts

        Returns:
            List of pact URLs and metadata

        Raises:
            BrokerError: If broker URL not configured or fetch fails
        """
        if not self.broker_url:
            raise BrokerError("Broker URL not configured")

        provider_name = provider or self.provider
        if not provider_name:
            raise BrokerError("Provider name not specified")

        # Use pacts for verification endpoint
        url = f"{self.broker_url}/pacts/provider/{provider_name}" f"/for-verification"

        headers = {"Content-Type": "application/json"}
        if isinstance(self._auth, str):
            headers["Authorization"] = self._auth

        # Default selectors
        if not consumer_version_selectors:
            consumer_version_selectors = [
                {"tag": "main"},
                {"tag": "master"},
                {"deployed": "true"},
            ]

        payload = {
            "consumerVersionSelectors": consumer_version_selectors,
            "includePendingStatus": enable_pending,
            "includeWipPactsSince": datetime.utcnow().date().isoformat(),
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                auth=self._auth if isinstance(self._auth, HTTPBasicAuth) else None,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            pacts = data.get("_embedded", {}).get("pacts", [])
            logger.info(f"Retrieved {len(pacts)} pacts for verification")
            return pacts
        except requests.RequestException as e:
            raise BrokerError(f"Failed to fetch pacts for verification: {e}") from e

    def register_state_handler(self, state: str, handler: Callable) -> None:
        """
        Register a provider state handler.

        Args:
            state: State name
            handler: Callable to setup the state
        """
        self.state_handlers[state] = handler
        logger.debug(f"Registered state handler for '{state}'")

    def verify_provider(
        self,
        provider: Optional[str] = None,
        base_url: Optional[str] = None,
        states: Optional[Dict[str, Callable]] = None,
        pact_urls: Optional[List[str]] = None,
        publish_results: bool = True,
        provider_version: Optional[str] = None,
        provider_tags: Optional[List[str]] = None,
    ) -> VerificationResult:
        """
        Verify provider against Pact contracts.

        Args:
            provider: Provider name
            base_url: Provider base URL
            states: Provider state handlers
            pact_urls: List of pact URLs to verify
            publish_results: Publish verification results to broker
            provider_version: Provider version for result publishing
            provider_tags: Provider tags for result publishing

        Returns:
            VerificationResult object

        Raises:
            VerificationError: If verification fails
            StateSetupError: If state setup fails
        """
        provider_name = provider or self.provider
        if not provider_name:
            raise VerificationError("Provider name not specified")

        if not base_url:
            raise VerificationError("Provider base URL not specified")

        # Merge state handlers
        all_handlers = {**self.state_handlers}
        if states:
            all_handlers.update(states)

        # Get pacts to verify
        if not pact_urls:
            pacts = self.get_pacts_for_verification(provider_name)
            pact_urls = [p["_links"]["self"]["href"] for p in pacts]

        if not pact_urls:
            logger.warning(f"No pacts found for provider {provider_name}")
            return VerificationResult(
                success=True,
                provider=provider_name,
                consumer="",
                pact_version="",
                timestamp=datetime.utcnow().isoformat(),
            )

        # Verify each pact
        all_failures = []
        all_consumers = []

        for pact_url in pact_urls:
            try:
                failures = self._verify_single_pact(pact_url, base_url, all_handlers)
                all_failures.extend(failures)

                # Extract consumer name from pact URL
                consumer_name = self._extract_consumer_from_url(pact_url)
                all_consumers.append(consumer_name)
            except Exception as e:
                logger.error(f"Verification failed for {pact_url}: {e}")
                all_failures.append(
                    {
                        "pact_url": pact_url,
                        "error": str(e),
                        "type": type(e).__name__,
                    }
                )

        # Create result
        result = VerificationResult(
            success=len(all_failures) == 0,
            provider=provider_name,
            consumer=", ".join(set(all_consumers)),
            pact_version="3.0.0",
            timestamp=datetime.utcnow().isoformat(),
            failures=all_failures,
        )

        # Publish results
        if publish_results and self.broker_url and provider_version:
            self._publish_verification_results(result, provider_version, provider_tags)

        if not result.success:
            logger.error(
                f"Provider verification failed with {len(all_failures)} failures"
            )
        else:
            logger.info("Provider verification passed")

        return result

    def _verify_single_pact(
        self, pact_url: str, base_url: str, state_handlers: Dict[str, Callable]
    ) -> List[Dict[str, Any]]:
        """Verify a single pact contract."""
        # Fetch pact
        headers = {}
        if isinstance(self._auth, str):
            headers["Authorization"] = self._auth

        try:
            response = requests.get(
                pact_url,
                headers=headers,
                auth=self._auth if isinstance(self._auth, HTTPBasicAuth) else None,
                timeout=30,
            )
            response.raise_for_status()
            pact_data = response.json()
        except requests.RequestException as e:
            raise VerificationError(f"Failed to fetch pact: {e}") from e

        contract = PactContract.from_dict(pact_data)
        failures = []

        # Verify each interaction
        for interaction in contract.interactions:
            # Setup state
            if interaction.state:
                if interaction.state not in state_handlers:
                    raise StateSetupError(f"No handler for state: {interaction.state}")
                try:
                    state_handlers[interaction.state]()
                except Exception as e:
                    raise StateSetupError(f"State setup failed: {e}") from e

            # Make request
            try:
                failure = self._verify_interaction(interaction, base_url)
                if failure:
                    failures.append(failure)
            except Exception as e:
                failures.append(
                    {
                        "interaction": interaction.description,
                        "state": interaction.state,
                        "error": str(e),
                    }
                )

        return failures

    def _verify_interaction(
        self, interaction: Interaction, base_url: str
    ) -> Optional[Dict[str, Any]]:
        """Verify a single interaction."""
        req = interaction.request
        expected_resp = interaction.response

        # Build request
        url = base_url.rstrip("/") + req.get("path", "/")
        method = req.get("method", "GET")
        headers = req.get("headers", {})
        body = req.get("body")

        # Make request
        try:
            response = requests.request(
                method, url, headers=headers, json=body, timeout=30
            )
        except requests.RequestException as e:
            return {
                "interaction": interaction.description,
                "state": interaction.state,
                "error": f"Request failed: {e}",
            }

        # Verify status
        expected_status = expected_resp.get("status", 200)
        if response.status_code != expected_status:
            return {
                "interaction": interaction.description,
                "state": interaction.state,
                "type": "status_mismatch",
                "expected": expected_status,
                "actual": response.status_code,
            }

        # Verify headers
        expected_headers = expected_resp.get("headers", {})
        for key, value in expected_headers.items():
            if response.headers.get(key) != value:
                return {
                    "interaction": interaction.description,
                    "state": interaction.state,
                    "type": "header_mismatch",
                    "header": key,
                    "expected": value,
                    "actual": response.headers.get(key),
                }

        # Verify body
        expected_body = expected_resp.get("body")
        if expected_body:
            try:
                actual_body = response.json()
            except ValueError:
                actual_body = response.text

            if not self._match_body(expected_body, actual_body):
                return {
                    "interaction": interaction.description,
                    "state": interaction.state,
                    "type": "body_mismatch",
                    "expected": expected_body,
                    "actual": actual_body,
                }

        return None

    def _match_body(self, expected: Any, actual: Any) -> bool:
        """Match response body with support for matchers."""
        if isinstance(expected, dict) and isinstance(actual, dict):
            for key, value in expected.items():
                if key not in actual:
                    return False
                if not self._match_body(value, actual[key]):
                    return False
            return True
        elif isinstance(expected, list) and isinstance(actual, list):
            if len(expected) != len(actual):
                return False
            for exp, act in zip(expected, actual):
                if not self._match_body(exp, act):
                    return False
            return True
        else:
            return expected == actual

    def _extract_consumer_from_url(self, pact_url: str) -> str:
        """Extract consumer name from pact URL."""
        # URL format: .../consumer/{consumer}/...
        parts = pact_url.split("/")
        try:
            idx = parts.index("consumer")
            return parts[idx + 1]
        except (ValueError, IndexError):
            return "unknown"

    def _publish_verification_results(
        self,
        result: VerificationResult,
        provider_version: str,
        provider_tags: Optional[List[str]],
    ) -> None:
        """Publish verification results to broker."""
        url = (
            f"{self.broker_url}/pacts/provider/{result.provider}"
            f"/consumer/{result.consumer}/pact-version/{result.pact_version}"
            f"/verification-results"
        )

        headers = {"Content-Type": "application/json"}
        if isinstance(self._auth, str):
            headers["Authorization"] = self._auth

        payload = {
            "success": result.success,
            "providerApplicationVersion": provider_version,
            "verifiedAt": result.timestamp,
        }

        if provider_tags:
            payload["tags"] = provider_tags

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                auth=self._auth if isinstance(self._auth, HTTPBasicAuth) else None,
                timeout=30,
            )
            response.raise_for_status()
            logger.info("Published verification results to broker")
        except requests.RequestException as e:
            logger.warning(f"Failed to publish verification results: {e}")

    def can_i_deploy(
        self,
        participant: str,
        version: str,
        to_environment: Optional[str] = None,
        to_tag: Optional[str] = None,
    ) -> CanIDeployResult:
        """
        Check if a participant version can be deployed.

        Args:
            participant: Consumer or provider name
            version: Version to deploy
            to_environment: Target environment name
            to_tag: Target environment tag (deprecated, use to_environment)

        Returns:
            CanIDeployResult object

        Raises:
            BrokerError: If broker URL not configured or check fails
        """
        if not self.broker_url:
            raise BrokerError("Broker URL not configured")

        environment = to_environment or to_tag or "production"

        # Use matrix endpoint
        url = f"{self.broker_url}/matrix"

        headers = {}
        if isinstance(self._auth, str):
            headers["Authorization"] = self._auth

        params: Dict[str, str] = {
            "q[][pacticipant]": participant,
            "q[][version]": version,
            "latestby": "cvp",
            "latest": "true",
            "environment": environment,
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                auth=self._auth if isinstance(self._auth, HTTPBasicAuth) else None,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise BrokerError(f"Failed to check deployment: {e}") from e

        # Parse matrix result
        summary = data.get("summary", {})
        deployable = summary.get("deployable", False)
        reason = summary.get("reason", "Unknown")

        status = (
            DeploymentStatus.DEPLOYABLE
            if deployable
            else DeploymentStatus.NOT_DEPLOYABLE
        )

        result = CanIDeployResult(
            status=status,
            participant=participant,
            version=version,
            environment=environment,
            reason=reason,
            details=data,
        )

        logger.info(
            f"Can-I-Deploy check for {participant}@{version} to "
            f"{environment}: {status.value} - {reason}"
        )

        return result

    def run_consumer_tests(self) -> PactContract:
        """
        Run consumer tests and generate contract.

        Returns:
            Generated PactContract

        Raises:
            ContractError: If consumer tests fail or contract invalid
        """
        if not self.consumer or not self.provider:
            raise ContractError("Consumer and provider must be specified")

        if not self.interactions:
            raise ContractError("No interactions added")

        contract = self.create_consumer_contract()

        # Save to pacts directory
        filename = f"{self.consumer}-{self.provider}.json"
        filepath = self.pacts_dir / filename
        contract.save(filepath)

        return contract

    def clear_interactions(self) -> None:
        """Clear all added interactions."""
        self.interactions = []
        logger.debug("Cleared all interactions")
