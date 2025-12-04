"""
Tests for Threat Intelligence Platform CLI.

This module provides comprehensive test coverage for the CLI interface,
including all commands, error handling, and configuration management.
"""

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest
import yaml
from click.testing import CliRunner
from tools.threat_intelligence.cli.threat_cli import cli


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config():
    """Create a temporary configuration file."""
    config_data = {
        "feeds": {
            "taxii_servers": [
                {
                    "url": "https://test-taxii.example.com/taxii/",
                    "collections": ["test-collection"],
                }
            ],
            "cve_sources": ["nvd"],
        },
        "correlation": {
            "min_confidence": 70,
            "risk_threshold": 60,
        },
        "enrichment": {
            "services": ["virustotal"],
            "api_keys": {"virustotal": "test_key"},
        },
        "output": {
            "formats": ["json"],
            "reports_dir": "./reports",
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(config_data, f)
        config_path = f.name

    yield config_path

    # Cleanup
    if os.path.exists(config_path):
        os.unlink(config_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_help(self, runner):
        """Test CLI help output."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Threat Intelligence Platform CLI" in result.output
        assert "ingest" in result.output
        assert "correlate" in result.output
        assert "vex" in result.output
        assert "ioc" in result.output
        assert "report" in result.output
        assert "attack" in result.output
        assert "config" in result.output

    def test_cli_version_options(self, runner):
        """Test CLI options."""
        result = runner.invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0

    def test_cli_quiet_mode(self, runner):
        """Test quiet mode flag."""
        result = runner.invoke(cli, ["--quiet", "--help"])
        assert result.exit_code == 0

    def test_cli_config_option(self, runner, temp_config):
        """Test custom config file option."""
        result = runner.invoke(cli, ["--config", temp_config, "--help"])
        assert result.exit_code == 0


class TestIngestCommand:
    """Test ingest command."""

    @patch("tools.threat_intelligence.cli.threat_cli.FeedAggregator")
    def test_ingest_taxii_feed(self, mock_aggregator, runner, temp_output_dir):
        """Test TAXII feed ingestion."""
        mock_instance = Mock()
        mock_instance.ingest_taxii.return_value = [
            {"type": "indicator", "value": "test"}
        ]
        mock_instance.deduplicate.return_value = [
            {"type": "indicator", "value": "test"}
        ]
        mock_aggregator.return_value = mock_instance

        output_file = os.path.join(temp_output_dir, "output.json")
        result = runner.invoke(
            cli,
            [
                "ingest",
                "--feed",
                "https://test-taxii.example.com/taxii/",
                "--format",
                "taxii21",
                "--collection",
                "test-collection",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        mock_instance.ingest_taxii.assert_called_once()

    @patch("tools.threat_intelligence.cli.threat_cli.FeedAggregator")
    def test_ingest_cve_feed(self, mock_aggregator, runner, temp_output_dir):
        """Test CVE feed ingestion."""
        mock_instance = Mock()
        mock_instance.ingest_cve.return_value = [{"type": "cve", "id": "CVE-2024-1234"}]
        mock_instance.deduplicate.return_value = [
            {"type": "cve", "id": "CVE-2024-1234"}
        ]
        mock_aggregator.return_value = mock_instance

        output_file = os.path.join(temp_output_dir, "cves.json")
        result = runner.invoke(
            cli,
            [
                "ingest",
                "--feed",
                "nvd",
                "--format",
                "cve",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        mock_instance.ingest_cve.assert_called_once()

    def test_ingest_missing_feed(self, runner):
        """Test ingest with missing --feed option."""
        result = runner.invoke(cli, ["ingest"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output

    @patch("tools.threat_intelligence.cli.threat_cli.FeedAggregator")
    def test_ingest_verbose_output(self, mock_aggregator, runner):
        """Test ingest with verbose flag."""
        mock_instance = Mock()
        mock_instance.ingest_stix.return_value = [
            {"type": "indicator", "value": "test1"},
            {"type": "malware", "value": "test2"},
        ]
        mock_instance.deduplicate.return_value = [
            {"type": "indicator", "value": "test1"},
            {"type": "malware", "value": "test2"},
        ]
        mock_aggregator.return_value = mock_instance

        result = runner.invoke(
            cli,
            [
                "--verbose",
                "ingest",
                "--feed",
                "./test.json",
                "--format",
                "stix",
            ],
        )

        assert "indicator" in result.output or result.exit_code == 0


class TestCorrelateCommand:
    """Test correlate command."""

    @patch("tools.threat_intelligence.cli.threat_cli.ThreatCorrelator")
    def test_correlate_sbom(self, mock_correlator, runner, temp_output_dir, tmp_path):
        """Test SBOM correlation."""
        mock_instance = Mock()
        mock_instance.correlate_sbom.return_value = [
            {
                "cve": "CVE-2024-1234",
                "severity": "HIGH",
                "risk_score": 85.0,
            }
        ]
        mock_correlator.return_value = mock_instance

        # Create dummy SBOM file
        sbom_file = tmp_path / "test.spdx.json"
        sbom_file.write_text(json.dumps({"packages": []}))

        output_file = os.path.join(temp_output_dir, "correlations.json")
        result = runner.invoke(
            cli,
            [
                "correlate",
                "--sbom",
                str(sbom_file),
                "--min-severity",
                "HIGH",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        mock_instance.correlate_sbom.assert_called_once()

    @patch("tools.threat_intelligence.cli.threat_cli.ThreatCorrelator")
    def test_correlate_assets(self, mock_correlator, runner, temp_output_dir, tmp_path):
        """Test asset correlation."""
        mock_instance = Mock()
        mock_instance.correlate_assets.return_value = [
            {
                "asset": "web-server-01",
                "threats": 5,
                "risk_score": 72.5,
            }
        ]
        mock_correlator.return_value = mock_instance

        # Create dummy assets file
        assets_file = tmp_path / "assets.json"
        assets_file.write_text(json.dumps({"assets": []}))

        output_file = os.path.join(temp_output_dir, "asset_risks.json")
        result = runner.invoke(
            cli,
            [
                "correlate",
                "--assets",
                str(assets_file),
                "--min-confidence",
                "80",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        mock_instance.correlate_assets.assert_called_once()

    def test_correlate_missing_inputs(self, runner, temp_output_dir):
        """Test correlate with no SBOM or assets."""
        output_file = os.path.join(temp_output_dir, "output.json")
        result = runner.invoke(cli, ["correlate", "--output", output_file])

        assert result.exit_code != 0
        assert "At least one" in result.output or "required" in result.output.lower()


class TestVEXCommand:
    """Test VEX command."""

    @patch("tools.threat_intelligence.cli.threat_cli.VEXGenerator")
    def test_vex_openvex_format(self, mock_generator, runner, temp_output_dir):
        """Test OpenVEX document generation."""
        mock_instance = Mock()
        mock_instance.generate_openvex.return_value = {
            "@context": "https://openvex.dev/ns",
            "statements": [{"status": "not_affected"}],
        }
        mock_generator.return_value = mock_instance

        output_file = os.path.join(temp_output_dir, "test.vex.json")
        result = runner.invoke(
            cli,
            [
                "vex",
                "--cve",
                "CVE-2024-1234",
                "--product",
                "pkg:npm/lodash@4.17.21",
                "--status",
                "not_affected",
                "--justification",
                "vulnerable_code_not_present",
                "--format",
                "openvex",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        mock_instance.generate_openvex.assert_called_once()

    @patch("tools.threat_intelligence.cli.threat_cli.VEXGenerator")
    def test_vex_csaf_format(self, mock_generator, runner, temp_output_dir):
        """Test CSAF document generation."""
        mock_instance = Mock()
        mock_instance.generate_csaf.return_value = {
            "document": {"category": "csaf_vex"}
        }
        mock_generator.return_value = mock_instance

        output_file = os.path.join(temp_output_dir, "test.csaf.json")
        result = runner.invoke(
            cli,
            [
                "vex",
                "--cve",
                "CVE-2024-5678",
                "--product",
                "pkg:pypi/requests@2.31.0",
                "--status",
                "fixed",
                "--format",
                "csaf",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        mock_instance.generate_csaf.assert_called_once()

    def test_vex_missing_required_args(self, runner, temp_output_dir):
        """Test VEX with missing required arguments."""
        output_file = os.path.join(temp_output_dir, "test.vex.json")
        result = runner.invoke(cli, ["vex", "--output", output_file])

        assert result.exit_code != 0

    def test_vex_not_affected_without_justification(self, runner, temp_output_dir):
        """Test not_affected status without justification."""
        output_file = os.path.join(temp_output_dir, "test.vex.json")
        result = runner.invoke(
            cli,
            [
                "vex",
                "--cve",
                "CVE-2024-1234",
                "--product",
                "pkg:npm/test@1.0.0",
                "--status",
                "not_affected",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code != 0
        assert "justification" in result.output.lower()


class TestIOCCommand:
    """Test IOC command."""

    def test_ioc_json_file(self, runner, temp_output_dir, tmp_path):
        """Test IOC processing from JSON file."""
        # Create test IOC file
        ioc_file = tmp_path / "iocs.json"
        ioc_data = [
            {"type": "ip", "value": "192.0.2.1"},
            {"type": "domain", "value": "example.com"},
        ]
        ioc_file.write_text(json.dumps(ioc_data))

        output_file = os.path.join(temp_output_dir, "processed_iocs.json")
        result = runner.invoke(
            cli,
            [
                "ioc",
                "--file",
                str(ioc_file),
                "--type",
                "all",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(output_file)

    def test_ioc_with_enrichment(self, runner, temp_output_dir, tmp_path):
        """Test IOC enrichment."""
        ioc_file = tmp_path / "iocs.json"
        ioc_data = [{"type": "ip", "value": "192.0.2.1"}]
        ioc_file.write_text(json.dumps(ioc_data))

        output_file = os.path.join(temp_output_dir, "enriched_iocs.json")
        result = runner.invoke(
            cli,
            [
                "ioc",
                "--file",
                str(ioc_file),
                "--enrich",
                "--confidence-threshold",
                "70",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0

    def test_ioc_csv_output(self, runner, temp_output_dir, tmp_path):
        """Test IOC CSV output format."""
        ioc_file = tmp_path / "iocs.json"
        ioc_data = [
            {"type": "ip", "value": "192.0.2.1"},
            {"type": "hash", "value": "abc123"},
        ]
        ioc_file.write_text(json.dumps(ioc_data))

        output_file = os.path.join(temp_output_dir, "iocs.csv")
        result = runner.invoke(
            cli,
            [
                "ioc",
                "--file",
                str(ioc_file),
                "--format",
                "csv",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(output_file)


class TestReportCommand:
    """Test report command."""

    def test_report_comprehensive(self, runner, temp_output_dir):
        """Test comprehensive report generation."""
        output_file = os.path.join(temp_output_dir, "comprehensive.json")
        result = runner.invoke(
            cli,
            [
                "report",
                "--type",
                "comprehensive",
                "--format",
                "json",
                "--timeframe",
                "7d",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(output_file)

        # Verify report structure
        with open(output_file, "r", encoding="utf-8") as f:
            report = json.load(f)
            assert "summary" in report
            assert "type" in report
            assert report["type"] == "comprehensive"

    def test_report_executive(self, runner, temp_output_dir):
        """Test executive report generation."""
        output_file = os.path.join(temp_output_dir, "executive.json")
        result = runner.invoke(
            cli,
            [
                "report",
                "--type",
                "executive",
                "--format",
                "json",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0

    def test_report_with_options(self, runner, temp_output_dir):
        """Test report with additional options."""
        output_file = os.path.join(temp_output_dir, "detailed.json")
        result = runner.invoke(
            cli,
            [
                "report",
                "--type",
                "technical",
                "--format",
                "json",
                "--include-iocs",
                "--include-mitigations",
                "--timeframe",
                "30d",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            report = json.load(f)
            assert "iocs" in report
            assert "mitigations" in report


class TestATTACKCommand:
    """Test ATT&CK command."""

    @patch("tools.threat_intelligence.cli.threat_cli.ATTACKMapper")
    def test_attack_technique_lookup(self, mock_mapper, runner):
        """Test ATT&CK technique lookup."""
        mock_instance = Mock()
        mock_instance.get_technique.return_value = {
            "id": "T1059",
            "name": "Command and Scripting Interpreter",
            "tactic": "execution",
        }
        mock_mapper.return_value = mock_instance

        result = runner.invoke(cli, ["attack", "--technique", "T1059"])

        assert result.exit_code == 0
        mock_instance.get_technique.assert_called_once_with("T1059")

    @patch("tools.threat_intelligence.cli.threat_cli.ATTACKMapper")
    def test_attack_coverage_analysis(self, mock_mapper, runner, tmp_path):
        """Test ATT&CK coverage analysis."""
        mock_instance = Mock()
        mock_instance.analyze_coverage.return_value = {
            "covered": 8,
            "not_covered": 6,
            "percentage": 57.1,
        }
        mock_mapper.return_value = mock_instance

        # Create test threat data
        threat_file = tmp_path / "threats.json"
        threat_file.write_text(json.dumps({"threats": []}))

        result = runner.invoke(
            cli,
            [
                "attack",
                "--threats",
                str(threat_file),
                "--coverage",
            ],
        )

        assert result.exit_code == 0

    @patch("tools.threat_intelligence.cli.threat_cli.ATTACKMapper")
    def test_attack_navigator_generation(
        self, mock_mapper, runner, temp_output_dir, tmp_path
    ):
        """Test ATT&CK Navigator layer generation."""
        mock_instance = Mock()
        mock_instance.generate_navigator_layer.return_value = {
            "name": "Threat Coverage",
            "versions": {"layer": "4.5"},
            "techniques": [],
        }
        mock_mapper.return_value = mock_instance

        threat_file = tmp_path / "threats.json"
        threat_file.write_text(json.dumps({"threats": []}))

        output_file = os.path.join(temp_output_dir, "navigator.json")
        result = runner.invoke(
            cli,
            [
                "attack",
                "--threats",
                str(threat_file),
                "--navigator",
                "--output",
                output_file,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(output_file)

    def test_attack_navigator_missing_output(self, runner, tmp_path):
        """Test navigator flag without output."""
        threat_file = tmp_path / "threats.json"
        threat_file.write_text(json.dumps({}))

        result = runner.invoke(
            cli,
            [
                "attack",
                "--threats",
                str(threat_file),
                "--navigator",
            ],
        )

        assert result.exit_code != 0
        assert "required" in result.output.lower()


class TestConfigCommand:
    """Test config command."""

    def test_config_show(self, runner, temp_config):
        """Test config show command."""
        result = runner.invoke(cli, ["--config", temp_config, "config", "--show"])

        assert result.exit_code == 0
        assert "feeds" in result.output

    def test_config_validate_valid(self, runner, temp_config):
        """Test config validation with valid config."""
        result = runner.invoke(cli, ["--config", temp_config, "config", "--validate"])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_config_validate_missing(self, runner):
        """Test config validation with missing config."""
        result = runner.invoke(
            cli, ["--config", "nonexistent.yaml", "config", "--validate"]
        )

        assert result.exit_code != 0

    def test_config_init(self, runner, temp_output_dir):
        """Test config initialization."""
        output_file = os.path.join(temp_output_dir, "new-config.yaml")
        result = runner.invoke(cli, ["config", "--init", "--output", output_file])

        assert result.exit_code == 0
        assert os.path.exists(output_file)

        # Verify config structure
        with open(output_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            assert "feeds" in config
            assert "correlation" in config
            assert "output" in config

    def test_config_init_default_path(self, runner):
        """Test config init with default path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(cli, ["config", "--init"])
                assert result.exit_code == 0
                assert os.path.exists("threat-config.yaml")
            finally:
                os.chdir(original_cwd)


class TestErrorHandling:
    """Test error handling."""

    @patch("tools.threat_intelligence.cli.threat_cli.FeedAggregator")
    def test_ingest_error_handling(self, mock_aggregator, runner):
        """Test error handling in ingest command."""
        mock_instance = Mock()
        mock_instance.ingest_taxii.side_effect = Exception("Connection failed")
        mock_aggregator.return_value = mock_instance

        result = runner.invoke(
            cli,
            [
                "ingest",
                "--feed",
                "https://invalid.example.com/taxii/",
                "--format",
                "taxii21",
            ],
        )

        assert result.exit_code == 1
        assert "failed" in result.output.lower()

    def test_invalid_config_file(self, runner, tmp_path):
        """Test invalid YAML config file."""
        bad_config = tmp_path / "bad.yaml"
        bad_config.write_text("invalid: yaml: content: {")

        result = runner.invoke(cli, ["--config", str(bad_config), "config", "--show"])

        # Should show warning but continue
        assert "Warning" in result.output or result.exit_code == 0


class TestOutputFormatting:
    """Test output formatting and Rich display."""

    def test_verbose_output(self, runner, tmp_path):
        """Test verbose output mode."""
        ioc_file = tmp_path / "iocs.json"
        ioc_file.write_text(json.dumps([{"type": "ip", "value": "192.0.2.1"}]))

        result = runner.invoke(
            cli,
            [
                "--verbose",
                "ioc",
                "--file",
                str(ioc_file),
                "--output",
                str(tmp_path / "out.json"),
            ],
        )

        assert result.exit_code == 0

    def test_quiet_output(self, runner, tmp_path):
        """Test quiet output mode."""
        ioc_file = tmp_path / "iocs.json"
        ioc_file.write_text(json.dumps([{"type": "ip", "value": "192.0.2.1"}]))

        result = runner.invoke(
            cli,
            [
                "--quiet",
                "ioc",
                "--file",
                str(ioc_file),
                "--output",
                str(tmp_path / "out.json"),
            ],
        )

        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
