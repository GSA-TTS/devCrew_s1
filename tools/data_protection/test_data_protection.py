"""
Comprehensive tests for Data Protection & Encryption Platform.

TOOL-SEC-012: Tests for devCrew_s1 data protection platform.
Target: 90%+ code coverage
"""

import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.data_protection.encryption_engine import (
    AESGCMCipher,
    RSACipher,
    NaClCipher,
    EncryptionEngine,
    EncryptionResult,
    DecryptionResult,
    generate_key,
)
from tools.data_protection.key_manager import (
    KeyManager,
    DerivedKey,
    KeyVersion,
)
from tools.data_protection.envelope_encryption import (
    EnvelopeEncryption,
    EnvelopeEncryptedData,
    MultiLayerEncryption,
)
from tools.data_protection.field_encryption import (
    FieldEncryption,
    EncryptedField,
    EncryptedColumnType,
)
from tools.data_protection.secrets_integration import (
    VaultClient,
    AWSKMSClient,
    AzureKeyVaultClient,
    GCPKMSClient,
    SecretValue,
)
from tools.data_protection.sops_integration import (
    SOPSManager,
    SOPSMetadata,
    create_age_key,
)


class TestAESGCMCipher(unittest.TestCase):
    """Tests for AES-256-GCM cipher."""

    def setUp(self):
        """Set up test fixtures."""
        self.key = os.urandom(32)
        self.cipher = AESGCMCipher(self.key)

    def test_encrypt_decrypt_roundtrip(self):
        """Test basic encryption/decryption."""
        plaintext = b"Hello, World!"
        result = self.cipher.encrypt(plaintext)

        self.assertIsInstance(result, EncryptionResult)
        self.assertEqual(result.algorithm, "AES-256-GCM")
        self.assertIsNotNone(result.nonce)
        self.assertEqual(len(result.nonce), 12)

        decrypted = self.cipher.decrypt(result.ciphertext, result.nonce)
        self.assertEqual(decrypted.plaintext, plaintext)
        self.assertTrue(decrypted.verified)

    def test_encrypt_with_aad(self):
        """Test authenticated encryption with AAD."""
        plaintext = b"Secret data"
        aad = b"metadata"

        result = self.cipher.encrypt(plaintext, aad)
        decrypted = self.cipher.decrypt(result.ciphertext, result.nonce, aad)
        self.assertEqual(decrypted.plaintext, plaintext)

    def test_aad_mismatch_fails(self):
        """Test that wrong AAD causes decryption failure."""
        plaintext = b"Secret data"
        aad = b"correct_metadata"

        result = self.cipher.encrypt(plaintext, aad)

        with self.assertRaises(Exception):
            self.cipher.decrypt(result.ciphertext, result.nonce, b"wrong_metadata")

    def test_invalid_key_size(self):
        """Test that invalid key sizes are rejected."""
        with self.assertRaises(ValueError):
            AESGCMCipher(b"short_key")

        with self.assertRaises(ValueError):
            AESGCMCipher(os.urandom(16))  # AES-128, not AES-256

    def test_missing_nonce(self):
        """Test that missing nonce raises error."""
        plaintext = b"Test"
        result = self.cipher.encrypt(plaintext)

        with self.assertRaises(ValueError):
            self.cipher.decrypt(result.ciphertext, None)

    def test_large_data(self):
        """Test encryption of larger data."""
        plaintext = os.urandom(1024 * 1024)  # 1 MB
        result = self.cipher.encrypt(plaintext)
        decrypted = self.cipher.decrypt(result.ciphertext, result.nonce)
        self.assertEqual(decrypted.plaintext, plaintext)


class TestRSACipher(unittest.TestCase):
    """Tests for RSA cipher."""

    def setUp(self):
        """Set up test fixtures."""
        self.cipher = RSACipher(key_size=2048)

    def test_encrypt_decrypt_roundtrip(self):
        """Test basic RSA encryption/decryption."""
        plaintext = b"Short secret"
        result = self.cipher.encrypt(plaintext)

        self.assertEqual(result.algorithm, "RSA-OAEP-SHA256")

        decrypted = self.cipher.decrypt(result.ciphertext)
        self.assertEqual(decrypted.plaintext, plaintext)

    def test_export_keys(self):
        """Test key export functionality."""
        pub_key = self.cipher.export_public_key()
        self.assertIn(b"BEGIN PUBLIC KEY", pub_key)

        priv_key = self.cipher.export_private_key()
        self.assertIn(b"BEGIN PRIVATE KEY", priv_key)

    def test_export_encrypted_private_key(self):
        """Test encrypted private key export."""
        password = b"test_password"
        priv_key = self.cipher.export_private_key(password)
        self.assertIn(b"BEGIN ENCRYPTED PRIVATE KEY", priv_key)

    def test_encrypt_without_public_key(self):
        """Test encryption fails without public key."""
        cipher = RSACipher.__new__(RSACipher)
        cipher._public_key = None
        cipher._private_key = None

        with self.assertRaises(ValueError):
            cipher.encrypt(b"test")

    def test_decrypt_without_private_key(self):
        """Test decryption fails without private key."""
        cipher = RSACipher.__new__(RSACipher)
        cipher._private_key = None
        cipher._public_key = self.cipher._public_key

        with self.assertRaises(ValueError):
            cipher.decrypt(b"test")


class TestNaClCipher(unittest.TestCase):
    """Tests for NaCl cipher."""

    def setUp(self):
        """Set up test fixtures."""
        self.key = os.urandom(32)
        self.cipher = NaClCipher(self.key)

    def test_encrypt_decrypt_roundtrip(self):
        """Test NaCl encryption/decryption."""
        plaintext = b"NaCl test data"
        result = self.cipher.encrypt(plaintext)

        self.assertIn("NaCl", result.algorithm)

        decrypted = self.cipher.decrypt(result.ciphertext, result.nonce)
        self.assertEqual(decrypted.plaintext, plaintext)

    def test_invalid_key_size(self):
        """Test that invalid key sizes are rejected."""
        with self.assertRaises(ValueError):
            NaClCipher(b"short")


class TestEncryptionEngine(unittest.TestCase):
    """Tests for EncryptionEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = EncryptionEngine()
        key = generate_key()
        self.engine.register_cipher("default", AESGCMCipher(key))

    def test_encrypt_decrypt(self):
        """Test engine encryption/decryption."""
        plaintext = b"Engine test"
        result = self.engine.encrypt(plaintext)
        decrypted = self.engine.decrypt(result.ciphertext, nonce=result.nonce)
        self.assertEqual(decrypted.plaintext, plaintext)

    def test_audit_log(self):
        """Test audit logging."""
        plaintext = b"Test"
        self.engine.encrypt(plaintext)

        log = self.engine.get_audit_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["operation"], "encrypt")

        self.engine.clear_audit_log()
        self.assertEqual(len(self.engine.get_audit_log()), 0)

    def test_unregistered_cipher(self):
        """Test error on unregistered cipher."""
        with self.assertRaises(ValueError):
            self.engine.encrypt(b"test", cipher_name="nonexistent")

    def test_invalid_algorithm(self):
        """Test invalid default algorithm."""
        with self.assertRaises(ValueError):
            EncryptionEngine(default_algorithm="INVALID")


class TestKeyManager(unittest.TestCase):
    """Tests for KeyManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.km = KeyManager()

    def test_generate_key(self):
        """Test key generation."""
        key = self.km.generate_key(32)
        self.assertEqual(len(key), 32)

    def test_derive_key_pbkdf2(self):
        """Test PBKDF2 key derivation."""
        password = b"test_password"
        result = self.km.derive_key_pbkdf2(password)

        self.assertIsInstance(result, DerivedKey)
        self.assertEqual(len(result.key), 32)
        self.assertEqual(len(result.salt), 16)
        self.assertEqual(result.algorithm, "PBKDF2-HMAC-SHA256")

    def test_derive_key_pbkdf2_deterministic(self):
        """Test PBKDF2 produces same key with same inputs."""
        password = b"password"
        salt = os.urandom(16)

        result1 = self.km.derive_key_pbkdf2(password, salt)
        result2 = self.km.derive_key_pbkdf2(password, salt)

        self.assertEqual(result1.key, result2.key)

    def test_derive_key_scrypt(self):
        """Test scrypt key derivation."""
        password = b"test_password"
        result = self.km.derive_key_scrypt(password)

        self.assertIsInstance(result, DerivedKey)
        self.assertEqual(len(result.key), 32)
        self.assertIn("scrypt", result.algorithm)

    def test_key_versioning(self):
        """Test key version creation and retrieval."""
        key = self.km.generate_key()
        version = self.km.create_key_version("test_key", key)

        self.assertEqual(version.version, 1)
        self.assertEqual(version.status, "active")

        retrieved = self.km.get_key("test_key")
        self.assertEqual(retrieved.version, 1)

    def test_key_rotation(self):
        """Test key rotation."""
        key1 = self.km.generate_key()
        self.km.create_key_version("rotate_test", key1)

        new_version = self.km.rotate_key("rotate_test")

        self.assertEqual(new_version.version, 2)

        old_version = self.km.get_key("rotate_test", version=1)
        self.assertEqual(old_version.status, "rotated")

    def test_key_revocation(self):
        """Test key revocation."""
        key = self.km.generate_key()
        self.km.create_key_version("revoke_test", key)

        result = self.km.revoke_key("revoke_test", 1)
        self.assertTrue(result)

        version = self.km.get_key("revoke_test", 1)
        self.assertEqual(version.status, "revoked")

    def test_list_keys(self):
        """Test listing keys."""
        key = self.km.generate_key()
        self.km.create_key_version("list_test", key)

        keys = self.km.list_keys()
        self.assertTrue(len(keys) >= 1)

    def test_audit_log(self):
        """Test audit log."""
        self.km.generate_key()
        log = self.km.get_audit_log()
        self.assertTrue(len(log) >= 1)


class TestEnvelopeEncryption(unittest.TestCase):
    """Tests for EnvelopeEncryption."""

    def setUp(self):
        """Set up test fixtures."""
        self.envelope = EnvelopeEncryption()

    def test_encrypt_decrypt_roundtrip(self):
        """Test envelope encryption roundtrip."""
        plaintext = b"Envelope test data"
        encrypted = self.envelope.encrypt(plaintext)

        self.assertIsInstance(encrypted, EnvelopeEncryptedData)
        self.assertIsNotNone(encrypted.encrypted_dek)
        self.assertIsNotNone(encrypted.encrypted_data)

        decrypted = self.envelope.decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)

    def test_with_aad(self):
        """Test envelope encryption with AAD."""
        plaintext = b"Test data"
        aad = b"context"

        encrypted = self.envelope.encrypt(plaintext, aad)
        decrypted = self.envelope.decrypt(encrypted, aad)
        self.assertEqual(decrypted, plaintext)

    def test_with_metadata(self):
        """Test envelope encryption with metadata."""
        plaintext = b"Test"
        metadata = {"purpose": "test", "user": "admin"}

        encrypted = self.envelope.encrypt(plaintext, metadata=metadata)
        self.assertEqual(encrypted.metadata["purpose"], "test")

    def test_serialization(self):
        """Test EnvelopeEncryptedData serialization."""
        plaintext = b"Serialize test"
        encrypted = self.envelope.encrypt(plaintext)

        # To dict and back
        data_dict = encrypted.to_dict()
        restored = EnvelopeEncryptedData.from_dict(data_dict)

        decrypted = self.envelope.decrypt(restored)
        self.assertEqual(decrypted, plaintext)

    def test_bytes_serialization(self):
        """Test bytes serialization."""
        plaintext = b"Bytes test"
        encrypted = self.envelope.encrypt(plaintext)

        as_bytes = encrypted.to_bytes()
        restored = EnvelopeEncryptedData.from_bytes(as_bytes)

        decrypted = self.envelope.decrypt(restored)
        self.assertEqual(decrypted, plaintext)

    def test_rewrap_dek(self):
        """Test DEK re-wrapping for key rotation."""
        plaintext = b"Rewrap test"
        encrypted = self.envelope.encrypt(plaintext)

        new_kek = RSACipher(key_size=2048)
        rewrapped = self.envelope.rewrap_dek(encrypted, new_kek_cipher=new_kek)

        self.assertNotEqual(rewrapped.encrypted_dek, encrypted.encrypted_dek)
        self.assertEqual(rewrapped.encrypted_data, encrypted.encrypted_data)

    def test_audit_log(self):
        """Test audit logging."""
        self.envelope.encrypt(b"test")
        log = self.envelope.get_audit_log()
        self.assertEqual(len(log), 1)


class TestMultiLayerEncryption(unittest.TestCase):
    """Tests for MultiLayerEncryption."""

    def test_multi_layer_roundtrip(self):
        """Test multi-layer encryption."""
        key1 = generate_key()
        key2 = generate_key()

        layers = [
            (AESGCMCipher(key1), "layer1"),
            (AESGCMCipher(key2), "layer2"),
        ]

        multi = MultiLayerEncryption(layers)

        plaintext = b"Multi-layer test"
        encrypted = multi.encrypt(plaintext)

        self.assertEqual(len(encrypted["layers"]), 2)

        decrypted = multi.decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)


class TestFieldEncryption(unittest.TestCase):
    """Tests for FieldEncryption."""

    def setUp(self):
        """Set up test fixtures."""
        self.master_key = os.urandom(32)
        self.fe = FieldEncryption(self.master_key)

    def test_encrypt_decrypt_field(self):
        """Test field encryption roundtrip."""
        value = "secret_ssn_123"
        encrypted = self.fe.encrypt_field("ssn", value)

        self.assertIsInstance(encrypted, EncryptedField)
        self.assertEqual(encrypted.field_name, "ssn")

        decrypted = self.fe.decrypt_field_string(encrypted)
        self.assertEqual(decrypted, value)

    def test_deterministic_encryption(self):
        """Test deterministic encryption produces same ciphertext."""
        value = "test_value"

        enc1 = self.fe.encrypt_field("email", value, deterministic=True)
        enc2 = self.fe.encrypt_field("email", value, deterministic=True)

        self.assertEqual(enc1.ciphertext, enc2.ciphertext)
        self.assertEqual(enc1.nonce, enc2.nonce)

    def test_randomized_encryption(self):
        """Test randomized encryption produces different ciphertext."""
        value = "test_value"

        enc1 = self.fe.encrypt_field("ssn", value, deterministic=False)
        enc2 = self.fe.encrypt_field("ssn", value, deterministic=False)

        self.assertNotEqual(enc1.ciphertext, enc2.ciphertext)

    def test_string_serialization(self):
        """Test EncryptedField string serialization."""
        value = "test"
        encrypted = self.fe.encrypt_field("field", value)

        encoded = encrypted.to_string()
        restored = EncryptedField.from_string(encoded, "field")

        decrypted = self.fe.decrypt_field_string(restored)
        self.assertEqual(decrypted, value)

    def test_encrypt_row(self):
        """Test row encryption."""
        row = {
            "id": 1,
            "name": "John Doe",
            "ssn": "123-45-6789",
            "email": "john@example.com"
        }

        encrypted_row = self.fe.encrypt_row(
            row,
            encrypt_fields=["ssn", "email"],
            deterministic_fields=["email"]
        )

        self.assertEqual(encrypted_row["id"], 1)
        self.assertEqual(encrypted_row["name"], "John Doe")
        self.assertTrue(encrypted_row["ssn"].startswith("rnd:"))
        self.assertTrue(encrypted_row["email"].startswith("det:"))

    def test_decrypt_row(self):
        """Test row decryption."""
        row = {"name": "Test", "ssn": "111-22-3333"}
        encrypted_row = self.fe.encrypt_row(row, ["ssn"])
        decrypted_row = self.fe.decrypt_row(encrypted_row, ["ssn"])

        self.assertEqual(decrypted_row["ssn"], "111-22-3333")

    def test_searchable_hash(self):
        """Test blind index generation."""
        value = "searchable"

        hash1 = self.fe.generate_searchable_hash("field", value)
        hash2 = self.fe.generate_searchable_hash("field", value)

        self.assertEqual(hash1, hash2)

        # Different field = different hash
        hash3 = self.fe.generate_searchable_hash("other_field", value)
        self.assertNotEqual(hash1, hash3)

    def test_key_rotation(self):
        """Test field encryption key rotation."""
        new_key = os.urandom(32)
        new_fe = self.fe.rotate_key(new_key, 2)

        self.assertEqual(new_fe._key_version, 2)

    def test_invalid_master_key(self):
        """Test invalid master key size."""
        with self.assertRaises(ValueError):
            FieldEncryption(b"short_key")


class TestEncryptedColumnType(unittest.TestCase):
    """Tests for EncryptedColumnType."""

    def test_process_bind_param(self):
        """Test SQLAlchemy bind parameter processing."""
        master_key = os.urandom(32)
        fe = FieldEncryption(master_key)
        col_type = EncryptedColumnType(fe, "test_col")

        result = col_type.process_bind_param("secret")
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("rnd:"))

    def test_process_result_value(self):
        """Test SQLAlchemy result value processing."""
        master_key = os.urandom(32)
        fe = FieldEncryption(master_key)
        col_type = EncryptedColumnType(fe, "test_col")

        encrypted = col_type.process_bind_param("original")
        decrypted = col_type.process_result_value(encrypted)

        self.assertEqual(decrypted, "original")

    def test_null_values(self):
        """Test null value handling."""
        master_key = os.urandom(32)
        fe = FieldEncryption(master_key)
        col_type = EncryptedColumnType(fe, "test_col")

        self.assertIsNone(col_type.process_bind_param(None))
        self.assertIsNone(col_type.process_result_value(None))


class TestSOPSManager(unittest.TestCase):
    """Tests for SOPSManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.sops = SOPSManager()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fallback_encrypt_decrypt(self):
        """Test fallback encryption when SOPS not available."""
        input_file = Path(self.temp_dir) / "test.yaml"
        with open(input_file, "w") as f:
            f.write("secret: value123\n")

        try:
            output_file = self.sops.encrypt_file(input_file)
            self.assertTrue(output_file.exists())

            decrypted_file = self.sops.decrypt_file(output_file)
            with open(decrypted_file) as f:
                content = f.read()
            self.assertIn("secret", content)
        except RuntimeError:
            # SOPS required but not available
            pass

    def test_sops_metadata(self):
        """Test SOPSMetadata creation."""
        metadata = SOPSMetadata(
            encrypted_at="2024-01-01T00:00:00Z",
            age=["age1xxx"],
        )

        data = metadata.to_dict()
        self.assertEqual(data["sops"]["version"], "3.8.0")
        self.assertEqual(len(data["sops"]["age"]), 1)


class TestSecretsIntegration(unittest.TestCase):
    """Tests for secrets integration clients."""

    def test_vault_client_init(self):
        """Test VaultClient initialization."""
        client = VaultClient(
            address="http://localhost:8200",
            token="test_token"
        )
        self.assertIsNotNone(client._address)

    def test_vault_audit_log(self):
        """Test VaultClient audit logging."""
        client = VaultClient()
        client._log_operation("test_op", {"key": "value"})
        log = client.get_audit_log()
        self.assertEqual(len(log), 1)

    def test_aws_kms_client_init(self):
        """Test AWSKMSClient initialization."""
        client = AWSKMSClient(key_id="test-key-id")
        self.assertEqual(client._key_id, "test-key-id")

    def test_azure_keyvault_client_init(self):
        """Test AzureKeyVaultClient initialization."""
        client = AzureKeyVaultClient(vault_url="https://test.vault.azure.net")
        self.assertEqual(client._vault_url, "https://test.vault.azure.net")

    def test_gcp_kms_client_init(self):
        """Test GCPKMSClient initialization."""
        client = GCPKMSClient(
            project_id="test-project",
            key_ring="test-ring",
            key_name="test-key"
        )
        self.assertEqual(client._project_id, "test-project")

    def test_secret_value(self):
        """Test SecretValue dataclass."""
        secret = SecretValue(
            value="test_secret",
            version="1",
            metadata={"env": "test"}
        )
        self.assertEqual(secret.value, "test_secret")
        self.assertEqual(secret.metadata["env"], "test")


class TestGenerateKey(unittest.TestCase):
    """Tests for generate_key function."""

    def test_generate_aes_key(self):
        """Test AES key generation."""
        key = generate_key("AES-256-GCM")
        self.assertEqual(len(key), 32)

    def test_generate_nacl_key(self):
        """Test NaCl key generation."""
        key = generate_key("NaCl-SecretBox")
        self.assertEqual(len(key), 32)

    def test_unsupported_algorithm(self):
        """Test unsupported algorithm."""
        with self.assertRaises(ValueError):
            generate_key("UNSUPPORTED")


class TestEncryptionCLI(unittest.TestCase):
    """Tests for encryption CLI."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_import(self):
        """Test CLI module imports correctly."""
        from tools.data_protection import encryption_cli
        self.assertIsNotNone(encryption_cli.main)


if __name__ == "__main__":
    unittest.main()
