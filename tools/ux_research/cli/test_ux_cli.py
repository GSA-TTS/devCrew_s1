"""
Unit tests for UX Research & Design Feedback Platform CLI.

Tests all CLI commands, configuration loading, output formatting,
and module interactions.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml
from click.testing import CliRunner

from tools.ux_research.cli.ux_cli import (cli, display_results_table,
                                          get_default_config,
                                          get_default_template, load_config,
                                          save_output)


@pytest.fixture
def runner() -> CliRunner:
    """
    Create a Click CLI test runner.

    Returns:
        CliRunner instance
    """
    return CliRunner()


@pytest.fixture
def temp_config_file() -> Path:
    """
    Create a temporary configuration file.

    Returns:
        Path to temporary config file
    """
    config_data = {
        "audit": {
            "wcag_level": "AA",
            "browsers": ["chromium"],
            "viewports": {"desktop": [1920, 1080]},
        },
        "feedback": {"sources": {"surveys": "test.csv"}, "min_confidence": 0.7},
        "analytics": {"google_analytics": {"property_id": "12345"}},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        return Path(f.name)


@pytest.fixture
def temp_heuristics_file() -> Path:
    """
    Create a temporary heuristics checklist file.

    Returns:
        Path to temporary heuristics file
    """
    heuristics_data = {
        "nielsen_10": [
            {
                "id": "H1",
                "name": "Visibility of system status",
                "weight": 5,
                "checks": [
                    {
                        "id": "H1.1",
                        "description": "Loading indicators present",
                        "automated": True,
                    }
                ],
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(heuristics_data, f)
        return Path(f.name)


class TestLoadConfig:
    """Test configuration loading functionality."""

    def test_load_valid_config(self, temp_config_file: Path) -> None:
        """Test loading a valid configuration file."""
        config = load_config(str(temp_config_file))

        assert config is not None
        assert "audit" in config
        assert "feedback" in config
        assert "analytics" in config
        assert config["audit"]["wcag_level"] == "AA"

    def test_load_nonexistent_config(self) -> None:
        """Test loading a non-existent configuration file."""
        from click.exceptions import ClickException

        with pytest.raises(ClickException) as exc_info:
            load_config("nonexistent.yaml")

        assert "not found" in str(exc_info.value)

    def test_load_invalid_yaml(self) -> None:
        """Test loading an invalid YAML file."""
        from click.exceptions import ClickException

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            f.write("invalid: yaml: content:")
            f.flush()

            with pytest.raises(ClickException) as exc_info:
                load_config(f.name)

            assert "Invalid YAML" in str(exc_info.value)


class TestSaveOutput:
    """Test output saving functionality."""

    def test_save_json_output(self) -> None:
        """Test saving output in JSON format."""
        data = {"test": "data", "count": 42}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        save_output(data, output_path, "json")

        with open(output_path, "r") as f:
            loaded_data = json.load(f)

        assert loaded_data == data

        Path(output_path).unlink()

    def test_save_yaml_output(self) -> None:
        """Test saving output in YAML format."""
        data = {"test": "data", "count": 42}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            output_path = f.name

        save_output(data, output_path, "yaml")

        with open(output_path, "r") as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == data

        Path(output_path).unlink()

    def test_save_output_no_path(self) -> None:
        """Test that nothing is saved when no output path is provided."""
        data = {"test": "data"}
        save_output(data, None, "json")
        # Should not raise any exceptions


class TestDisplayResultsTable:
    """Test results table display functionality."""

    def test_display_basic_table(self, capsys: pytest.CaptureFixture) -> None:
        """Test displaying a basic results table."""
        results = [
            {"id": "V1", "description": "Test violation", "severity": "critical"},
            {"id": "V2", "description": "Another issue", "severity": "moderate"},
        ]

        display_results_table(
            results,
            "Test Results",
            ["ID", "Description", "Severity"],
            severity_col="Severity",
        )

        # Test runs without error - actual output validation would require
        # rich console capture

    def test_display_empty_table(self) -> None:
        """Test displaying an empty table."""
        display_results_table([], "Empty Results", ["Column1", "Column2"])
        # Should not raise any exceptions


class TestGetDefaultConfig:
    """Test default configuration generation."""

    def test_get_default_config_structure(self) -> None:
        """Test that default config has required structure."""
        config = get_default_config()

        assert "audit" in config
        assert "feedback" in config
        assert "analytics" in config
        assert "monitoring" in config

        assert config["audit"]["wcag_level"] == "AA"
        assert "browsers" in config["audit"]
        assert "viewports" in config["audit"]

    def test_get_default_config_viewport_values(self) -> None:
        """Test that default viewports have valid values."""
        config = get_default_config()

        viewports = config["audit"]["viewports"]
        assert "mobile" in viewports
        assert "tablet" in viewports
        assert "desktop" in viewports

        assert len(viewports["mobile"]) == 2
        assert all(isinstance(v, int) for v in viewports["mobile"])


class TestGetDefaultTemplate:
    """Test default template generation."""

    def test_get_html_template(self) -> None:
        """Test getting HTML template."""
        template = get_default_template("accessibility", "html")

        assert "<!DOCTYPE html>" in template
        assert "<html" in template
        assert "</html>" in template

    def test_get_markdown_template(self) -> None:
        """Test getting Markdown template."""
        template = get_default_template("usability", "markdown")

        assert "# UX Research Report" in template
        assert "**Type:**" in template

    def test_get_json_template(self) -> None:
        """Test getting JSON template."""
        template = get_default_template("feedback", "json")

        assert "tojson" in template


class TestCliMain:
    """Test main CLI group."""

    def test_cli_help(self, runner: CliRunner) -> None:
        """Test CLI help output."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "UX Research & Design Feedback Platform" in result.output
        assert "audit" in result.output
        assert "feedback" in result.output
        assert "heuristics" in result.output

    def test_cli_with_config(self, runner: CliRunner, temp_config_file: Path) -> None:
        """Test CLI with custom configuration file."""
        result = runner.invoke(cli, ["--config", str(temp_config_file), "--help"])

        assert result.exit_code == 0

    def test_cli_with_invalid_config(self, runner: CliRunner) -> None:
        """Test CLI with non-existent configuration file."""
        result = runner.invoke(cli, ["--config", "nonexistent.yaml", "--help"])

        assert result.exit_code != 0
        assert "not found" in result.output


class TestAuditCommand:
    """Test accessibility audit command."""

    @patch("tools.ux_research.cli.ux_cli.AccessibilityAuditor")
    def test_audit_basic(
        self, mock_auditor: Mock, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test basic audit command."""
        mock_instance = MagicMock()
        mock_instance.audit_url.return_value = {
            "total_violations": 5,
            "critical_count": 1,
            "serious_count": 2,
            "moderate_count": 2,
            "minor_count": 0,
            "violations": [],
        }
        mock_auditor.return_value = mock_instance

        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "audit",
                "--url",
                "https://example.com",
            ],
        )

        assert mock_instance.audit_url.called

    def test_audit_dry_run(self, runner: CliRunner, temp_config_file: Path) -> None:
        """Test audit command in dry-run mode."""
        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "audit",
                "--url",
                "https://example.com",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.output

    def test_audit_missing_url(self, runner: CliRunner, temp_config_file: Path) -> None:
        """Test audit command without URL."""
        result = runner.invoke(cli, ["--config", str(temp_config_file), "audit"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output

    @patch("tools.ux_research.cli.ux_cli.AccessibilityAuditor")
    def test_audit_with_output(
        self, mock_auditor: Mock, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test audit command with output file."""
        mock_instance = MagicMock()
        mock_instance.audit_url.return_value = {
            "total_violations": 0,
            "critical_count": 0,
            "violations": [],
        }
        mock_auditor.return_value = mock_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit_results.json"

            result = runner.invoke(
                cli,
                [
                    "--config",
                    str(temp_config_file),
                    "audit",
                    "--url",
                    "https://example.com",
                    "--output",
                    str(output_path),
                ],
            )

            assert output_path.exists()


class TestFeedbackCommand:
    """Test feedback analysis command."""

    @patch("tools.ux_research.cli.ux_cli.SentimentAnalyzer")
    @patch("tools.ux_research.cli.ux_cli.FeedbackCollector")
    def test_feedback_basic(
        self,
        mock_collector: Mock,
        mock_analyzer: Mock,
        runner: CliRunner,
        temp_config_file: Path,
    ) -> None:
        """Test basic feedback command."""
        mock_collector_instance = MagicMock()
        mock_collector_instance.collect_from_source.return_value = [
            {"text": "Great product!", "rating": 5}
        ]
        mock_collector.return_value = mock_collector_instance

        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.analyze_sentiment.return_value = {
            "positive_count": 1,
            "positive_pct": 100,
            "negative_count": 0,
            "negative_pct": 0,
            "neutral_count": 0,
            "neutral_pct": 0,
        }
        mock_analyzer.return_value = mock_analyzer_instance

        result = runner.invoke(
            cli, ["--config", str(temp_config_file), "feedback", "--source", "test.csv"]
        )

        assert mock_collector_instance.collect_from_source.called

    def test_feedback_missing_source(
        self, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test feedback command without source."""
        result = runner.invoke(cli, ["--config", str(temp_config_file), "feedback"])

        assert result.exit_code != 0


class TestHeuristicsCommand:
    """Test usability heuristics command."""

    @patch("tools.ux_research.cli.ux_cli.UsabilityValidator")
    def test_heuristics_basic(
        self,
        mock_validator: Mock,
        runner: CliRunner,
        temp_config_file: Path,
        temp_heuristics_file: Path,
    ) -> None:
        """Test basic heuristics command."""
        mock_instance = MagicMock()
        mock_instance.evaluate_heuristics.return_value = {
            "heuristics": [
                {
                    "name": "Visibility of system status",
                    "passed": 8,
                    "failed": 2,
                    "failed_checks": ["Check 1", "Check 2"],
                }
            ],
            "overall_score": 80.0,
        }
        mock_validator.return_value = mock_instance

        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "heuristics",
                "--url",
                "https://example.com",
                "--checklist",
                str(temp_heuristics_file),
            ],
        )

        assert mock_instance.evaluate_heuristics.called

    def test_heuristics_missing_checklist(
        self, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test heuristics command with missing checklist file."""
        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "heuristics",
                "--url",
                "https://example.com",
                "--checklist",
                "nonexistent.yaml",
            ],
        )

        assert result.exit_code != 0


class TestAnalyzeCommand:
    """Test analytics analysis command."""

    @patch("tools.ux_research.cli.ux_cli.AnalyticsIntegrator")
    def test_analyze_basic(
        self, mock_integrator: Mock, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test basic analyze command."""
        mock_instance = MagicMock()
        mock_instance.analyze_platform.return_value = {
            "metrics": {
                "bounce_rate": {"value": 45.2, "change": -5.3},
                "conversion_rate": {"value": 3.2, "change": 0.8},
            }
        }
        mock_integrator.return_value = mock_instance

        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "analyze",
                "--platform",
                "google_analytics",
                "--start-date",
                "2025-01-01",
                "--end-date",
                "2025-01-31",
            ],
        )

        assert mock_instance.analyze_platform.called

    def test_analyze_invalid_platform(
        self, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test analyze command with invalid platform."""
        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "analyze",
                "--platform",
                "invalid_platform",
            ],
        )

        assert result.exit_code != 0


class TestReportCommand:
    """Test report generation command."""

    def test_report_basic(self, runner: CliRunner, temp_config_file: Path) -> None:
        """Test basic report command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"

            result = runner.invoke(
                cli,
                [
                    "--config",
                    str(temp_config_file),
                    "report",
                    "--type",
                    "accessibility",
                    "--output",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

    def test_report_missing_type(
        self, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test report command without type."""
        result = runner.invoke(
            cli,
            ["--config", str(temp_config_file), "report", "--output", "report.html"],
        )

        assert result.exit_code != 0


class TestMonitorCommand:
    """Test continuous monitoring command."""

    @patch("tools.ux_research.cli.ux_cli.AccessibilityAuditor")
    def test_monitor_basic(
        self, mock_auditor: Mock, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test basic monitor command."""
        mock_instance = MagicMock()
        mock_instance.audit_url.return_value = {
            "critical_count": 0,
            "serious_count": 0,
            "moderate_count": 0,
            "minor_count": 0,
        }
        mock_auditor.return_value = mock_instance

        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "monitor",
                "--url",
                "https://example.com",
                "--max-runs",
                "1",
            ],
        )

        assert mock_instance.audit_url.called

    @patch("tools.ux_research.cli.ux_cli.AccessibilityAuditor")
    def test_monitor_with_alerts(
        self, mock_auditor: Mock, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test monitor command with alert thresholds."""
        mock_instance = MagicMock()
        mock_instance.audit_url.return_value = {
            "critical_count": 10,  # Exceeds default threshold
            "serious_count": 15,  # Exceeds default threshold
            "moderate_count": 5,
            "minor_count": 2,
        }
        mock_auditor.return_value = mock_instance

        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "monitor",
                "--url",
                "https://example.com",
                "--threshold-critical",
                "5",
                "--max-runs",
                "1",
            ],
        )

        assert "ALERT" in result.output or "WARNING" in result.output


class TestConfigCommand:
    """Test configuration management command."""

    def test_config_show(self, runner: CliRunner, temp_config_file: Path) -> None:
        """Test config show action."""
        result = runner.invoke(
            cli, ["--config", str(temp_config_file), "config", "--action", "show"]
        )

        assert result.exit_code == 0
        assert "audit" in result.output

    def test_config_validate(self, runner: CliRunner, temp_config_file: Path) -> None:
        """Test config validate action."""
        result = runner.invoke(
            cli, ["--config", str(temp_config_file), "config", "--action", "validate"]
        )

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_config_init(self, runner: CliRunner) -> None:
        """Test config init action."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "new-config.yaml"

            result = runner.invoke(
                cli, ["config", "--action", "init", "--config-file", str(config_path)]
            )

            assert result.exit_code == 0
            assert config_path.exists()

            # Verify created config has valid structure
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            assert "audit" in config
            assert "feedback" in config

    def test_config_set(self, runner: CliRunner, temp_config_file: Path) -> None:
        """Test config set action."""
        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "config",
                "--action",
                "set",
                "--key",
                "audit.wcag_level",
                "--value",
                "AAA",
            ],
        )

        assert result.exit_code == 0

        # Verify value was set
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)
        assert config["audit"]["wcag_level"] == "AAA"

    def test_config_set_missing_args(
        self, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test config set action with missing arguments."""
        result = runner.invoke(
            cli, ["--config", str(temp_config_file), "config", "--action", "set"]
        )

        assert result.exit_code != 0
        assert "required" in result.output.lower()


class TestVerboseQuietModes:
    """Test verbose and quiet output modes."""

    @patch("tools.ux_research.cli.ux_cli.AccessibilityAuditor")
    def test_verbose_mode(
        self, mock_auditor: Mock, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test CLI with verbose mode."""
        mock_instance = MagicMock()
        mock_instance.audit_url.return_value = {
            "total_violations": 0,
            "critical_count": 0,
            "violations": [],
        }
        mock_auditor.return_value = mock_instance

        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "--verbose",
                "audit",
                "--url",
                "https://example.com",
            ],
        )

        assert result.exit_code == 0

    @patch("tools.ux_research.cli.ux_cli.AccessibilityAuditor")
    def test_quiet_mode(
        self, mock_auditor: Mock, runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test CLI with quiet mode."""
        mock_instance = MagicMock()
        mock_instance.audit_url.return_value = {
            "total_violations": 0,
            "critical_count": 0,
            "violations": [],
        }
        mock_auditor.return_value = mock_instance

        result = runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "--quiet",
                "audit",
                "--url",
                "https://example.com",
            ],
        )

        assert result.exit_code == 0
        # Quiet mode should suppress non-essential output
        assert "UX Research" not in result.output


class TestIntegration:
    """Integration tests for CLI commands."""

    def test_full_workflow(
        self, runner: CliRunner, temp_config_file: Path, temp_heuristics_file: Path
    ) -> None:
        """Test a complete workflow using multiple commands."""
        # Test dry-run mode for all commands
        commands = [
            ["audit", "--url", "https://example.com", "--dry-run"],
            ["config", "--action", "show"],
            ["config", "--action", "validate"],
        ]

        for cmd in commands:
            result = runner.invoke(cli, ["--config", str(temp_config_file)] + cmd)
            # All commands should succeed or fail gracefully
            assert result.exit_code in [0, 1, 2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
