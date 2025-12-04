"""IOC Manager for Threat Intelligence Platform.

This module provides comprehensive Indicator of Compromise (IOC) management
including extraction, enrichment, filtering, lifecycle tracking, and export.
"""

import hashlib
import ipaddress
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import dns.resolver
import requests
from pydantic import BaseModel, Field, validator


class IOC(BaseModel):
    """Indicator of Compromise model."""

    ioc_type: str  # ip, domain, hash, url, email
    value: str
    confidence: int = Field(ge=0, le=100)  # 0-100
    first_seen: datetime
    last_seen: datetime
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    @validator("ioc_type")
    def validate_ioc_type(cls, v: str) -> str:
        """Validate IOC type."""
        valid_types = ["ip", "domain", "hash", "url", "email", "file"]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid IOC type: {v}. Must be one of {valid_types}")
        return v.lower()

    @validator("confidence")
    def validate_confidence(cls, v: int) -> int:
        """Validate confidence score."""
        if not 0 <= v <= 100:
            raise ValueError("Confidence must be between 0 and 100")
        return v


class GeoLocation(BaseModel):
    """Geolocation information."""

    country: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    asn: Optional[str] = None
    isp: Optional[str] = None


class EnrichedIOC(BaseModel):
    """Enriched IOC with additional intelligence."""

    ioc: IOC
    reputation_score: int = Field(ge=0, le=100)  # 0-100, lower is worse
    malicious_votes: int = 0
    benign_votes: int = 0
    geolocation: Optional[GeoLocation] = None
    asn: Optional[str] = None
    related_threats: List[str] = Field(default_factory=list)
    enrichment_sources: List[str] = Field(default_factory=list)
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IOCLifecycle(BaseModel):
    """IOC lifecycle tracking."""

    ioc: IOC
    status: str  # new, active, expired, false_positive
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    times_seen: int = 0
    last_activity: Optional[datetime] = None
    notes: List[str] = Field(default_factory=list)


class IOCManager:
    """Manages IOC extraction, enrichment, filtering, and lifecycle."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize IOC manager.

        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config or {}
        self.api_keys = self.config.get("api_keys", {})
        self.cache: Dict[str, EnrichedIOC] = {}
        self.whitelist: Set[str] = set(self.config.get("whitelist", []))
        self.rate_limits: Dict[str, Dict[str, Any]] = {
            "virustotal": {"calls": 0, "reset_time": datetime.utcnow()},
            "abuseipdb": {"calls": 0, "reset_time": datetime.utcnow()},
        }
        self.max_calls_per_minute = self.config.get("max_calls_per_minute", 4)

        # IOC extraction patterns
        self.patterns = {
            "ipv4": re.compile(
                r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
                r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
            ),
            "domain": re.compile(
                r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]"
                r"{2,}\b"
            ),
            "md5": re.compile(r"\b[a-fA-F0-9]{32}\b"),
            "sha1": re.compile(r"\b[a-fA-F0-9]{40}\b"),
            "sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "url": re.compile(
                r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\."
                r"[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"
            ),
        }

    def extract_iocs(self, threat_data: List[Dict[str, Any]]) -> List[IOC]:
        """Extract IOCs from threat data.

        Args:
            threat_data: List of STIX objects or threat intelligence data

        Returns:
            List of extracted IOCs
        """
        iocs = []

        for item in threat_data:
            # Handle STIX objects
            if isinstance(item, dict) and item.get("type") == "indicator":
                pattern = item.get("pattern", "")
                ioc = self._extract_from_stix_pattern(pattern, item)
                if ioc:
                    iocs.append(ioc)

            # Extract from raw text
            text = self._extract_text(item)
            if text:
                extracted = self._extract_from_text(text, source=item.get("source"))
                iocs.extend(extracted)

        # Deduplicate IOCs
        unique_iocs = self._deduplicate_iocs(iocs)
        return unique_iocs

    def _extract_from_stix_pattern(
        self, pattern: str, item: Dict[str, Any]
    ) -> Optional[IOC]:
        """Extract IOC from STIX pattern."""
        try:
            # Parse STIX 2.1 pattern like: [ipv4-addr:value = '192.168.1.1']
            if "ipv4-addr:value" in pattern:
                value = re.search(r"'([^']+)'", pattern)
                if value:
                    return IOC(
                        ioc_type="ip",
                        value=value.group(1),
                        confidence=80,
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        tags=item.get("labels", []),
                        source=item.get("created_by_ref"),
                    )
            elif "domain-name:value" in pattern:
                value = re.search(r"'([^']+)'", pattern)
                if value:
                    return IOC(
                        ioc_type="domain",
                        value=value.group(1),
                        confidence=80,
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        tags=item.get("labels", []),
                        source=item.get("created_by_ref"),
                    )
            elif "file:hashes" in pattern:
                hash_match = re.search(r"'([a-fA-F0-9]+)'", pattern)
                if hash_match:
                    hash_value = hash_match.group(1)
                    hash_type = self._detect_hash_type(hash_value)
                    return IOC(
                        ioc_type="hash",
                        value=hash_value,
                        confidence=90,
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        tags=item.get("labels", []),
                        source=item.get("created_by_ref"),
                        context={"hash_type": hash_type},
                    )
        except Exception:
            pass
        return None

    def _extract_text(self, item: Any) -> str:
        """Extract text from various data structures."""
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            # Extract text from common fields
            text_parts = []
            for key in ["description", "content", "text", "pattern", "name"]:
                if key in item:
                    text_parts.append(str(item[key]))
            return " ".join(text_parts)
        return ""

    def _extract_from_text(self, text: str, source: Optional[str] = None) -> List[IOC]:
        """Extract IOCs from raw text."""
        iocs = []
        now = datetime.utcnow()

        # Extract IPs
        for match in self.patterns["ipv4"].finditer(text):
            ip = match.group(0)
            if self._is_valid_ip(ip):
                iocs.append(
                    IOC(
                        ioc_type="ip",
                        value=ip,
                        confidence=70,
                        first_seen=now,
                        last_seen=now,
                        tags=["extracted"],
                        source=source,
                    )
                )

        # Extract domains
        for match in self.patterns["domain"].finditer(text):
            domain = match.group(0)
            if self._is_valid_domain(domain):
                iocs.append(
                    IOC(
                        ioc_type="domain",
                        value=domain.lower(),
                        confidence=70,
                        first_seen=now,
                        last_seen=now,
                        tags=["extracted"],
                        source=source,
                    )
                )

        # Extract hashes
        for hash_type in ["md5", "sha1", "sha256"]:
            for match in self.patterns[hash_type].finditer(text):
                hash_value = match.group(0)
                iocs.append(
                    IOC(
                        ioc_type="hash",
                        value=hash_value.lower(),
                        confidence=85,
                        first_seen=now,
                        last_seen=now,
                        tags=["extracted"],
                        source=source,
                        context={"hash_type": hash_type},
                    )
                )

        # Extract emails
        for match in self.patterns["email"].finditer(text):
            email = match.group(0)
            iocs.append(
                IOC(
                    ioc_type="email",
                    value=email.lower(),
                    confidence=70,
                    first_seen=now,
                    last_seen=now,
                    tags=["extracted"],
                    source=source,
                )
            )

        # Extract URLs
        for match in self.patterns["url"].finditer(text):
            url = match.group(0)
            iocs.append(
                IOC(
                    ioc_type="url",
                    value=url,
                    confidence=75,
                    first_seen=now,
                    last_seen=now,
                    tags=["extracted"],
                    source=source,
                )
            )

        return iocs

    def _is_valid_ip(self, ip: str) -> bool:
        """Check if IP is valid and not private/reserved."""
        try:
            ip_obj = ipaddress.ip_address(ip)
            # Exclude private, loopback, link-local
            return not (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_multicast
            )
        except ValueError:
            return False

    def _is_valid_domain(self, domain: str) -> bool:
        """Check if domain is valid."""
        # Exclude common false positives
        excluded = [
            "example.com",
            "localhost",
            "test.com",
            "domain.com",
            "email.com",
        ]
        if domain.lower() in excluded:
            return False
        # Must have TLD
        if "." not in domain:
            return False
        return True

    def _detect_hash_type(self, hash_value: str) -> str:
        """Detect hash type by length."""
        length = len(hash_value)
        if length == 32:
            return "md5"
        elif length == 40:
            return "sha1"
        elif length == 64:
            return "sha256"
        return "unknown"

    def _deduplicate_iocs(self, iocs: List[IOC]) -> List[IOC]:
        """Remove duplicate IOCs."""
        seen = {}
        unique = []

        for ioc in iocs:
            key = f"{ioc.ioc_type}:{ioc.value}"
            if key not in seen:
                seen[key] = ioc
                unique.append(ioc)
            else:
                # Update last_seen and merge tags
                existing = seen[key]
                existing.last_seen = max(existing.last_seen, ioc.last_seen)
                existing.tags = list(set(existing.tags + ioc.tags))
                existing.confidence = max(existing.confidence, ioc.confidence)

        return unique

    def enrich_ioc(
        self, ioc: IOC, services: List[str] = ["virustotal", "abuseipdb"]
    ) -> EnrichedIOC:
        """Enrich IOC with external data.

        Args:
            ioc: IOC to enrich
            services: List of enrichment services to use

        Returns:
            EnrichedIOC with additional intelligence
        """
        # Check cache first
        cache_key = f"{ioc.ioc_type}:{ioc.value}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            # Return cached if less than 24 hours old
            if (datetime.utcnow() - cached.enriched_at) < timedelta(hours=24):
                return cached

        enriched = EnrichedIOC(
            ioc=ioc,
            reputation_score=50,  # Default neutral score
        )

        # Enrich based on IOC type
        if ioc.ioc_type == "ip":
            enriched = self._enrich_ip(ioc, services, enriched)
        elif ioc.ioc_type == "domain":
            enriched = self._enrich_domain(ioc, services, enriched)
        elif ioc.ioc_type == "hash":
            enriched = self._enrich_hash(ioc, services, enriched)
        elif ioc.ioc_type == "url":
            enriched = self._enrich_url(ioc, services, enriched)

        # Cache the result
        self.cache[cache_key] = enriched

        return enriched

    def _check_rate_limit(self, service: str) -> bool:
        """Check if rate limit allows another call."""
        now = datetime.utcnow()
        service_limits = self.rate_limits.get(service, {})

        # Reset counter if a minute has passed
        if (now - service_limits.get("reset_time", now)).total_seconds() >= 60:
            self.rate_limits[service] = {"calls": 0, "reset_time": now}
            return True

        # Check if under limit
        if service_limits.get("calls", 0) < self.max_calls_per_minute:
            return True

        return False

    def _increment_rate_limit(self, service: str) -> None:
        """Increment rate limit counter."""
        if service not in self.rate_limits:
            self.rate_limits[service] = {
                "calls": 0,
                "reset_time": datetime.utcnow(),
            }
        self.rate_limits[service]["calls"] += 1

    def _enrich_ip(
        self, ioc: IOC, services: List[str], enriched: EnrichedIOC
    ) -> EnrichedIOC:
        """Enrich IP address."""
        # AbuseIPDB enrichment
        if "abuseipdb" in services and self._check_rate_limit("abuseipdb"):
            api_key = self.api_keys.get("abuseipdb")
            if api_key:
                try:
                    headers = {"Key": api_key, "Accept": "application/json"}
                    params: Dict[str, Any] = {
                        "ipAddress": ioc.value,
                        "maxAgeInDays": 90,
                    }
                    response = requests.get(
                        "https://api.abuseipdb.com/api/v2/check",
                        headers=headers,
                        params=params,
                        timeout=10,
                    )
                    if response.status_code == 200:
                        data = response.json().get("data", {})
                        abuse_score = data.get("abuseConfidenceScore", 0)
                        enriched.reputation_score = 100 - abuse_score
                        enriched.metadata["abuse_reports"] = data.get("totalReports", 0)
                        enriched.metadata["is_whitelisted"] = data.get(
                            "isWhitelisted", False
                        )
                        enriched.enrichment_sources.append("abuseipdb")
                        self._increment_rate_limit("abuseipdb")
                except Exception:
                    pass

        # VirusTotal enrichment
        if "virustotal" in services and self._check_rate_limit("virustotal"):
            api_key = self.api_keys.get("virustotal")
            if api_key:
                try:
                    headers = {"x-apikey": api_key}
                    response = requests.get(
                        f"https://www.virustotal.com/api/v3/ip_addresses/{ioc.value}",
                        headers=headers,
                        timeout=10,
                    )
                    if response.status_code == 200:
                        data = response.json().get("data", {}).get("attributes", {})
                        stats = data.get("last_analysis_stats", {})
                        enriched.malicious_votes = stats.get("malicious", 0)
                        enriched.benign_votes = stats.get("harmless", 0)

                        # Calculate reputation
                        total = sum(stats.values())
                        if total > 0:
                            score = (stats.get("harmless", 0) / total) * 100
                            enriched.reputation_score = int(score)

                        enriched.enrichment_sources.append("virustotal")
                        self._increment_rate_limit("virustotal")
                except Exception:
                    pass

        # DNS enrichment
        try:
            enriched.metadata["ptr_record"] = self._get_ptr_record(ioc.value)
        except Exception:
            pass

        return enriched

    def _enrich_domain(
        self, ioc: IOC, services: List[str], enriched: EnrichedIOC
    ) -> EnrichedIOC:
        """Enrich domain name."""
        # VirusTotal enrichment
        if "virustotal" in services and self._check_rate_limit("virustotal"):
            api_key = self.api_keys.get("virustotal")
            if api_key:
                try:
                    headers = {"x-apikey": api_key}
                    response = requests.get(
                        f"https://www.virustotal.com/api/v3/domains/{ioc.value}",
                        headers=headers,
                        timeout=10,
                    )
                    if response.status_code == 200:
                        data = response.json().get("data", {}).get("attributes", {})
                        stats = data.get("last_analysis_stats", {})
                        enriched.malicious_votes = stats.get("malicious", 0)
                        enriched.benign_votes = stats.get("harmless", 0)

                        # Calculate reputation
                        total = sum(stats.values())
                        if total > 0:
                            score = (stats.get("harmless", 0) / total) * 100
                            enriched.reputation_score = int(score)

                        enriched.enrichment_sources.append("virustotal")
                        self._increment_rate_limit("virustotal")
                except Exception:
                    pass

        # DNS resolution
        try:
            ip_addresses = self._resolve_domain(ioc.value)
            enriched.metadata["resolved_ips"] = ip_addresses
        except Exception:
            pass

        return enriched

    def _enrich_hash(
        self, ioc: IOC, services: List[str], enriched: EnrichedIOC
    ) -> EnrichedIOC:
        """Enrich file hash."""
        # VirusTotal enrichment
        if "virustotal" in services and self._check_rate_limit("virustotal"):
            api_key = self.api_keys.get("virustotal")
            if api_key:
                try:
                    headers = {"x-apikey": api_key}
                    response = requests.get(
                        f"https://www.virustotal.com/api/v3/files/{ioc.value}",
                        headers=headers,
                        timeout=10,
                    )
                    if response.status_code == 200:
                        data = response.json().get("data", {}).get("attributes", {})
                        stats = data.get("last_analysis_stats", {})
                        enriched.malicious_votes = stats.get("malicious", 0)
                        enriched.benign_votes = stats.get("harmless", 0)

                        # Calculate reputation
                        total = sum(stats.values())
                        if total > 0:
                            score = (stats.get("undetected", 0) / total) * 100
                            enriched.reputation_score = int(score)

                        # Add file metadata
                        enriched.metadata["file_type"] = data.get("type_description")
                        enriched.metadata["file_size"] = data.get("size")
                        enriched.metadata["file_names"] = data.get("names", [])

                        enriched.enrichment_sources.append("virustotal")
                        self._increment_rate_limit("virustotal")
                except Exception:
                    pass

        return enriched

    def _enrich_url(
        self, ioc: IOC, services: List[str], enriched: EnrichedIOC
    ) -> EnrichedIOC:
        """Enrich URL."""
        # Parse URL
        try:
            parsed = urlparse(ioc.value)
            enriched.metadata["domain"] = parsed.netloc
            enriched.metadata["path"] = parsed.path
            enriched.metadata["scheme"] = parsed.scheme
        except Exception:
            pass

        # VirusTotal enrichment
        if "virustotal" in services and self._check_rate_limit("virustotal"):
            api_key = self.api_keys.get("virustotal")
            if api_key:
                try:
                    headers = {"x-apikey": api_key}
                    # URL needs to be base64 encoded without padding
                    import base64

                    url_id = (
                        base64.urlsafe_b64encode(ioc.value.encode()).decode().strip("=")
                    )
                    response = requests.get(
                        f"https://www.virustotal.com/api/v3/urls/{url_id}",
                        headers=headers,
                        timeout=10,
                    )
                    if response.status_code == 200:
                        data = response.json().get("data", {}).get("attributes", {})
                        stats = data.get("last_analysis_stats", {})
                        enriched.malicious_votes = stats.get("malicious", 0)
                        enriched.benign_votes = stats.get("harmless", 0)

                        # Calculate reputation
                        total = sum(stats.values())
                        if total > 0:
                            score = (stats.get("harmless", 0) / total) * 100
                            enriched.reputation_score = int(score)

                        enriched.enrichment_sources.append("virustotal")
                        self._increment_rate_limit("virustotal")
                except Exception:
                    pass

        return enriched

    def _get_ptr_record(self, ip: str) -> Optional[str]:
        """Get PTR (reverse DNS) record for IP."""
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 2
            resolver.lifetime = 2
            addr = dns.reversename.from_address(ip)
            answers = resolver.resolve(addr, "PTR")
            if answers:
                return str(answers[0])
        except Exception:
            pass
        return None

    def _resolve_domain(self, domain: str) -> List[str]:
        """Resolve domain to IP addresses."""
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 2
            resolver.lifetime = 2
            answers = resolver.resolve(domain, "A")
            return [str(rdata) for rdata in answers]
        except Exception:
            return []

    def filter_false_positives(
        self, iocs: List[IOC], whitelist: Optional[List[str]] = None
    ) -> List[IOC]:
        """Filter known false positives.

        Args:
            iocs: List of IOCs to filter
            whitelist: Additional whitelist entries

        Returns:
            Filtered list of IOCs
        """
        if whitelist:
            self.whitelist.update(whitelist)

        filtered = []
        for ioc in iocs:
            # Check whitelist
            if ioc.value in self.whitelist:
                continue

            # Check common false positives
            if self._is_false_positive(ioc):
                continue

            filtered.append(ioc)

        return filtered

    def _is_false_positive(self, ioc: IOC) -> bool:
        """Check if IOC is likely a false positive."""
        # Common false positive domains
        fp_domains = [
            "google.com",
            "microsoft.com",
            "apple.com",
            "amazon.com",
            "facebook.com",
            "twitter.com",
            "github.com",
            "stackoverflow.com",
        ]

        if ioc.ioc_type == "domain" and any(
            fp in ioc.value.lower() for fp in fp_domains
        ):
            return True

        # RFC 1918 private IPs should have been filtered earlier
        if ioc.ioc_type == "ip":
            try:
                ip_obj = ipaddress.ip_address(ioc.value)
                if ip_obj.is_private:
                    return True
            except ValueError:
                pass

        # Low confidence IOCs
        if ioc.confidence < 30:
            return True

        return False

    def manage_lifecycle(self, ioc: IOC) -> IOCLifecycle:
        """Track IOC lifecycle.

        Args:
            ioc: IOC to track

        Returns:
            IOCLifecycle object
        """
        now = datetime.utcnow()

        # Determine status based on age and activity
        age_days = (now - ioc.first_seen).days
        status = "new"

        if age_days > 90:
            status = "expired"
        elif age_days > 7:
            status = "active"

        # Calculate expiration (90 days from first seen)
        expires_at = ioc.first_seen + timedelta(days=90)

        lifecycle = IOCLifecycle(
            ioc=ioc,
            status=status,
            created_at=ioc.first_seen,
            updated_at=now,
            expires_at=expires_at,
            times_seen=1,
            last_activity=ioc.last_seen,
        )

        return lifecycle

    def export_iocs(self, iocs: List[IOC], format: str = "stix") -> str:  # noqa: A002
        """Export IOCs in various formats.

        Args:
            iocs: List of IOCs to export
            format: Export format (stix, misp, csv, json)

        Returns:
            Exported data as string
        """
        if format == "json":
            return self._export_json(iocs)
        elif format == "csv":
            return self._export_csv(iocs)
        elif format == "stix":
            return self._export_stix(iocs)
        elif format == "misp":
            return self._export_misp(iocs)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(self, iocs: List[IOC]) -> str:
        """Export as JSON."""
        data = [ioc.dict() for ioc in iocs]
        return json.dumps(data, indent=2, default=str)

    def _export_csv(self, iocs: List[IOC]) -> str:
        """Export as CSV."""
        lines = ["type,value,confidence,first_seen,last_seen,tags,source"]

        for ioc in iocs:
            tags = ";".join(ioc.tags)
            lines.append(
                f"{ioc.ioc_type},{ioc.value},{ioc.confidence},"
                f"{ioc.first_seen},{ioc.last_seen},{tags},{ioc.source or ''}"
            )

        return "\n".join(lines)

    def _export_stix(self, iocs: List[IOC]) -> str:
        """Export as STIX 2.1."""
        bundle_objects = []

        for ioc in iocs:
            # Create STIX indicator
            indicator = {
                "type": "indicator",
                "spec_version": "2.1",
                "id": f"indicator--{hashlib.sha256(ioc.value.encode()).hexdigest()}",
                "created": ioc.first_seen.isoformat() + "Z",
                "modified": ioc.last_seen.isoformat() + "Z",
                "name": f"{ioc.ioc_type.upper()}: {ioc.value}",
                "pattern": self._create_stix_pattern(ioc),
                "pattern_type": "stix",
                "valid_from": ioc.first_seen.isoformat() + "Z",
                "labels": ioc.tags,
                "confidence": ioc.confidence,
            }
            bundle_objects.append(indicator)

        bundle = {
            "type": "bundle",
            "id": f"bundle--{hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()}",
            "objects": bundle_objects,
        }

        return json.dumps(bundle, indent=2)

    def _create_stix_pattern(self, ioc: IOC) -> str:
        """Create STIX pattern from IOC."""
        if ioc.ioc_type == "ip":
            return f"[ipv4-addr:value = '{ioc.value}']"
        elif ioc.ioc_type == "domain":
            return f"[domain-name:value = '{ioc.value}']"
        elif ioc.ioc_type == "hash":
            hash_type = "MD5"
            if ioc.context:
                hash_type = str(ioc.context.get("hash_type", "MD5"))
            return f"[file:hashes.{hash_type.upper()} = '{ioc.value}']"
        elif ioc.ioc_type == "url":
            return f"[url:value = '{ioc.value}']"
        elif ioc.ioc_type == "email":
            return f"[email-addr:value = '{ioc.value}']"
        return f"[x-custom:value = '{ioc.value}']"

    def _export_misp(self, iocs: List[IOC]) -> str:
        """Export as MISP format."""
        attributes: List[Dict[str, Any]] = []

        for ioc in iocs:
            attribute: Dict[str, Any] = {
                "type": self._get_misp_type(ioc.ioc_type),
                "value": ioc.value,
                "category": "Network activity",
                "to_ids": True,
                "comment": f"Confidence: {ioc.confidence}%",
                "timestamp": int(ioc.last_seen.timestamp()),
            }
            if ioc.tags:
                attribute["Tag"] = [{"name": tag} for tag in ioc.tags]

            attributes.append(attribute)

        event: Dict[str, Any] = {
            "Event": {
                "info": f"IOC Export {datetime.utcnow().isoformat()}",
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "threat_level_id": "2",
                "analysis": "2",
                "distribution": "3",
                "Attribute": attributes,
            }
        }

        return json.dumps(event, indent=2)

    def _get_misp_type(self, ioc_type: str) -> str:
        """Map IOC type to MISP type."""
        mapping = {
            "ip": "ip-dst",
            "domain": "domain",
            "hash": "md5",
            "url": "url",
            "email": "email-dst",
        }
        return mapping.get(ioc_type, "other")
