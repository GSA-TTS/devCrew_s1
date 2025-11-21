"""
SOPS Integration - File encryption with age and multi-key support.

TOOL-SEC-012: SOPS-compatible file encryption for devCrew_s1 data protection.
"""

import os
import json
import yaml
import base64
import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

logger = logging.getLogger(__name__)


@dataclass
class SOPSMetadata:
    """SOPS file metadata."""
    encrypted_at: str
    version: str = "3.8.0"
    age: List[str] = field(default_factory=list)
    pgp: List[str] = field(default_factory=list)
    kms: List[Dict[str, str]] = field(default_factory=list)
    gcp_kms: List[Dict[str, str]] = field(default_factory=list)
    azure_kv: List[Dict[str, str]] = field(default_factory=list)
    mac: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "sops": {
                "version": self.version,
                "encrypted_at": self.encrypted_at,
            }
        }

        if self.age:
            result["sops"]["age"] = [{"recipient": r} for r in self.age]
        if self.pgp:
            result["sops"]["pgp"] = [{"fp": fp} for fp in self.pgp]
        if self.kms:
            result["sops"]["kms"] = self.kms
        if self.gcp_kms:
            result["sops"]["gcp_kms"] = self.gcp_kms
        if self.azure_kv:
            result["sops"]["azure_kv"] = self.azure_kv
        if self.mac:
            result["sops"]["mac"] = self.mac

        return result


class SOPSManager:
    """
    SOPS-compatible file encryption manager.

    Supports:
    - Age encryption (recommended)
    - Multi-recipient encryption
    - YAML and JSON file formats
    - Key groups for threshold encryption
    """

    def __init__(
        self,
        age_recipients: Optional[List[str]] = None,
        age_key_file: Optional[Path] = None,
        sops_binary: str = "sops"
    ):
        """
        Initialize SOPS manager.

        Args:
            age_recipients: List of age public keys for encryption
            age_key_file: Path to age private key file for decryption
            sops_binary: Path to sops binary
        """
        self._age_recipients = age_recipients or []
        self._age_key_file = age_key_file
        self._sops_binary = sops_binary
        self._audit_log: list = []

        # Check for SOPS_AGE_KEY_FILE env var
        if not self._age_key_file:
            env_key_file = os.environ.get("SOPS_AGE_KEY_FILE")
            if env_key_file:
                self._age_key_file = Path(env_key_file)

        # Check for SOPS_AGE_RECIPIENTS env var
        if not self._age_recipients:
            env_recipients = os.environ.get("SOPS_AGE_RECIPIENTS")
            if env_recipients:
                self._age_recipients = [r.strip() for r in env_recipients.split(",")]

        logger.info(
            "SOPSManager initialized: recipients=%d, key_file=%s",
            len(self._age_recipients),
            self._age_key_file
        )

    def encrypt_file(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        in_place: bool = False
    ) -> Path:
        """
        Encrypt a file using SOPS.

        Args:
            input_path: Path to plaintext file
            output_path: Path for encrypted output (default: input_path.enc)
            in_place: Encrypt file in place

        Returns:
            Path to encrypted file
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if in_place:
            output_path = input_path
        elif output_path is None:
            output_path = input_path.with_suffix(input_path.suffix + ".enc")

        self._log_operation("encrypt_file", {
            "input": str(input_path),
            "output": str(output_path)
        })

        # Build SOPS command
        cmd = [self._sops_binary]

        # Add age recipients
        for recipient in self._age_recipients:
            cmd.extend(["--age", recipient])

        if in_place:
            cmd.extend(["--encrypt", "--in-place", str(input_path)])
        else:
            cmd.extend(["--encrypt", "--output", str(output_path), str(input_path)])

        try:
            result = subprocess.run(  # nosec B603 B607
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("File encrypted: %s -> %s", input_path, output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error("SOPS encryption failed: %s", e.stderr)
            raise RuntimeError(f"SOPS encryption failed: {e.stderr}")
        except FileNotFoundError:
            logger.warning("SOPS binary not found, using fallback encryption")
            return self._fallback_encrypt(input_path, output_path)

    def decrypt_file(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        in_place: bool = False
    ) -> Path:
        """
        Decrypt a SOPS-encrypted file.

        Args:
            input_path: Path to encrypted file
            output_path: Path for decrypted output
            in_place: Decrypt file in place

        Returns:
            Path to decrypted file
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if in_place:
            output_path = input_path
        elif output_path is None:
            # Remove .enc suffix if present
            if input_path.suffix == ".enc":
                output_path = input_path.with_suffix("")
            else:
                output_path = input_path.with_suffix(".dec" + input_path.suffix)

        self._log_operation("decrypt_file", {
            "input": str(input_path),
            "output": str(output_path)
        })

        # Build SOPS command
        cmd = [self._sops_binary]

        # Set age key file if available
        env = os.environ.copy()
        if self._age_key_file and self._age_key_file.exists():
            env["SOPS_AGE_KEY_FILE"] = str(self._age_key_file)

        if in_place:
            cmd.extend(["--decrypt", "--in-place", str(input_path)])
        else:
            cmd.extend(["--decrypt", "--output", str(output_path), str(input_path)])

        try:
            result = subprocess.run(  # nosec B603 B607
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            logger.info("File decrypted: %s -> %s", input_path, output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error("SOPS decryption failed: %s", e.stderr)
            raise RuntimeError(f"SOPS decryption failed: {e.stderr}")
        except FileNotFoundError:
            logger.warning("SOPS binary not found, using fallback decryption")
            return self._fallback_decrypt(input_path, output_path)

    def encrypt_data(
        self,
        data: Dict[str, Any],
        format: str = "yaml"
    ) -> str:
        """
        Encrypt a dictionary and return as encrypted string.

        Args:
            data: Dictionary to encrypt
            format: Output format (yaml or json)

        Returns:
            Encrypted content string
        """
        self._log_operation("encrypt_data", {"format": format})

        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=f".{format}",
            delete=False
        ) as f:
            if format == "yaml":
                yaml.dump(data, f, default_flow_style=False)
            else:
                json.dump(data, f, indent=2)
            temp_input = Path(f.name)

        try:
            temp_output = temp_input.with_suffix(f".{format}.enc")
            self.encrypt_file(temp_input, temp_output)

            with open(temp_output) as f:
                encrypted_content = f.read()

            return encrypted_content
        finally:
            temp_input.unlink(missing_ok=True)
            if temp_output.exists():
                temp_output.unlink()

    def decrypt_data(self, encrypted_content: str, format: str = "yaml") -> Dict[str, Any]:
        """
        Decrypt encrypted content string to dictionary.

        Args:
            encrypted_content: Encrypted content string
            format: Content format (yaml or json)

        Returns:
            Decrypted dictionary
        """
        self._log_operation("decrypt_data", {"format": format})

        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=f".{format}.enc",
            delete=False
        ) as f:
            f.write(encrypted_content)
            temp_input = Path(f.name)

        try:
            temp_output = temp_input.with_suffix("")
            self.decrypt_file(temp_input, temp_output)

            with open(temp_output) as f:
                if format == "yaml":
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        finally:
            temp_input.unlink(missing_ok=True)
            if temp_output.exists():
                temp_output.unlink()

    def rotate_keys(
        self,
        file_path: Path,
        new_recipients: Optional[List[str]] = None,
        remove_recipients: Optional[List[str]] = None
    ) -> None:
        """
        Rotate encryption keys for a SOPS file.

        Args:
            file_path: Path to encrypted file
            new_recipients: New age recipients to add
            remove_recipients: Recipients to remove
        """
        file_path = Path(file_path)

        self._log_operation("rotate_keys", {
            "file": str(file_path),
            "add": new_recipients,
            "remove": remove_recipients
        })

        # Build command
        cmd = [self._sops_binary, "updatekeys"]

        if new_recipients:
            for recipient in new_recipients:
                cmd.extend(["--add-age", recipient])

        if remove_recipients:
            for recipient in remove_recipients:
                cmd.extend(["--rm-age", recipient])

        cmd.append(str(file_path))

        try:
            subprocess.run(  # nosec B603 B607
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Keys rotated for: %s", file_path)
        except subprocess.CalledProcessError as e:
            logger.error("Key rotation failed: %s", e.stderr)
            raise RuntimeError(f"Key rotation failed: {e.stderr}")

    def _fallback_encrypt(self, input_path: Path, output_path: Path) -> Path:
        """
        Fallback encryption when SOPS is not available.

        Uses internal AES-256-GCM encryption with age-like format.
        """
        from .encryption_engine import AESGCMCipher, generate_key

        with open(input_path) as f:
            plaintext = f.read()

        key = generate_key()
        cipher = AESGCMCipher(key)
        result = cipher.encrypt(plaintext.encode())

        # Create SOPS-like structure
        encrypted_data = {
            "data": base64.b64encode(result.ciphertext).decode(),
            "sops": {
                "version": "fallback",
                "encrypted_at": datetime.now(timezone.utc).isoformat(),
                "nonce": base64.b64encode(result.nonce).decode(),
                "key": base64.b64encode(key).decode(),  # In real SOPS, key would be wrapped
            }
        }

        suffix = input_path.suffix
        if suffix in (".yaml", ".yml"):
            with open(output_path, "w") as f:
                yaml.dump(encrypted_data, f, default_flow_style=False)
        else:
            with open(output_path, "w") as f:
                json.dump(encrypted_data, f, indent=2)

        logger.warning("Used fallback encryption (not SOPS-compatible)")
        return output_path

    def _fallback_decrypt(self, input_path: Path, output_path: Path) -> Path:
        """
        Fallback decryption for files encrypted with fallback method.
        """
        from .encryption_engine import AESGCMCipher

        suffix = input_path.suffix
        with open(input_path) as f:
            if suffix in (".yaml", ".yml", ".enc"):
                try:
                    encrypted_data = yaml.safe_load(f)
                except yaml.YAMLError:
                    f.seek(0)
                    encrypted_data = json.load(f)
            else:
                encrypted_data = json.load(f)

        if encrypted_data.get("sops", {}).get("version") != "fallback":
            raise RuntimeError("File requires SOPS binary for decryption")

        sops_meta = encrypted_data["sops"]
        key = base64.b64decode(sops_meta["key"])
        nonce = base64.b64decode(sops_meta["nonce"])
        ciphertext = base64.b64decode(encrypted_data["data"])

        cipher = AESGCMCipher(key)
        result = cipher.decrypt(ciphertext, nonce)

        with open(output_path, "w") as f:
            f.write(result.plaintext.decode())

        logger.warning("Used fallback decryption")
        return output_path

    def get_audit_log(self) -> list:
        """Return audit log of SOPS operations."""
        return self._audit_log.copy()

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log a SOPS operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        })


def create_age_key() -> Dict[str, str]:
    """
    Generate a new age key pair.

    Returns:
        Dictionary with 'public_key' and 'private_key'
    """
    try:
        result = subprocess.run(  # nosec B603 B607
            ["age-keygen"],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse output
        lines = result.stdout.strip().split("\n")
        public_key = None
        for line in lines:
            if line.startswith("# public key:"):
                public_key = line.split(": ")[1]
            elif line.startswith("AGE-SECRET-KEY"):
                private_key = line

        return {
            "public_key": public_key,
            "private_key": private_key
        }
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error("Failed to generate age key: %s", e)
        raise RuntimeError("age-keygen not available")
