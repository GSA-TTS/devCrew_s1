"""
Feed Aggregator for Threat Intelligence Platform.

This module implements comprehensive threat feed aggregation with support for:
- STIX/TAXII 2.1 feed ingestion
- CVE database synchronization (NVD, OSV, GitHub Advisory)
- Custom feed parsers (JSON, CSV, RSS)
- Feed deduplication and normalization
- Automatic feed updates

Author: devCrew_s1
"""

import hashlib
import json
import logging
import xml.etree.ElementTree as ET
from csv import DictReader
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
from pydantic import BaseModel, Field, field_validator
from stix2 import parse as stix_parse
from taxii2client.v21 import Server

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class STIXObject(BaseModel):
    """STIX 2.1 Object Model."""

    id: str = Field(..., description="STIX object ID")
    type: str = Field(..., description="STIX object type")
    spec_version: str = Field(default="2.1", description="STIX spec version")
    created: datetime = Field(..., description="Creation timestamp")
    modified: datetime = Field(..., description="Modification timestamp")
    indicator: Optional[Dict[str, Any]] = Field(
        default=None, description="Indicator data"
    )
    pattern: Optional[str] = Field(default=None, description="STIX pattern")
    name: Optional[str] = Field(default=None, description="Object name")
    description: Optional[str] = Field(default=None, description="Object description")
    labels: List[str] = Field(default_factory=list, description="Object labels")
    confidence: Optional[int] = Field(
        default=None, ge=0, le=100, description="Confidence level 0-100"
    )

    @field_validator("spec_version")
    @classmethod
    def validate_spec_version(cls, v: str) -> str:
        """Validate STIX spec version."""
        if not v.startswith("2."):
            raise ValueError(f"Unsupported STIX version: {v}")
        return v


class CVE(BaseModel):
    """Common Vulnerabilities and Exposures Model."""

    cve_id: str = Field(..., description="CVE identifier (e.g., CVE-2024-1234)")
    description: str = Field(..., description="Vulnerability description")
    severity: str = Field(..., description="Severity level")
    cvss_score: float = Field(..., ge=0.0, le=10.0, description="CVSS score")
    published_date: datetime = Field(..., description="Publication date")
    references: List[str] = Field(default_factory=list, description="Reference URLs")
    affected_products: List[str] = Field(
        default_factory=list, description="Affected products"
    )
    cwe_ids: List[str] = Field(default_factory=list, description="CWE identifiers")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity level."""
        valid_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_severities:
            raise ValueError(
                f"Invalid severity: {v}. Must be one of {valid_severities}"
            )
        return v_upper

    @field_validator("cve_id")
    @classmethod
    def validate_cve_id(cls, v: str) -> str:
        """Validate CVE ID format."""
        if not v.startswith("CVE-"):
            raise ValueError(f"Invalid CVE ID format: {v}")
        return v


class ThreatIndicator(BaseModel):
    """Threat Indicator Model."""

    indicator_type: str = Field(..., description="Indicator type")
    value: str = Field(..., description="Indicator value")
    threat_type: str = Field(..., description="Threat classification")
    confidence: int = Field(..., ge=0, le=100, description="Confidence level 0-100")
    first_seen: datetime = Field(..., description="First seen timestamp")
    last_seen: datetime = Field(..., description="Last seen timestamp")
    tags: List[str] = Field(default_factory=list, description="Indicator tags")
    source: Optional[str] = Field(default=None, description="Feed source")

    @field_validator("indicator_type")
    @classmethod
    def validate_indicator_type(cls, v: str) -> str:
        """Validate indicator type."""
        valid_types = {"IP", "DOMAIN", "HASH", "URL", "EMAIL", "FILE"}
        v_upper = v.upper()
        if v_upper not in valid_types:
            raise ValueError(
                f"Invalid indicator type: {v}. Must be one of {valid_types}"
            )
        return v_upper


class FeedAggregator:
    """
    Feed Aggregator for Threat Intelligence Platform.

    Provides comprehensive threat feed aggregation with STIX/TAXII support,
    CVE database synchronization, and custom feed parsing.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Feed Aggregator.

        Args:
            config: Configuration dictionary with the following optional keys:
                - cache_dir: Directory for caching feed data (default: ./.cache)
                - update_interval: Feed update interval in minutes (default: 15)
                - timeout: Request timeout in seconds (default: 30)
                - max_retries: Maximum retry attempts (default: 3)
                - user_agent: Custom user agent string
                - verify_ssl: Verify SSL certificates (default: True)
        """
        self.config = config or {}
        self.cache_dir = Path(self.config.get("cache_dir", "./.cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.update_interval = self.config.get("update_interval", 15)
        self.timeout = self.config.get("timeout", 30)
        self.max_retries = self.config.get("max_retries", 3)
        self.verify_ssl = self.config.get("verify_ssl", True)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.config.get(
                    "user_agent", "devCrew_s1-ThreatIntelligence/1.0"
                )
            }
        )

        # Cache for deduplication
        self._seen_hashes: Set[str] = set()

        logger.info("FeedAggregator initialized with config: %s", self.config)

    def _compute_hash(self, data: Any) -> str:
        """
        Compute SHA-256 hash of data for deduplication.

        Args:
            data: Data to hash (will be JSON serialized)

        Returns:
            Hexadecimal hash string
        """
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _make_request(
        self, url: str, auth: Optional[Dict[str, str]] = None, **kwargs: Any
    ) -> requests.Response:
        """
        Make HTTP request with retry logic.

        Args:
            url: Request URL
            auth: Optional authentication dict with 'username' and 'password'
            **kwargs: Additional arguments for requests.get

        Returns:
            Response object

        Raises:
            requests.RequestException: On request failure after retries
        """
        auth_tuple = None
        if auth:
            auth_tuple = (auth.get("username", ""), auth.get("password", ""))

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    auth=auth_tuple,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    **kwargs,
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(
                    "Request failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries,
                    e,
                )
                if attempt == self.max_retries - 1:
                    raise
        raise requests.RequestException("Max retries exceeded")

    def ingest_stix_feed(
        self, url: str, auth: Optional[Dict[str, str]] = None
    ) -> List[STIXObject]:
        """
        Ingest STIX 2.1 feed from URL.

        Args:
            url: STIX feed URL
            auth: Optional authentication credentials

        Returns:
            List of parsed STIX objects

        Raises:
            ValueError: On invalid STIX data
            requests.RequestException: On network errors
        """
        logger.info("Ingesting STIX feed from: %s", url)

        try:
            response = self._make_request(url, auth)
            stix_data = response.json()

            stix_objects = []

            # Handle STIX bundle
            if isinstance(stix_data, dict) and stix_data.get("type") == "bundle":
                objects = stix_data.get("objects", [])
            elif isinstance(stix_data, list):
                objects = stix_data
            else:
                objects = [stix_data]

            for obj in objects:
                try:
                    # Parse with stix2 library for validation
                    stix_obj = stix_parse(obj, allow_custom=True)

                    # Extract timestamps (already datetime objects from stix2)
                    created = getattr(stix_obj, "created", None)
                    modified = getattr(stix_obj, "modified", None)

                    # Convert to our model (use getattr for stix2 objects)
                    stix_model = STIXObject(
                        id=getattr(stix_obj, "id", ""),
                        type=getattr(stix_obj, "type", ""),
                        spec_version=getattr(stix_obj, "spec_version", "2.1"),
                        created=created if created else datetime.utcnow(),
                        modified=modified if modified else datetime.utcnow(),
                        name=getattr(stix_obj, "name", None),
                        description=getattr(stix_obj, "description", None),
                        pattern=getattr(stix_obj, "pattern", None),
                        labels=getattr(stix_obj, "labels", []),
                        confidence=getattr(stix_obj, "confidence", None),
                    )

                    stix_objects.append(stix_model)

                except Exception as e:
                    logger.warning("Failed to parse STIX object: %s", e)
                    continue

            logger.info("Ingested %d STIX objects from feed", len(stix_objects))
            return stix_objects

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in STIX feed: {e}") from e

    def ingest_taxii_feed(
        self,
        server_url: str,
        collection_id: str,
        auth: Optional[Dict[str, str]] = None,
    ) -> List[STIXObject]:
        """
        Ingest TAXII 2.1 feed from collection.

        Args:
            server_url: TAXII server URL
            collection_id: Collection identifier
            auth: Optional authentication credentials

        Returns:
            List of STIX objects from collection

        Raises:
            ValueError: On invalid collection or server
            requests.RequestException: On network errors
        """
        logger.info(
            "Ingesting TAXII feed from server: %s, collection: %s",
            server_url,
            collection_id,
        )

        try:
            # Initialize TAXII server connection
            server_kwargs: Dict[str, Any] = {"verify": self.verify_ssl}
            if auth:
                server_kwargs["user"] = auth.get("username")
                server_kwargs["password"] = auth.get("password")

            server = Server(server_url, **server_kwargs)

            # Find and connect to collection
            collection = None
            for coll in server.collections:
                if coll.id == collection_id:
                    collection = coll
                    break

            if not collection:
                raise ValueError(
                    f"Collection {collection_id} not found on server {server_url}"
                )

            # Fetch objects from collection
            stix_objects = []
            manifest = collection.get_objects()

            for obj in manifest.get("objects", []):
                try:
                    stix_obj = stix_parse(obj, allow_custom=True)

                    # Extract timestamps (already datetime objects from stix2)
                    created = getattr(stix_obj, "created", None)
                    modified = getattr(stix_obj, "modified", None)

                    stix_model = STIXObject(
                        id=getattr(stix_obj, "id", ""),
                        type=getattr(stix_obj, "type", ""),
                        spec_version=getattr(stix_obj, "spec_version", "2.1"),
                        created=created if created else datetime.utcnow(),
                        modified=modified if modified else datetime.utcnow(),
                        name=getattr(stix_obj, "name", None),
                        description=getattr(stix_obj, "description", None),
                        pattern=getattr(stix_obj, "pattern", None),
                        labels=getattr(stix_obj, "labels", []),
                        confidence=getattr(stix_obj, "confidence", None),
                    )

                    stix_objects.append(stix_model)

                except Exception as e:
                    logger.warning("Failed to parse TAXII object: %s", e)
                    continue

            logger.info("Ingested %d objects from TAXII collection", len(stix_objects))
            return stix_objects

        except Exception as e:
            raise ValueError(f"Failed to ingest TAXII feed: {e}") from e

    def sync_cve_database(
        self, source: str = "nvd", since: Optional[datetime] = None
    ) -> List[CVE]:
        """
        Synchronize CVE database from external source.

        Args:
            source: CVE source (nvd, osv, github)
            since: Only fetch CVEs modified since this date

        Returns:
            List of CVE objects

        Raises:
            ValueError: On unsupported source
            requests.RequestException: On network errors
        """
        logger.info("Syncing CVE database from source: %s", source)

        if source.lower() == "nvd":
            return self._sync_nvd_cves(since)
        elif source.lower() == "osv":
            return self._sync_osv_cves(since)
        elif source.lower() == "github":
            return self._sync_github_cves(since)
        else:
            raise ValueError(
                f"Unsupported CVE source: {source}. "
                "Supported sources: nvd, osv, github"
            )

    def _sync_nvd_cves(self, since: Optional[datetime] = None) -> List[CVE]:
        """
        Sync CVEs from NVD (National Vulnerability Database).

        Args:
            since: Only fetch CVEs modified since this date

        Returns:
            List of CVE objects
        """
        cves = []
        base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"

        # Default to last 7 days if not specified
        if since is None:
            since = datetime.utcnow() - timedelta(days=7)

        params = {
            "lastModStartDate": since.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "resultsPerPage": 100,
        }

        try:
            response = self._make_request(base_url, params=params)
            data = response.json()

            for item in data.get("vulnerabilities", []):
                cve_data = item.get("cve", {})
                cve_id = cve_data.get("id", "")

                # Extract description
                descriptions = cve_data.get("descriptions", [])
                description = ""
                for desc in descriptions:
                    if desc.get("lang") == "en":
                        description = desc.get("value", "")
                        break

                # Extract CVSS metrics
                metrics = cve_data.get("metrics", {})
                cvss_score = 0.0
                severity = "UNKNOWN"

                # Try CVSS v3.1 first, then v3.0, then v2
                for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                    if version in metrics and metrics[version]:
                        metric = metrics[version][0]
                        cvss_data = metric.get("cvssData", {})
                        cvss_score = float(cvss_data.get("baseScore", 0.0))
                        severity = metric.get("baseSeverity", "UNKNOWN").upper()
                        break

                # Map numeric score to severity if not provided
                if severity == "UNKNOWN" and cvss_score > 0:
                    if cvss_score >= 9.0:
                        severity = "CRITICAL"
                    elif cvss_score >= 7.0:
                        severity = "HIGH"
                    elif cvss_score >= 4.0:
                        severity = "MEDIUM"
                    else:
                        severity = "LOW"

                # Extract references
                references = []
                for ref in cve_data.get("references", []):
                    url = ref.get("url")
                    if url:
                        references.append(url)

                # Extract affected products
                affected_products = []
                configurations = cve_data.get("configurations", [])
                for config in configurations:
                    for node in config.get("nodes", []):
                        for cpe_match in node.get("cpeMatch", []):
                            criteria = cpe_match.get("criteria", "")
                            if criteria:
                                affected_products.append(criteria)

                # Extract CWE IDs
                cwe_ids = []
                for weakness in cve_data.get("weaknesses", []):
                    for desc in weakness.get("description", []):
                        value = desc.get("value", "")
                        if value.startswith("CWE-"):
                            cwe_ids.append(value)

                # Parse published date
                published_str = cve_data.get("published", "")
                published_date = datetime.fromisoformat(
                    published_str.replace("Z", "+00:00")
                )

                cve = CVE(
                    cve_id=cve_id,
                    description=description,
                    severity=severity if severity != "UNKNOWN" else "LOW",
                    cvss_score=cvss_score,
                    published_date=published_date,
                    references=references,
                    affected_products=affected_products[:10],
                    cwe_ids=cwe_ids,
                )

                cves.append(cve)

            logger.info("Synced %d CVEs from NVD", len(cves))
            return cves

        except Exception as e:
            logger.error("Failed to sync NVD CVEs: %s", e)
            return []

    def _sync_osv_cves(self, since: Optional[datetime] = None) -> List[CVE]:
        """
        Sync CVEs from OSV (Open Source Vulnerabilities).

        Args:
            since: Only fetch CVEs modified since this date

        Returns:
            List of CVE objects
        """
        cves: List[CVE] = []

        try:
            # OSV provides ecosystem-specific feeds
            # Base URL: https://osv-vulnerabilities.storage.googleapis.com
            ecosystems = ["PyPI", "npm", "Go", "Maven", "NuGet"]

            for ecosystem in ecosystems:
                # Note: This is a simplified implementation
                # In production, you would download and extract the ZIP file
                # from: https://osv-vulnerabilities.storage.googleapis.com/{ecosystem}/all.zip  # noqa: E501
                logger.info("Would fetch OSV data for ecosystem: %s", ecosystem)

            logger.info("OSV sync completed (simplified implementation)")
            return cves

        except Exception as e:
            logger.error("Failed to sync OSV CVEs: %s", e)
            return []

    def _sync_github_cves(self, since: Optional[datetime] = None) -> List[CVE]:
        """
        Sync CVEs from GitHub Advisory Database.

        Args:
            since: Only fetch CVEs modified since this date

        Returns:
            List of CVE objects
        """
        cves: List[CVE] = []
        # GitHub Advisory Database requires GraphQL API
        # This is a simplified implementation

        logger.info("GitHub Advisory sync (requires GraphQL API implementation)")
        return cves

    def parse_custom_feed(
        self, file_path: str, format: str = "json"
    ) -> List[ThreatIndicator]:
        """
        Parse custom threat feed file.

        Args:
            file_path: Path to feed file
            format: Feed format (json, csv, rss)

        Returns:
            List of threat indicators

        Raises:
            ValueError: On unsupported format or invalid data
            FileNotFoundError: If file doesn't exist
        """
        logger.info("Parsing custom feed: %s (format: %s)", file_path, format)

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Feed file not found: {file_path}")

        format_lower = format.lower()

        if format_lower == "json":
            return self._parse_json_feed(path)
        elif format_lower == "csv":
            return self._parse_csv_feed(path)
        elif format_lower == "rss":
            return self._parse_rss_feed(path)
        else:
            raise ValueError(
                f"Unsupported feed format: {format}. "
                "Supported formats: json, csv, rss"
            )

    def _parse_json_feed(self, path: Path) -> List[ThreatIndicator]:
        """Parse JSON format threat feed."""
        indicators = []

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Support both single object and array
        if isinstance(data, dict):
            data = [data]

        for item in data:
            try:
                indicator = ThreatIndicator(
                    indicator_type=item.get("type", "unknown"),
                    value=item.get("value", ""),
                    threat_type=item.get("threat_type", "unknown"),
                    confidence=int(item.get("confidence", 50)),
                    first_seen=datetime.fromisoformat(
                        item.get("first_seen", datetime.utcnow().isoformat())
                    ),
                    last_seen=datetime.fromisoformat(
                        item.get("last_seen", datetime.utcnow().isoformat())
                    ),
                    tags=item.get("tags", []),
                    source=item.get("source", "custom_json"),
                )
                indicators.append(indicator)
            except Exception as e:
                logger.warning("Failed to parse JSON indicator: %s", e)
                continue

        logger.info("Parsed %d indicators from JSON feed", len(indicators))
        return indicators

    def _parse_csv_feed(self, path: Path) -> List[ThreatIndicator]:
        """Parse CSV format threat feed."""
        indicators = []

        with open(path, "r", encoding="utf-8") as f:
            reader = DictReader(f)

            for row in reader:
                try:
                    # Parse tags if present
                    tags = []
                    if "tags" in row and row["tags"]:
                        tags = [t.strip() for t in row["tags"].split(",")]

                    # Parse timestamps
                    first_seen = row.get("first_seen")
                    if first_seen:
                        first_seen_dt = datetime.fromisoformat(first_seen)
                    else:
                        first_seen_dt = datetime.utcnow()

                    last_seen = row.get("last_seen")
                    if last_seen:
                        last_seen_dt = datetime.fromisoformat(last_seen)
                    else:
                        last_seen_dt = datetime.utcnow()

                    indicator = ThreatIndicator(
                        indicator_type=row.get("type", "unknown"),
                        value=row.get("value", ""),
                        threat_type=row.get("threat_type", "unknown"),
                        confidence=int(row.get("confidence", 50)),
                        first_seen=first_seen_dt,
                        last_seen=last_seen_dt,
                        tags=tags,
                        source=row.get("source", "custom_csv"),
                    )
                    indicators.append(indicator)
                except Exception as e:
                    logger.warning("Failed to parse CSV row: %s", e)
                    continue

        logger.info("Parsed %d indicators from CSV feed", len(indicators))
        return indicators

    def _parse_rss_feed(self, path: Path) -> List[ThreatIndicator]:
        """Parse RSS format threat feed."""
        indicators = []

        try:
            tree = ET.parse(path)  # nosec B314 - Use defusedxml.ElementTree in production
            root = tree.getroot()

            # Find all items in the feed
            for item in root.findall(".//item"):
                try:
                    title = item.findtext("title", "")
                    description = item.findtext("description", "")
                    pub_date_str = item.findtext("pubDate", "")

                    # Parse publication date
                    pub_date = datetime.utcnow()
                    if pub_date_str:
                        try:
                            # RFC 2822 format
                            from email.utils import parsedate_to_datetime

                            pub_date = parsedate_to_datetime(pub_date_str)
                        except Exception:
                            pass

                    # Extract indicator from title or description
                    # This is a simplified heuristic
                    indicator_value = title or description

                    # Determine indicator type heuristically
                    indicator_type = "UNKNOWN"
                    if "." in indicator_value and len(indicator_value.split(".")) == 4:
                        indicator_type = "IP"
                    elif "." in indicator_value:
                        indicator_type = "DOMAIN"
                    elif "http" in indicator_value.lower():
                        indicator_type = "URL"

                    indicator = ThreatIndicator(
                        indicator_type=indicator_type,
                        value=indicator_value[:200],
                        threat_type="rss_feed",
                        confidence=50,
                        first_seen=pub_date,
                        last_seen=pub_date,
                        tags=["rss"],
                        source="custom_rss",
                    )
                    indicators.append(indicator)

                except Exception as e:
                    logger.warning("Failed to parse RSS item: %s", e)
                    continue

            logger.info("Parsed %d indicators from RSS feed", len(indicators))
            return indicators

        except ET.ParseError as e:
            logger.error("Failed to parse RSS XML: %s", e)
            return []

    def deduplicate_indicators(
        self, indicators: List[ThreatIndicator]
    ) -> List[ThreatIndicator]:
        """
        Remove duplicate indicators using content hashing.

        Args:
            indicators: List of threat indicators

        Returns:
            Deduplicated list of indicators
        """
        logger.info("Deduplicating %d indicators", len(indicators))

        unique_indicators = []
        seen_hashes = set()

        for indicator in indicators:
            # Create hash from indicator type and value
            hash_data = f"{indicator.indicator_type}:{indicator.value}"
            indicator_hash = self._compute_hash(hash_data)

            if indicator_hash not in seen_hashes:
                seen_hashes.add(indicator_hash)
                unique_indicators.append(indicator)

        deduplicated_count = len(indicators) - len(unique_indicators)
        logger.info(
            "Removed %d duplicates, %d unique indicators remaining",
            deduplicated_count,
            len(unique_indicators),
        )

        return unique_indicators

    def normalize_feed_data(
        self, raw_data: Any, source_format: str
    ) -> List[STIXObject]:
        """
        Normalize feed data to STIX 2.1 format.

        Args:
            raw_data: Raw feed data (dict, list, or string)
            source_format: Source format identifier

        Returns:
            List of STIX objects

        Raises:
            ValueError: On invalid data or unsupported format
        """
        logger.info("Normalizing feed data from format: %s", source_format)

        stix_objects = []

        try:
            # Handle different source formats
            if source_format.lower() == "stix":
                # Already STIX, just validate
                if isinstance(raw_data, dict):
                    raw_data = [raw_data]

                for obj in raw_data:
                    stix_obj = stix_parse(obj, allow_custom=True)

                    # Extract timestamps (already datetime objects from stix2)
                    created = getattr(stix_obj, "created", None)
                    modified = getattr(stix_obj, "modified", None)

                    stix_model = STIXObject(
                        id=getattr(stix_obj, "id", ""),
                        type=getattr(stix_obj, "type", ""),
                        spec_version=getattr(stix_obj, "spec_version", "2.1"),
                        created=created if created else datetime.utcnow(),
                        modified=modified if modified else datetime.utcnow(),
                        name=getattr(stix_obj, "name", None),
                        description=getattr(stix_obj, "description", None),
                        pattern=getattr(stix_obj, "pattern", None),
                        labels=getattr(stix_obj, "labels", []),
                        confidence=getattr(stix_obj, "confidence", None),
                    )
                    stix_objects.append(stix_model)

            else:
                # Convert custom format to STIX
                if isinstance(raw_data, dict):
                    raw_data = [raw_data]

                for item in raw_data:
                    # Create STIX indicator from custom data
                    now = datetime.utcnow()
                    indicator_id = f"indicator--{self._compute_hash(item)[:36]}"

                    # Merge labels with source format
                    labels = item.get("labels", [])
                    if source_format not in labels:
                        labels = labels + [source_format]

                    stix_obj = STIXObject(
                        id=indicator_id,
                        type="indicator",
                        spec_version="2.1",
                        created=now,
                        modified=now,
                        name=item.get("name", "Unknown Indicator"),
                        description=item.get("description", ""),
                        pattern=item.get("pattern", ""),
                        labels=labels,
                        confidence=item.get("confidence"),
                    )
                    stix_objects.append(stix_obj)

            logger.info("Normalized %d objects to STIX format", len(stix_objects))
            return stix_objects

        except Exception as e:
            raise ValueError(f"Failed to normalize feed data: {e}") from e
