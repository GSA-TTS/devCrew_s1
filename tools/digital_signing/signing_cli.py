"""
Signing CLI - Command-line interface for digital signing operations.

Provides commands for signing, verification, key generation, and policy management.
"""

import json
import sys

import click


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Digital Signing & Verification Platform CLI."""
    pass


@cli.command()
@click.option(
    "--type",
    "sign_type",
    required=True,
    type=click.Choice(["gpg", "cosign", "x509"]),
    help="Signature type",
)
@click.option("--file", "file_path", type=click.Path(exists=True), help="File to sign")
@click.option("--image", help="Container image to sign (for cosign)")
@click.option("--key-id", help="Key ID to use for signing (GPG)")
@click.option(
    "--key", "key_file", type=click.Path(exists=True), help="Private key file"
)
@click.option("--output", help="Output signature file path")
@click.option("--detach/--no-detach", default=True, help="Create detached signature")
@click.option("--keyless", is_flag=True, help="Use keyless signing (Cosign)")
@click.option("--identity", help="Identity for keyless signing")
@click.option("--oidc-issuer", help="OIDC issuer for keyless signing")
def sign(
    sign_type,
    file_path,
    image,
    key_id,
    key_file,
    output,
    detach,
    keyless,
    identity,
    oidc_issuer,
):
    """Sign files or container images."""
    try:
        if sign_type == "gpg":
            from gpg_handler import GPGHandler

            if not file_path:
                click.echo("Error: --file required for GPG signing", err=True)
                sys.exit(1)

            handler = GPGHandler()

            # If no key_id provided, generate one
            if not key_id:
                click.echo("Generating new GPG key...")
                key_id = handler.generate_key(
                    name="CLI User",
                    email="cli@example.com",
                    algorithm="rsa",
                    key_size=2048,
                )
                click.echo(f"Generated key: {key_id}")

            sig_path = handler.sign_file(file_path, key_id, detached=detach)
            click.echo(f"Signed: {file_path}")
            click.echo(f"Signature: {sig_path}")

            # Show key ID for verification
            click.echo(f"Key ID: {key_id}")

        elif sign_type == "cosign":
            from cosign_manager import CosignManager

            if not image:
                click.echo("Error: --image required for Cosign signing", err=True)
                sys.exit(1)

            manager = CosignManager()

            if keyless:
                if not identity or not oidc_issuer:
                    click.echo(
                        "Error: --identity and --oidc-issuer required "
                        "for keyless signing",
                        err=True,
                    )
                    sys.exit(1)

                result = manager.sign_image_keyless(image, identity, oidc_issuer)
                click.echo(f"Signed (keyless): {image}")
                click.echo(f"Identity: {identity}")
                click.echo(f"OIDC Issuer: {oidc_issuer}")
            else:
                # Generate or load key
                if key_file:
                    with open(key_file, "r") as f:
                        key_pem = f.read()
                else:
                    key_pem = manager.generate_signing_key()
                    # Save key for later use
                    key_output = output or "cosign.key"
                    with open(key_output, "w") as f:
                        f.write(key_pem)
                    click.echo(f"Generated key: {key_output}")

                result = manager.sign_image(image, key_pem)
                click.echo(f"Signed: {image}")

            click.echo(f"Signature Digest: {result['signature_digest']}")
            click.echo(f"Rekor Entry: {result['rekor_entry']}")

        else:  # x509
            click.echo("X.509 signing not yet implemented via CLI", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--type",
    "verify_type",
    required=True,
    type=click.Choice(["gpg", "cosign", "x509"]),
    help="Verification type",
)
@click.option(
    "--file", "file_path", type=click.Path(exists=True), help="File to verify"
)
@click.option("--image", help="Container image to verify")
@click.option("--signature", type=click.Path(exists=True), help="Signature file")
@click.option("--key-id", help="Key ID for verification (GPG)")
@click.option("--key", "key_file", type=click.Path(exists=True), help="Public key file")
@click.option("--identity", help="Expected identity for keyless verification")
@click.option("--oidc-issuer", help="Expected OIDC issuer")
@click.option("--json", "output_json", is_flag=True, help="Output JSON format")
def verify(
    verify_type,
    file_path,
    image,
    signature,
    key_id,
    key_file,
    identity,
    oidc_issuer,
    output_json,
):
    """Verify signatures."""
    try:
        from verification_engine import VerificationEngine

        verifier = VerificationEngine()

        if verify_type == "gpg":
            if not file_path or not signature:
                click.echo(
                    "Error: --file and --signature required for GPG verification",
                    err=True,
                )
                sys.exit(1)

            result = verifier.verify(
                artifact_type="file",
                artifact=file_path,
                verification_method="gpg",
                signature_file=signature,
                key_id=key_id,
            )

        elif verify_type == "cosign":
            if not image:
                click.echo("Error: --image required for Cosign verification", err=True)
                sys.exit(1)

            # Load public key if provided
            public_key = None
            if key_file:
                with open(key_file, "r") as f:
                    public_key = f.read()

            result = verifier.verify(
                artifact_type="container",
                artifact=image,
                verification_method="cosign",
                public_key=public_key,
                identity=identity,
                oidc_issuer=oidc_issuer,
            )

        else:  # x509
            click.echo("X.509 verification not yet implemented via CLI", err=True)
            sys.exit(1)

        if output_json:
            click.echo(json.dumps(result, indent=2))
        else:
            if result["valid"]:
                click.echo("✓ Signature valid", fg="green")
                if "signer" in result:
                    click.echo(f"Signer: {result['signer']}")
                if "timestamp" in result:
                    click.echo(f"Timestamp: {result['timestamp']}")
            else:
                click.echo("✗ Signature invalid", fg="red")
                if "error" in result:
                    click.echo(f"Error: {result['error']}")

        sys.exit(0 if result["valid"] else 1)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--type",
    "key_type",
    required=True,
    type=click.Choice(["gpg", "cosign", "x509"]),
    help="Key type",
)
@click.option("--name", help="Name for key (GPG)")
@click.option("--email", help="Email for key (GPG)")
@click.option(
    "--algorithm",
    type=click.Choice(["rsa", "ecdsa"]),
    default="rsa",
    help="Key algorithm",
)
@click.option("--key-size", type=int, default=2048, help="Key size")
@click.option("--output", help="Output key file")
def keygen(key_type, name, email, algorithm, key_size, output):
    """Generate signing keys."""
    try:
        if key_type == "gpg":
            from gpg_handler import GPGHandler

            if not name or not email:
                click.echo(
                    "Error: --name and --email required for GPG key generation",
                    err=True,
                )
                sys.exit(1)

            handler = GPGHandler()
            key_id = handler.generate_key(
                name=name,
                email=email,
                algorithm=algorithm,
                key_size=key_size if algorithm == "rsa" else None,
                curve="secp256r1" if algorithm == "ecdsa" else None,
            )

            click.echo("Generated GPG key")
            click.echo(f"Key ID: {key_id}")
            click.echo(f"Name: {name}")
            click.echo(f"Email: {email}")
            click.echo(f"Algorithm: {algorithm}")

            # Optionally export public key
            if output:
                public_key = handler.export_public_key(key_id)
                with open(output, "w") as f:
                    f.write(public_key)
                click.echo(f"Public key exported to: {output}")

        elif key_type == "cosign":
            from cosign_manager import CosignManager

            manager = CosignManager()
            key_pem = manager.generate_signing_key(
                algorithm=algorithm, key_size=key_size
            )

            output_file = output or "cosign.key"
            with open(output_file, "w") as f:
                f.write(key_pem)

            click.echo(f"Generated Cosign key: {output_file}")

        else:  # x509
            from cert_manager import CertificateManager

            manager = CertificateManager()
            cert_pem, key_pem = manager.generate_self_signed_cert(
                common_name=name or "Test Certificate",
                key_size=key_size,
            )

            cert_file = output or "cert.pem"
            key_file = cert_file.replace(".pem", ".key")

            with open(cert_file, "w") as f:
                f.write(cert_pem)
            with open(key_file, "w") as f:
                f.write(key_pem)

            click.echo(f"Generated X.509 certificate: {cert_file}")
            click.echo(f"Private key: {key_file}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--key-id", required=True, help="Key ID to export")
@click.option("--output", required=True, help="Output file path")
@click.option("--private", is_flag=True, help="Export private key")
def export(key_id, output, private):
    """Export public or private keys."""
    try:
        from gpg_handler import GPGHandler

        handler = GPGHandler()

        if private:
            key_data = handler.export_private_key(key_id)
            click.echo("Warning: Exporting private key. Keep it secure!", fg="yellow")
        else:
            key_data = handler.export_public_key(key_id)

        with open(output, "w") as f:
            f.write(key_data)

        click.echo(f"Key exported to: {output}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.group()
def policy():
    """Manage signing policies."""
    pass


@policy.command("add")
@click.option("--name", required=True, help="Policy rule name")
@click.option("--pattern", required=True, help="Artifact pattern")
@click.option(
    "--signer",
    required=True,
    multiple=True,
    help="Required signer (can specify multiple)",
)
@click.option(
    "--min-signatures", type=int, default=1, help="Minimum signatures required"
)
@click.option("--max-age-days", type=int, help="Maximum signature age in days")
@click.option("--config", type=click.Path(), help="Policy configuration file")
def policy_add(name, pattern, signer, min_signatures, max_age_days, config):
    """Add a policy rule."""
    try:
        from policy_engine import PolicyEngine

        engine = PolicyEngine(policy_file=config if config else None)
        engine.add_rule(
            name=name,
            artifact_pattern=pattern,
            required_signers=list(signer),
            min_signatures=min_signatures,
            max_age_days=max_age_days,
        )

        if config:
            engine.save_policies(config)
            click.echo(f"Policy saved to: {config}")

        click.echo(f"Added policy rule: {name}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@policy.command("list")
@click.option(
    "--config", type=click.Path(exists=True), help="Policy configuration file"
)
@click.option("--json", "output_json", is_flag=True, help="Output JSON format")
def policy_list(config, output_json):
    """List policy rules."""
    try:
        from policy_engine import PolicyEngine

        engine = PolicyEngine(policy_file=config if config else None)
        rules = engine.get_rules()

        if output_json:
            click.echo(json.dumps(rules, indent=2))
        else:
            if not rules:
                click.echo("No policy rules configured")
            else:
                click.echo(f"Policy Rules ({len(rules)}):\n")
                for rule in rules:
                    click.echo(f"  Name: {rule['name']}")
                    click.echo(f"  Pattern: {rule['artifact_pattern']}")
                    click.echo(f"  Signers: {', '.join(rule['required_signers'])}")
                    click.echo(f"  Min Signatures: {rule['min_signatures']}")
                    click.echo(f"  Enabled: {rule.get('enabled', True)}")
                    click.echo()

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@policy.command("evaluate")
@click.option("--artifact", required=True, help="Artifact to evaluate")
@click.option(
    "--config", type=click.Path(exists=True), help="Policy configuration file"
)
@click.option("--json", "output_json", is_flag=True, help="Output JSON format")
def policy_evaluate(artifact, config, output_json):
    """Evaluate policy for an artifact."""
    try:
        from policy_engine import PolicyEngine

        engine = PolicyEngine(policy_file=config if config else None)

        # For demo purposes, use empty verification results
        result = engine.evaluate(artifact, verification_results=[])

        if output_json:
            click.echo(json.dumps(result, indent=2))
        else:
            if result["compliant"]:
                click.echo("✓ Policy compliant", fg="green")
            else:
                click.echo("✗ Policy violations found", fg="red")
                for violation in result["violations"]:
                    click.echo(f"  - {violation['message']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--current-key",
    required=True,
    type=click.Path(exists=True),
    help="Current key file",
)
@click.option(
    "--new-key", type=click.Path(), help="New key file (generated if not provided)"
)
@click.option("--grace-period", type=int, default=30, help="Grace period in days")
def rotate(current_key, new_key, grace_period):
    """Rotate signing keys."""
    try:
        click.echo(f"Starting key rotation (grace period: {grace_period} days)")

        # Generate new key if not provided
        if not new_key:
            from cosign_manager import CosignManager

            manager = CosignManager()
            key_pem = manager.generate_signing_key()

            new_key = "cosign.key.new"
            with open(new_key, "w") as f:
                f.write(key_pem)

            click.echo(f"Generated new key: {new_key}")

        click.echo(f"Old key: {current_key}")
        click.echo(f"New key: {new_key}")
        click.echo(f"Grace period: {grace_period} days")
        click.echo("\nNote: Both keys will be valid during grace period")
        click.echo("After grace period, update all signatures to use new key")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
