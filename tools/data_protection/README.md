# Data Protection & Encryption Platform

**TOOL-SEC-012** - Comprehensive encryption toolkit for devCrew_s1.

## Overview

This platform provides enterprise-grade data protection capabilities including:

- **AES-256-GCM** - Authenticated symmetric encryption
- **RSA-OAEP** - Asymmetric encryption for key wrapping
- **NaCl/libsodium** - Modern cryptographic primitives
- **Envelope Encryption** - DEK/KEK pattern for scalable encryption
- **Field-Level Encryption** - Database column encryption with searchable hashing
- **SOPS Integration** - File encryption with age/PGP support
- **Secrets Management** - Vault, AWS KMS, Azure Key Vault, GCP KMS integration

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### AES-256-GCM Encryption

```python
from tools.data_protection import AESGCMCipher, generate_key

# Generate a key
key = generate_key()

# Create cipher and encrypt
cipher = AESGCMCipher(key)
result = cipher.encrypt(b"sensitive data")

# Decrypt
decrypted = cipher.decrypt(result.ciphertext, result.nonce)
print(decrypted.plaintext)
```

### Key Derivation

```python
from tools.data_protection import KeyManager

km = KeyManager()

# PBKDF2 derivation
derived = km.derive_key_pbkdf2(b"password123")
print(f"Key: {derived.key.hex()}")
print(f"Salt: {derived.salt.hex()}")

# scrypt derivation
derived = km.derive_key_scrypt(b"password123")
```

### Envelope Encryption

```python
from tools.data_protection import EnvelopeEncryption

envelope = EnvelopeEncryption()

# Encrypt data
encrypted = envelope.encrypt(b"large dataset")

# Store encrypted.to_dict() in database
stored = encrypted.to_dict()

# Later, restore and decrypt
from tools.data_protection.envelope_encryption import EnvelopeEncryptedData
restored = EnvelopeEncryptedData.from_dict(stored)
plaintext = envelope.decrypt(restored)
```

### Field-Level Encryption

```python
from tools.data_protection import FieldEncryption
import os

master_key = os.urandom(32)
fe = FieldEncryption(master_key)

# Encrypt a database row
row = {"id": 1, "ssn": "123-45-6789", "email": "user@example.com"}
encrypted_row = fe.encrypt_row(
    row,
    encrypt_fields=["ssn", "email"],
    deterministic_fields=["email"]  # Enables equality queries
)

# Generate searchable hash for blind index
email_hash = fe.generate_searchable_hash("email", "user@example.com")
```

## CLI Usage

```bash
# Generate a key
python encryption_cli.py keygen --algorithm AES-256-GCM

# Encrypt a file
python encryption_cli.py encrypt secret.txt --key <base64_key>

# Decrypt a file
python encryption_cli.py decrypt secret.txt.enc --key <base64_key>

# Derive key from password
python encryption_cli.py derive --password "mypassword" --algorithm pbkdf2

# Rotate encryption key
python encryption_cli.py rotate encrypted.enc --old-key <old> --new-key <new>

# Envelope encryption
python encryption_cli.py envelope encrypt data.json
python encryption_cli.py envelope decrypt data.envelope

# SOPS operations
python encryption_cli.py sops encrypt config.yaml --recipients age1xxx
python encryption_cli.py sops decrypt config.yaml.enc

# Vault operations
python encryption_cli.py vault get secret/myapp
python encryption_cli.py vault set secret/myapp "value"
```

## Architecture

```
                    +------------------+
                    |  EncryptionEngine |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         |                   |                   |
+--------v-------+  +--------v-------+  +--------v-------+
|  AESGCMCipher  |  |   RSACipher    |  |   NaClCipher   |
+----------------+  +----------------+  +----------------+

+------------------+     +------------------+
|   KeyManager     |     | EnvelopeEncrypt  |
| - PBKDF2         |     | - DEK/KEK        |
| - scrypt         |     | - Multi-layer    |
| - Versioning     |     +------------------+
+------------------+

+------------------+     +------------------+
| FieldEncryption  |     |   SOPSManager    |
| - Deterministic  |     | - age support    |
| - Blind index    |     | - Multi-key      |
+------------------+     +------------------+

+------------------+
| SecretsIntegration|
| - Vault          |
| - AWS KMS        |
| - Azure KV       |
| - GCP KMS        |
+------------------+
```

## Security Considerations

1. **Key Management**: Store keys in secure vaults, never in code
2. **Key Rotation**: Regularly rotate keys using the built-in rotation support
3. **Audit Logging**: All operations are logged for compliance
4. **AAD Usage**: Use authenticated associated data for context binding
5. **Deterministic Encryption**: Only use for fields requiring equality search

## Testing

```bash
cd tools/data_protection
pytest test_data_protection.py -v --cov=. --cov-report=term-missing
```

## License

Internal use only - devCrew_s1 project.
