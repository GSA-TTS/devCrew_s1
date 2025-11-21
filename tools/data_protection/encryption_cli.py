#!/usr/bin/env python3
"""
Encryption CLI - Command-line interface for data protection operations.

TOOL-SEC-012: CLI for devCrew_s1 data protection platform.

Usage:
    encryption_cli.py encrypt <file> [--key <key>] [--algorithm <alg>] [--output <file>]
    encryption_cli.py decrypt <file> [--key <key>] [--output <file>]
    encryption_cli.py rotate <file> --old-key <key> --new-key <key>
    encryption_cli.py keygen [--algorithm <alg>] [--output <file>]
    encryption_cli.py derive --password <pass> [--salt <salt>] [--algorithm <alg>]
    encryption_cli.py envelope encrypt <file> [--output <file>]
    encryption_cli.py envelope decrypt <file> [--output <file>]
    encryption_cli.py sops encrypt <file> [--recipients <keys>] [--output <file>]
    encryption_cli.py sops decrypt <file> [--output <file>]
    encryption_cli.py vault get <path>
    encryption_cli.py vault set <path> <value>
"""

import argparse
import base64
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.data_protection.encryption_engine import (
    AESGCMCipher,
    RSACipher,
    NaClCipher,
    generate_key,
)
from tools.data_protection.key_manager import KeyManager
from tools.data_protection.envelope_encryption import EnvelopeEncryption
from tools.data_protection.sops_integration import SOPSManager
from tools.data_protection.secrets_integration import VaultClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def cmd_encrypt(args: argparse.Namespace) -> int:
    """Encrypt a file."""
    input_path = Path(args.file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    # Get or generate key
    if args.key:
        key = base64.b64decode(args.key)
    elif args.key_file:
        with open(args.key_file, "rb") as f:
            key = f.read()
    else:
        key = generate_key()
        logger.info("Generated key: %s", base64.b64encode(key).decode())

    # Select cipher
    algorithm = args.algorithm or "AES-256-GCM"
    if algorithm == "AES-256-GCM":
        cipher = AESGCMCipher(key)
    elif algorithm == "NaCl":
        cipher = NaClCipher(key)
    else:
        logger.error("Unsupported algorithm: %s", algorithm)
        return 1

    # Read and encrypt
    with open(input_path, "rb") as f:
        plaintext = f.read()

    result = cipher.encrypt(plaintext)

    # Prepare output
    output_data = {
        "algorithm": result.algorithm,
        "nonce": base64.b64encode(result.nonce).decode() if result.nonce else None,
        "ciphertext": base64.b64encode(result.ciphertext).decode(),
        "timestamp": result.timestamp,
    }

    # Write output
    output_path = Path(args.output) if args.output else input_path.with_suffix(".enc")
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info("Encrypted: %s -> %s", input_path, output_path)
    return 0


def cmd_decrypt(args: argparse.Namespace) -> int:
    """Decrypt a file."""
    input_path = Path(args.file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    # Load encrypted data
    with open(input_path) as f:
        encrypted_data = json.load(f)

    # Get key
    if args.key:
        key = base64.b64decode(args.key)
    elif args.key_file:
        with open(args.key_file, "rb") as f:
            key = f.read()
    else:
        logger.error("Key required for decryption")
        return 1

    # Select cipher
    algorithm = encrypted_data.get("algorithm", "AES-256-GCM")
    if "AES" in algorithm:
        cipher = AESGCMCipher(key)
    elif "NaCl" in algorithm:
        cipher = NaClCipher(key)
    else:
        logger.error("Unsupported algorithm: %s", algorithm)
        return 1

    # Decrypt
    ciphertext = base64.b64decode(encrypted_data["ciphertext"])
    nonce = base64.b64decode(encrypted_data["nonce"]) if encrypted_data.get("nonce") else None

    result = cipher.decrypt(ciphertext, nonce)

    # Write output
    output_path = Path(args.output) if args.output else input_path.with_suffix(".dec")
    with open(output_path, "wb") as f:
        f.write(result.plaintext)

    logger.info("Decrypted: %s -> %s", input_path, output_path)
    return 0


def cmd_keygen(args: argparse.Namespace) -> int:
    """Generate encryption key."""
    algorithm = args.algorithm or "AES-256-GCM"

    if algorithm in ("AES-256-GCM", "NaCl"):
        key = generate_key()
        key_b64 = base64.b64encode(key).decode()

        if args.output:
            with open(args.output, "wb") as f:
                f.write(key)
            logger.info("Key saved to: %s", args.output)
        else:
            print(f"Key (base64): {key_b64}")

    elif algorithm == "RSA":
        cipher = RSACipher(key_size=args.key_size or 2048)
        pub_key = cipher.export_public_key()
        priv_key = cipher.export_private_key()

        if args.output:
            pub_path = Path(args.output).with_suffix(".pub")
            priv_path = Path(args.output)

            with open(pub_path, "wb") as f:
                f.write(pub_key)
            with open(priv_path, "wb") as f:
                f.write(priv_key)

            logger.info("RSA keys saved to: %s, %s", priv_path, pub_path)
        else:
            print("Public Key:")
            print(pub_key.decode())
            print("\nPrivate Key:")
            print(priv_key.decode())
    else:
        logger.error("Unsupported algorithm: %s", algorithm)
        return 1

    return 0


def cmd_derive(args: argparse.Namespace) -> int:
    """Derive key from password."""
    km = KeyManager()

    password = args.password.encode()
    salt = base64.b64decode(args.salt) if args.salt else None
    algorithm = args.algorithm or "pbkdf2"

    if algorithm == "pbkdf2":
        result = km.derive_key_pbkdf2(password, salt)
    elif algorithm == "scrypt":
        result = km.derive_key_scrypt(password, salt)
    else:
        logger.error("Unsupported derivation algorithm: %s", algorithm)
        return 1

    print(f"Algorithm: {result.algorithm}")
    print(f"Salt (base64): {base64.b64encode(result.salt).decode()}")
    print(f"Key (base64): {base64.b64encode(result.key).decode()}")
    print(f"Key ID: {result.key_id}")

    return 0


def cmd_envelope_encrypt(args: argparse.Namespace) -> int:
    """Encrypt file using envelope encryption."""
    input_path = Path(args.file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    envelope = EnvelopeEncryption()

    with open(input_path, "rb") as f:
        plaintext = f.read()

    result = envelope.encrypt(plaintext)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".envelope")
    with open(output_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    logger.info("Envelope encrypted: %s -> %s", input_path, output_path)
    return 0


def cmd_envelope_decrypt(args: argparse.Namespace) -> int:
    """Decrypt envelope-encrypted file."""
    input_path = Path(args.file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    # Note: This requires the same EnvelopeEncryption instance with matching KEK
    # In production, KEK would be loaded from secure storage
    logger.warning("Decryption requires matching KEK from encryption")

    with open(input_path) as f:
        data = json.load(f)

    from tools.data_protection.envelope_encryption import EnvelopeEncryptedData
    encrypted = EnvelopeEncryptedData.from_dict(data)

    # In production, load the appropriate KEK
    envelope = EnvelopeEncryption()
    try:
        plaintext = envelope.decrypt(encrypted)
    except Exception as e:
        logger.error("Decryption failed (KEK mismatch?): %s", e)
        return 1

    output_path = Path(args.output) if args.output else input_path.with_suffix(".dec")
    with open(output_path, "wb") as f:
        f.write(plaintext)

    logger.info("Envelope decrypted: %s -> %s", input_path, output_path)
    return 0


def cmd_sops_encrypt(args: argparse.Namespace) -> int:
    """Encrypt file using SOPS."""
    input_path = Path(args.file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    recipients = args.recipients.split(",") if args.recipients else None
    sops = SOPSManager(age_recipients=recipients)

    output_path = Path(args.output) if args.output else None

    try:
        result_path = sops.encrypt_file(input_path, output_path)
        logger.info("SOPS encrypted: %s -> %s", input_path, result_path)
        return 0
    except Exception as e:
        logger.error("SOPS encryption failed: %s", e)
        return 1


def cmd_sops_decrypt(args: argparse.Namespace) -> int:
    """Decrypt SOPS-encrypted file."""
    input_path = Path(args.file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    key_file = Path(args.key_file) if args.key_file else None
    sops = SOPSManager(age_key_file=key_file)

    output_path = Path(args.output) if args.output else None

    try:
        result_path = sops.decrypt_file(input_path, output_path)
        logger.info("SOPS decrypted: %s -> %s", input_path, result_path)
        return 0
    except Exception as e:
        logger.error("SOPS decryption failed: %s", e)
        return 1


def cmd_vault_get(args: argparse.Namespace) -> int:
    """Get secret from Vault."""
    try:
        vault = VaultClient()
        secret = vault.get_secret(args.path, args.version)
        print(f"Value: {secret.value}")
        print(f"Version: {secret.version}")
        if secret.created_at:
            print(f"Created: {secret.created_at}")
        return 0
    except Exception as e:
        logger.error("Failed to get secret: %s", e)
        return 1


def cmd_vault_set(args: argparse.Namespace) -> int:
    """Set secret in Vault."""
    try:
        vault = VaultClient()
        version = vault.set_secret(args.path, args.value)
        logger.info("Secret stored: path=%s, version=%s", args.path, version)
        return 0
    except Exception as e:
        logger.error("Failed to set secret: %s", e)
        return 1


def cmd_rotate(args: argparse.Namespace) -> int:
    """Re-encrypt file with new key."""
    input_path = Path(args.file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    old_key = base64.b64decode(args.old_key)
    new_key = base64.b64decode(args.new_key)

    # Load encrypted data
    with open(input_path) as f:
        encrypted_data = json.load(f)

    # Decrypt with old key
    algorithm = encrypted_data.get("algorithm", "AES-256-GCM")
    if "AES" in algorithm:
        old_cipher = AESGCMCipher(old_key)
        new_cipher = AESGCMCipher(new_key)
    else:
        logger.error("Unsupported algorithm for rotation: %s", algorithm)
        return 1

    ciphertext = base64.b64decode(encrypted_data["ciphertext"])
    nonce = base64.b64decode(encrypted_data["nonce"]) if encrypted_data.get("nonce") else None

    plaintext = old_cipher.decrypt(ciphertext, nonce).plaintext

    # Re-encrypt with new key
    result = new_cipher.encrypt(plaintext)

    # Update file
    encrypted_data["ciphertext"] = base64.b64encode(result.ciphertext).decode()
    encrypted_data["nonce"] = base64.b64encode(result.nonce).decode() if result.nonce else None
    encrypted_data["timestamp"] = result.timestamp

    output_path = Path(args.output) if args.output else input_path
    with open(output_path, "w") as f:
        json.dump(encrypted_data, f, indent=2)

    logger.info("Key rotated: %s", output_path)
    logger.info("New key: %s", base64.b64encode(new_key).decode())
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Data Protection CLI - devCrew_s1 encryption toolkit"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # encrypt command
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a file")
    encrypt_parser.add_argument("file", help="File to encrypt")
    encrypt_parser.add_argument("--key", "-k", help="Encryption key (base64)")
    encrypt_parser.add_argument("--key-file", "-K", help="Key file path")
    encrypt_parser.add_argument("--algorithm", "-a", help="Algorithm (AES-256-GCM, NaCl)")
    encrypt_parser.add_argument("--output", "-o", help="Output file")

    # decrypt command
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt a file")
    decrypt_parser.add_argument("file", help="File to decrypt")
    decrypt_parser.add_argument("--key", "-k", help="Decryption key (base64)")
    decrypt_parser.add_argument("--key-file", "-K", help="Key file path")
    decrypt_parser.add_argument("--output", "-o", help="Output file")

    # keygen command
    keygen_parser = subparsers.add_parser("keygen", help="Generate encryption key")
    keygen_parser.add_argument("--algorithm", "-a", help="Algorithm (AES-256-GCM, NaCl, RSA)")
    keygen_parser.add_argument("--key-size", "-s", type=int, help="Key size (for RSA)")
    keygen_parser.add_argument("--output", "-o", help="Output file")

    # derive command
    derive_parser = subparsers.add_parser("derive", help="Derive key from password")
    derive_parser.add_argument("--password", "-p", required=True, help="Password")
    derive_parser.add_argument("--salt", "-s", help="Salt (base64)")
    derive_parser.add_argument("--algorithm", "-a", help="Algorithm (pbkdf2, scrypt)")

    # rotate command
    rotate_parser = subparsers.add_parser("rotate", help="Rotate encryption key")
    rotate_parser.add_argument("file", help="Encrypted file")
    rotate_parser.add_argument("--old-key", required=True, help="Old key (base64)")
    rotate_parser.add_argument("--new-key", required=True, help="New key (base64)")
    rotate_parser.add_argument("--output", "-o", help="Output file")

    # envelope subcommand
    envelope_parser = subparsers.add_parser("envelope", help="Envelope encryption")
    envelope_sub = envelope_parser.add_subparsers(dest="envelope_cmd")

    env_encrypt = envelope_sub.add_parser("encrypt", help="Envelope encrypt")
    env_encrypt.add_argument("file", help="File to encrypt")
    env_encrypt.add_argument("--output", "-o", help="Output file")

    env_decrypt = envelope_sub.add_parser("decrypt", help="Envelope decrypt")
    env_decrypt.add_argument("file", help="File to decrypt")
    env_decrypt.add_argument("--output", "-o", help="Output file")

    # sops subcommand
    sops_parser = subparsers.add_parser("sops", help="SOPS file encryption")
    sops_sub = sops_parser.add_subparsers(dest="sops_cmd")

    sops_encrypt = sops_sub.add_parser("encrypt", help="SOPS encrypt")
    sops_encrypt.add_argument("file", help="File to encrypt")
    sops_encrypt.add_argument("--recipients", "-r", help="Age recipients (comma-separated)")
    sops_encrypt.add_argument("--output", "-o", help="Output file")

    sops_decrypt = sops_sub.add_parser("decrypt", help="SOPS decrypt")
    sops_decrypt.add_argument("file", help="File to decrypt")
    sops_decrypt.add_argument("--key-file", "-k", help="Age key file")
    sops_decrypt.add_argument("--output", "-o", help="Output file")

    # vault subcommand
    vault_parser = subparsers.add_parser("vault", help="Vault secrets")
    vault_sub = vault_parser.add_subparsers(dest="vault_cmd")

    vault_get = vault_sub.add_parser("get", help="Get secret")
    vault_get.add_argument("path", help="Secret path")
    vault_get.add_argument("--version", "-v", help="Secret version")

    vault_set = vault_sub.add_parser("set", help="Set secret")
    vault_set.add_argument("path", help="Secret path")
    vault_set.add_argument("value", help="Secret value")

    args = parser.parse_args()

    if args.command == "encrypt":
        return cmd_encrypt(args)
    elif args.command == "decrypt":
        return cmd_decrypt(args)
    elif args.command == "keygen":
        return cmd_keygen(args)
    elif args.command == "derive":
        return cmd_derive(args)
    elif args.command == "rotate":
        return cmd_rotate(args)
    elif args.command == "envelope":
        if args.envelope_cmd == "encrypt":
            return cmd_envelope_encrypt(args)
        elif args.envelope_cmd == "decrypt":
            return cmd_envelope_decrypt(args)
    elif args.command == "sops":
        if args.sops_cmd == "encrypt":
            return cmd_sops_encrypt(args)
        elif args.sops_cmd == "decrypt":
            return cmd_sops_decrypt(args)
    elif args.command == "vault":
        if args.vault_cmd == "get":
            return cmd_vault_get(args)
        elif args.vault_cmd == "set":
            return cmd_vault_set(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
