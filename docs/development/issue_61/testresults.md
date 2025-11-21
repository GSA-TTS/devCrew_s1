============================= test session starts ==============================
platform darwin -- Python 3.12.9, pytest-8.4.1, pluggy-1.6.0 -- /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
cachedir: .pytest_cache
metadata: {'Python': '3.12.9', 'Platform': 'macOS-26.1-arm64-arm-64bit', 'Packages': {'pytest': '8.4.1', 'pluggy': '1.6.0'}, 'Plugins': {'env': '1.1.5', 'asyncio': '1.1.0', 'xdist': '3.8.0', 'json-report': '1.5.0', 'httpx': '0.35.0', 'timeout': '2.4.0', 'metadata': '3.1.1', 'Faker': '37.8.0', 'hypothesis': '6.100.0', 'anyio': '4.10.0', 'langsmith': '0.4.20', 'cov': '6.2.1', 'mock': '3.14.1'}}
hypothesis profile 'default' -> database=DirectoryBasedExampleDatabase(PosixPath('/Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/.hypothesis/examples'))
rootdir: /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing
plugins: env-1.1.5, asyncio-1.1.0, xdist-3.8.0, json-report-1.5.0, httpx-0.35.0, timeout-2.4.0, metadata-3.1.1, Faker-37.8.0, hypothesis-6.100.0, anyio-4.10.0, langsmith-0.4.20, cov-6.2.1, mock-3.14.1
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 39 items

test_signing.py::TestGPGHandler::test_export_private_key PASSED          [  2%]
test_signing.py::TestGPGHandler::test_export_public_key PASSED           [  5%]
test_signing.py::TestGPGHandler::test_generate_ecdsa_key PASSED          [  7%]
test_signing.py::TestGPGHandler::test_generate_rsa_key PASSED            [ 10%]
test_signing.py::TestGPGHandler::test_key_expiration PASSED              [ 12%]
test_signing.py::TestGPGHandler::test_sign_file_detached PASSED          [ 15%]
test_signing.py::TestGPGHandler::test_verify_signature_invalid PASSED    [ 17%]
test_signing.py::TestGPGHandler::test_verify_signature_valid PASSED      [ 20%]
test_signing.py::TestCertificateManager::test_check_certificate_expiration PASSED [ 23%]
test_signing.py::TestCertificateManager::test_generate_csr PASSED        [ 25%]
test_signing.py::TestCertificateManager::test_generate_self_signed_cert PASSED [ 28%]
test_signing.py::TestCertificateManager::test_validate_certificate_chain PASSED [ 30%]
test_signing.py::TestCosignManager::test_generate_slsa_provenance PASSED [ 33%]
test_signing.py::TestCosignManager::test_sign_attestation PASSED         [ 35%]
test_signing.py::TestCosignManager::test_sign_image_keyless PASSED       [ 38%]
test_signing.py::TestCosignManager::test_sign_image_with_key PASSED      [ 41%]
test_signing.py::TestCosignManager::test_verify_image_signature PASSED   [ 43%]
test_signing.py::TestVerificationEngine::test_batch_verification PASSED  [ 46%]
test_signing.py::TestVerificationEngine::test_trust_root_validation PASSED [ 48%]
test_signing.py::TestVerificationEngine::test_verify_cosign_signature PASSED [ 51%]
test_signing.py::TestVerificationEngine::test_verify_gpg_signature PASSED [ 53%]
test_signing.py::TestHSMClient::test_delete_key PASSED                   [ 56%]
test_signing.py::TestHSMClient::test_generate_key_in_hsm PASSED          [ 58%]
test_signing.py::TestHSMClient::test_initialize_hsm_mock PASSED          [ 61%]
test_signing.py::TestHSMClient::test_list_keys PASSED                    [ 64%]
test_signing.py::TestHSMClient::test_sign_with_hsm_key PASSED            [ 66%]
test_signing.py::TestHSMClient::test_verify_with_hsm_key PASSED          [ 69%]
test_signing.py::TestPolicyEngine::test_add_policy_rule PASSED           [ 71%]
test_signing.py::TestPolicyEngine::test_evaluate_policy_fail PASSED      [ 74%]
test_signing.py::TestPolicyEngine::test_evaluate_policy_pass PASSED      [ 76%]
test_signing.py::TestPolicyEngine::test_multiple_signers_required PASSED [ 79%]
test_signing.py::TestPolicyEngine::test_pattern_matching PASSED          [ 82%]
test_signing.py::TestSigningCLI::test_cli_export_command PASSED          [ 84%]
test_signing.py::TestSigningCLI::test_cli_keygen_command PASSED          [ 87%]
test_signing.py::TestSigningCLI::test_cli_policy_command PASSED          [ 89%]
test_signing.py::TestSigningCLI::test_cli_sign_command PASSED            [ 92%]
test_signing.py::TestSigningCLI::test_cli_verify_command PASSED          [ 94%]
test_signing.py::TestIntegration::test_full_container_signing_workflow PASSED [ 97%]
test_signing.py::TestIntegration::test_full_gpg_workflow PASSED          [100%]

=============================== warnings summary ===============================
test_signing.py::TestCertificateManager::test_check_certificate_expiration
test_signing.py::TestCertificateManager::test_generate_self_signed_cert
test_signing.py::TestCertificateManager::test_validate_certificate_chain
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:81: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    .not_valid_before(datetime.utcnow())

test_signing.py::TestCertificateManager::test_check_certificate_expiration
test_signing.py::TestCertificateManager::test_generate_self_signed_cert
test_signing.py::TestCertificateManager::test_validate_certificate_chain
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:82: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    .not_valid_after(datetime.utcnow() + timedelta(days=validity_days))

test_signing.py::TestCertificateManager::test_check_certificate_expiration
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:371: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    return datetime.utcnow() > cert.not_valid_after

test_signing.py::TestCertificateManager::test_check_certificate_expiration
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:371: CryptographyDeprecationWarning: Properties that return a naïve datetime object have been deprecated. Please switch to not_valid_after_utc.
    return datetime.utcnow() > cert.not_valid_after

test_signing.py::TestCertificateManager::test_check_certificate_expiration
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:384: CryptographyDeprecationWarning: Properties that return a naïve datetime object have been deprecated. Please switch to not_valid_after_utc.
    delta = cert.not_valid_after - datetime.utcnow()

test_signing.py::TestCertificateManager::test_check_certificate_expiration
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:384: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    delta = cert.not_valid_after - datetime.utcnow()

test_signing.py::TestCertificateManager::test_validate_certificate_chain
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:255: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    .not_valid_before(datetime.utcnow())

test_signing.py::TestCertificateManager::test_validate_certificate_chain
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:256: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    .not_valid_after(datetime.utcnow() + timedelta(days=validity_days))

test_signing.py::TestCertificateManager::test_validate_certificate_chain
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:346: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    now = datetime.utcnow()

test_signing.py::TestCertificateManager::test_validate_certificate_chain
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:347: CryptographyDeprecationWarning: Properties that return a naïve datetime object have been deprecated. Please switch to not_valid_before_utc.
    if not (cert.not_valid_before <= now <= cert.not_valid_after):

test_signing.py::TestCertificateManager::test_validate_certificate_chain
  /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/digital_signing/cert_manager.py:347: CryptographyDeprecationWarning: Properties that return a naïve datetime object have been deprecated. Please switch to not_valid_after_utc.
    if not (cert.not_valid_before <= now <= cert.not_valid_after):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 39 passed, 15 warnings in 1.62s ========================
