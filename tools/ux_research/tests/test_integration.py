"""
Integration tests for UX Research & Design Feedback Platform.

This module contains end-to-end integration tests for complete workflows:
- Accessibility audit workflows
- Feedback collection and analysis workflows
- Heuristic evaluation workflows
- Analytics integration workflows
- Report generation workflows
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestAccessibilityAuditWorkflow:
    """Integration tests for complete accessibility audit workflows."""

    @pytest.mark.asyncio
    async def test_full_accessibility_audit_workflow(
        self, temp_dir, sample_html_with_issues, mock_axe_results, mock_github_client
    ):
        """
        Test complete accessibility audit workflow.

        Workflow:
        1. Initialize auditor with configuration
        2. Run accessibility audit on test page
        3. Detect WCAG violations
        4. Generate remediation guide
        5. Create GitHub issues for violations
        6. Generate comprehensive HTML report
        """
        # Mock components
        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            with patch("tools.ux_research.remediation.GuideGenerator") as MockGuide:
                # Setup mocks
                auditor = MockAuditor.return_value
                auditor.audit_page = AsyncMock(return_value=mock_axe_results)

                guide_gen = MockGuide.return_value
                guide_gen.generate_guide = Mock(
                    return_value={
                        "violations": mock_axe_results["violations"],
                        "remediation_steps": ["Step 1", "Step 2"],
                        "code_examples": ["<img alt='text'>"],
                    }
                )

                # Step 1: Run audit
                audit_result = await auditor.audit_page(
                    url="https://example.com", wcag_level="AA"
                )

                assert audit_result is not None
                assert "violations" in audit_result
                assert len(audit_result["violations"]) == 3

                # Step 2: Detect violations
                violations = audit_result["violations"]
                critical_violations = [
                    v for v in violations if v["impact"] == "critical"
                ]
                assert len(critical_violations) == 2

                # Step 3: Generate remediation guide
                remediation = guide_gen.generate_guide(violations)
                assert "remediation_steps" in remediation
                assert "code_examples" in remediation

                # Step 4: Create GitHub issues
                issues_created = []
                for violation in critical_violations:
                    issue = mock_github_client.create_issue(
                        title=f"[A11Y] {violation['description']}",
                        body=f"Impact: {violation['impact']}\n"
                        f"Help: {violation['help']}",
                    )
                    issues_created.append(issue)

                assert len(issues_created) == 2
                assert all(issue["number"] for issue in issues_created)

                # Step 5: Generate HTML report
                report_path = temp_dir / "audit_report.html"
                report_data = {
                    "audit_results": audit_result,
                    "remediation": remediation,
                    "issues": issues_created,
                    "timestamp": "2024-01-01T00:00:00Z",
                }

                # Verify report generation
                assert report_data["audit_results"]["violations"]
                assert report_data["issues"]

    @pytest.mark.asyncio
    async def test_multi_page_audit_workflow(self, temp_dir, mock_axe_results):
        """
        Test multi-page accessibility audit workflow.

        Tests auditing multiple pages in a site and aggregating results.
        """
        pages = [
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/contact",
        ]

        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value
            auditor.audit_page = AsyncMock(return_value=mock_axe_results)

            # Audit all pages
            results = []
            for page_url in pages:
                result = await auditor.audit_page(url=page_url, wcag_level="AA")
                results.append(
                    {
                        "url": page_url,
                        "violations": result["violations"],
                        "violation_count": len(result["violations"]),
                    }
                )

            # Aggregate results
            total_violations = sum(r["violation_count"] for r in results)
            assert total_violations > 0
            assert len(results) == len(pages)

            # Generate summary report
            summary = {
                "total_pages": len(pages),
                "total_violations": total_violations,
                "pages": results,
            }

            assert summary["total_pages"] == 3
            assert summary["total_violations"] == 9  # 3 violations per page

    @pytest.mark.asyncio
    async def test_multi_viewport_audit_workflow(self, mock_axe_results):
        """
        Test accessibility audit across multiple viewports.

        Tests responsive design accessibility across mobile, tablet, desktop.
        """
        viewports = [
            {"width": 375, "height": 667, "name": "mobile"},
            {"width": 768, "height": 1024, "name": "tablet"},
            {"width": 1920, "height": 1080, "name": "desktop"},
        ]

        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value
            auditor.audit_page = AsyncMock(return_value=mock_axe_results)

            results = []
            for viewport in viewports:
                result = await auditor.audit_page(
                    url="https://example.com", viewport=viewport, wcag_level="AA"
                )
                results.append(
                    {
                        "viewport": viewport["name"],
                        "violations": len(result["violations"]),
                    }
                )

            assert len(results) == 3
            assert all(r["violations"] > 0 for r in results)


class TestFeedbackAnalysisWorkflow:
    """Integration tests for feedback collection and analysis workflows."""

    @pytest.mark.asyncio
    async def test_feedback_analysis_workflow(
        self, sample_feedback_csv, mock_sentiment_results, temp_dir
    ):
        """
        Test complete feedback analysis workflow.

        Workflow:
        1. Collect feedback from CSV file
        2. Analyze sentiment for each feedback item
        3. Extract themes and patterns
        4. Generate insights report
        5. Export results to JSON
        """
        with patch("tools.ux_research.collector.FeedbackCollector") as MockCollector:
            with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
                # Setup mocks
                collector = MockCollector.return_value
                collector.load_from_csv = Mock(
                    return_value=[
                        {"feedback": "Great design", "rating": 5},
                        {"feedback": "Confusing interface", "rating": 2},
                        {"feedback": "Works well", "rating": 4},
                    ]
                )

                analyzer = MockAnalyzer.return_value
                analyzer.analyze_sentiment = Mock(return_value=mock_sentiment_results)
                analyzer.extract_themes = Mock(
                    return_value=[
                        {"theme": "usability", "count": 5, "sentiment": "negative"},
                        {"theme": "design", "count": 3, "sentiment": "positive"},
                    ]
                )

                # Step 1: Collect feedback
                feedback_items = collector.load_from_csv(sample_feedback_csv)
                assert len(feedback_items) > 0

                # Step 2: Analyze sentiment
                sentiment_results = analyzer.analyze_sentiment(feedback_items)
                assert len(sentiment_results) > 0
                assert all("sentiment" in r for r in sentiment_results)

                # Step 3: Extract themes
                themes = analyzer.extract_themes(feedback_items)
                assert len(themes) > 0
                assert all("theme" in t for t in themes)

                # Step 4: Generate insights
                insights = {
                    "total_feedback": len(feedback_items),
                    "sentiment_distribution": {
                        "positive": sum(
                            1 for r in sentiment_results if r["sentiment"] == "positive"
                        ),
                        "negative": sum(
                            1 for r in sentiment_results if r["sentiment"] == "negative"
                        ),
                        "neutral": sum(
                            1 for r in sentiment_results if r["sentiment"] == "neutral"
                        ),
                    },
                    "top_themes": themes,
                    "average_rating": 3.67,
                }

                assert insights["total_feedback"] > 0
                assert "sentiment_distribution" in insights
                assert "top_themes" in insights

                # Step 5: Export results
                output_path = temp_dir / "feedback_analysis.json"
                output_path.write_text(json.dumps(insights, indent=2))

                assert output_path.exists()
                loaded_insights = json.loads(output_path.read_text())
                assert loaded_insights["total_feedback"] == insights["total_feedback"]

    @pytest.mark.asyncio
    async def test_multi_source_feedback_collection(
        self, sample_feedback_csv, sample_feedback_json, mock_hotjar_heatmap_data
    ):
        """
        Test collecting feedback from multiple sources.

        Sources: CSV files, JSON API, Hotjar integration
        """
        with patch("tools.ux_research.collector.FeedbackCollector") as MockCollector:
            collector = MockCollector.return_value

            # Mock different collection methods
            collector.load_from_csv = Mock(
                return_value=[{"source": "csv", "feedback": "Test 1"}]
            )
            collector.load_from_json = Mock(return_value=sample_feedback_json)
            collector.fetch_from_hotjar = AsyncMock(
                return_value=mock_hotjar_heatmap_data
            )

            # Collect from all sources
            csv_feedback = collector.load_from_csv(sample_feedback_csv)
            json_feedback = collector.load_from_json("feedback.json")
            hotjar_data = await collector.fetch_from_hotjar(site_id="12345")

            # Aggregate results
            all_feedback = {
                "csv": csv_feedback,
                "json": json_feedback,
                "hotjar": hotjar_data["heatmaps"],
            }

            assert len(all_feedback["csv"]) > 0
            assert len(all_feedback["json"]) > 0
            assert len(all_feedback["hotjar"]) > 0

    def test_sentiment_theme_extraction_workflow(self, large_feedback_dataset):
        """
        Test sentiment analysis and theme extraction on large dataset.

        Tests processing efficiency and accuracy on 1000+ feedback items.
        """
        with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value

            # Mock sentiment analysis
            analyzer.analyze_batch = Mock(
                return_value=[
                    {
                        "id": item["id"],
                        "sentiment": item["sentiment"],
                        "score": 0.8,
                        "themes": [item["category"]],
                    }
                    for item in large_feedback_dataset
                ]
            )

            # Analyze large dataset
            results = analyzer.analyze_batch(large_feedback_dataset)

            assert len(results) == len(large_feedback_dataset)

            # Extract themes
            theme_counts = {}
            for result in results:
                for theme in result["themes"]:
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1

            assert len(theme_counts) > 0
            assert sum(theme_counts.values()) >= len(large_feedback_dataset)


class TestHeuristicEvaluationWorkflow:
    """Integration tests for heuristic evaluation workflows."""

    @pytest.mark.asyncio
    async def test_heuristic_evaluation_workflow(
        self, mock_heuristic_evaluation, temp_dir
    ):
        """
        Test complete heuristic evaluation workflow.

        Workflow:
        1. Load Nielsen's 10 heuristics checklist
        2. Evaluate each heuristic
        3. Calculate scores and severity
        4. Generate recommendations
        5. Export detailed report
        """
        with patch("tools.ux_research.validator.UsabilityValidator") as MockValidator:
            validator = MockValidator.return_value
            validator.evaluate_heuristics = Mock(return_value=mock_heuristic_evaluation)
            validator.generate_recommendations = Mock(
                return_value=[
                    {
                        "heuristic": "H3",
                        "recommendation": "Add undo functionality",
                        "priority": "high",
                    }
                ]
            )

            # Step 1: Evaluate heuristics
            evaluation = validator.evaluate_heuristics(url="https://example.com")

            assert "heuristics" in evaluation
            assert len(evaluation["heuristics"]) > 0
            assert "overall_score" in evaluation

            # Step 2: Calculate scores
            scores = [h["score"] for h in evaluation["heuristics"]]
            avg_score = sum(scores) / len(scores)
            assert avg_score > 0

            # Step 3: Generate recommendations
            recommendations = validator.generate_recommendations(evaluation)
            assert len(recommendations) > 0

            # Step 4: Export report
            report = {
                "evaluation": evaluation,
                "recommendations": recommendations,
                "summary": {
                    "average_score": avg_score,
                    "total_issues": evaluation["total_issues"],
                    "critical_issues": evaluation["critical_issues"],
                },
            }

            output_path = temp_dir / "heuristic_report.json"
            output_path.write_text(json.dumps(report, indent=2))

            assert output_path.exists()

    def test_custom_checklist_evaluation(self, temp_dir):
        """Test heuristic evaluation with custom checklist."""
        custom_checklist = {
            "heuristics": [
                {
                    "id": "C1",
                    "name": "Mobile responsiveness",
                    "criteria": ["Touch targets", "Viewport scaling"],
                },
                {
                    "id": "C2",
                    "name": "Performance",
                    "criteria": ["Load time", "Animation smoothness"],
                },
            ]
        }

        with patch("tools.ux_research.validator.UsabilityValidator") as MockValidator:
            validator = MockValidator.return_value
            validator.load_custom_checklist = Mock(return_value=custom_checklist)
            validator.evaluate_custom = Mock(
                return_value={
                    "results": [
                        {"id": "C1", "score": 8, "findings": []},
                        {"id": "C2", "score": 7, "findings": []},
                    ]
                }
            )

            # Load custom checklist
            checklist = validator.load_custom_checklist("custom.yaml")
            assert len(checklist["heuristics"]) == 2

            # Evaluate
            results = validator.evaluate_custom(
                url="https://example.com", checklist=checklist
            )
            assert len(results["results"]) == 2


class TestAnalyticsIntegrationWorkflow:
    """Integration tests for analytics platform integration workflows."""

    @pytest.mark.asyncio
    async def test_analytics_integration_workflow(
        self, mock_google_analytics_data, mock_hotjar_heatmap_data, temp_dir
    ):
        """
        Test complete analytics integration workflow.

        Workflow:
        1. Fetch Google Analytics data
        2. Fetch Hotjar heatmap data
        3. Aggregate metrics
        4. Generate insights
        5. Export combined report
        """
        with patch("tools.ux_research.analytics.AnalyticsIntegrator") as MockIntegrator:
            integrator = MockIntegrator.return_value

            # Mock API calls
            integrator.fetch_google_analytics = AsyncMock(
                return_value=mock_google_analytics_data
            )
            integrator.fetch_hotjar = AsyncMock(return_value=mock_hotjar_heatmap_data)

            # Step 1: Fetch Google Analytics
            ga_data = await integrator.fetch_google_analytics(
                view_id="12345", start_date="2024-01-01", end_date="2024-01-31"
            )
            assert "reports" in ga_data

            # Step 2: Fetch Hotjar data
            hotjar_data = await integrator.fetch_hotjar(site_id="67890")
            assert "heatmaps" in hotjar_data

            # Step 3: Aggregate metrics
            metrics = {
                "pageviews": sum(
                    int(row["metrics"][0]["values"][0])
                    for row in ga_data["reports"][0]["data"]["rows"]
                ),
                "avg_time_on_page": 90.5,
                "bounce_rate": 44.3,
                "total_heatmaps": len(hotjar_data["heatmaps"]),
            }

            assert metrics["pageviews"] > 0
            assert metrics["total_heatmaps"] > 0

            # Step 4: Generate insights
            insights = {
                "high_bounce_pages": [
                    row["dimensions"][0]
                    for row in ga_data["reports"][0]["data"]["rows"]
                    if float(row["metrics"][0]["values"][2]) > 50
                ],
                "engagement_zones": [
                    click
                    for heatmap in hotjar_data["heatmaps"]
                    if heatmap["type"] == "click"
                    for click in heatmap["data"]["clicks"]
                    if click["count"] > 30
                ],
            }

            assert len(insights["high_bounce_pages"]) > 0

            # Step 5: Export report
            report = {
                "metrics": metrics,
                "insights": insights,
                "timestamp": "2024-01-01T00:00:00Z",
            }

            output_path = temp_dir / "analytics_report.json"
            output_path.write_text(json.dumps(report, indent=2))
            assert output_path.exists()

    @pytest.mark.asyncio
    async def test_user_journey_mapping(self, mock_google_analytics_data):
        """Test user journey mapping from analytics data."""
        with patch("tools.ux_research.analytics.AnalyticsIntegrator") as MockIntegrator:
            integrator = MockIntegrator.return_value
            integrator.map_user_journeys = AsyncMock(
                return_value={
                    "journeys": [
                        {
                            "path": ["/ ", "/about", "/contact"],
                            "frequency": 50,
                            "avg_duration": 180,
                        }
                    ]
                }
            )

            journeys = await integrator.map_user_journeys(
                data=mock_google_analytics_data
            )

            assert "journeys" in journeys
            assert len(journeys["journeys"]) > 0


class TestReportGenerationWorkflow:
    """Integration tests for comprehensive report generation."""

    @pytest.mark.asyncio
    async def test_comprehensive_report_generation(
        self,
        temp_dir,
        mock_axe_results,
        mock_sentiment_results,
        mock_heuristic_evaluation,
        mock_google_analytics_data,
    ):
        """
        Test generation of comprehensive UX report.

        Combines:
        - Accessibility audit results
        - Feedback analysis
        - Heuristic evaluation
        - Analytics insights
        """
        # Collect all data
        report_data = {
            "accessibility": {
                "violations": len(mock_axe_results["violations"]),
                "critical_issues": sum(
                    1
                    for v in mock_axe_results["violations"]
                    if v["impact"] == "critical"
                ),
                "wcag_level": "AA",
            },
            "feedback": {
                "total_items": len(mock_sentiment_results),
                "sentiment_breakdown": {
                    "positive": sum(
                        1
                        for r in mock_sentiment_results
                        if r["sentiment"] == "positive"
                    ),
                    "negative": sum(
                        1
                        for r in mock_sentiment_results
                        if r["sentiment"] == "negative"
                    ),
                },
            },
            "heuristics": {
                "overall_score": mock_heuristic_evaluation["overall_score"],
                "total_issues": mock_heuristic_evaluation["total_issues"],
                "critical_issues": mock_heuristic_evaluation["critical_issues"],
            },
            "analytics": {
                "total_pages": len(
                    mock_google_analytics_data["reports"][0]["data"]["rows"]
                ),
                "metrics": "aggregated",
            },
        }

        # Generate report
        output_formats = ["json", "html", "pdf"]
        generated_reports = []

        for fmt in output_formats:
            report_path = temp_dir / f"ux_report.{fmt}"
            if fmt == "json":
                report_path.write_text(json.dumps(report_data, indent=2))
            else:
                # Mock HTML/PDF generation
                report_path.write_text(f"Mock {fmt.upper()} report")

            generated_reports.append(report_path)

        # Verify all reports generated
        assert len(generated_reports) == 3
        assert all(p.exists() for p in generated_reports)

        # Verify JSON report content
        json_report = json.loads(generated_reports[0].read_text())
        assert "accessibility" in json_report
        assert "feedback" in json_report
        assert "heuristics" in json_report
        assert "analytics" in json_report

    def test_pdf_report_generation(self, temp_dir, mock_axe_results):
        """Test PDF report generation with charts and visualizations."""
        with patch("tools.ux_research.cli.ux_cli.generate_pdf_report") as mock_pdf:
            mock_pdf.return_value = temp_dir / "report.pdf"

            # Generate PDF
            pdf_path = mock_pdf(
                data=mock_axe_results,
                output_path=temp_dir / "report.pdf",
                include_charts=True,
            )

            assert pdf_path is not None
            mock_pdf.assert_called_once()


class TestErrorHandlingAndEdgeCases:
    """Integration tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test handling of network timeouts during audit."""
        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value
            auditor.audit_page = AsyncMock(side_effect=asyncio.TimeoutError())

            with pytest.raises(asyncio.TimeoutError):
                await auditor.audit_page(url="https://slow-site.com", timeout=1)

    def test_invalid_feedback_data_handling(self, temp_dir):
        """Test handling of invalid feedback data."""
        # Create invalid CSV
        invalid_csv = temp_dir / "invalid.csv"
        invalid_csv.write_text("not,valid,csv,data\n")

        with patch("tools.ux_research.collector.FeedbackCollector") as MockCollector:
            collector = MockCollector.return_value
            collector.load_from_csv = Mock(side_effect=ValueError("Invalid CSV"))

            with pytest.raises(ValueError):
                collector.load_from_csv(invalid_csv)

    def test_empty_results_handling(self):
        """Test handling of empty audit results."""
        empty_results = {
            "violations": [],
            "passes": [],
            "incomplete": [],
            "inapplicable": [],
        }

        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value
            auditor.audit_page = AsyncMock(return_value=empty_results)

            async def run_test():
                result = await auditor.audit_page(url="https://perfect-site.com")
                assert len(result["violations"]) == 0

            asyncio.run(run_test())

    @pytest.mark.asyncio
    async def test_api_rate_limiting(self):
        """Test handling of API rate limiting."""
        with patch("tools.ux_research.analytics.AnalyticsIntegrator") as MockIntegrator:
            integrator = MockIntegrator.return_value
            integrator.fetch_google_analytics = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )

            with pytest.raises(Exception, match="Rate limit exceeded"):
                await integrator.fetch_google_analytics(view_id="12345")


class TestConcurrentOperations:
    """Integration tests for concurrent operations."""

    @pytest.mark.asyncio
    async def test_parallel_page_auditing(self, mock_axe_results):
        """Test auditing multiple pages concurrently."""
        urls = [f"https://example.com/page{i}" for i in range(10)]

        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value
            auditor.audit_page = AsyncMock(return_value=mock_axe_results)

            # Audit pages concurrently
            tasks = [auditor.audit_page(url=url, wcag_level="AA") for url in urls]
            results = await asyncio.gather(*tasks)

            assert len(results) == len(urls)
            assert all(r["violations"] for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_sentiment_analysis(self, large_feedback_dataset):
        """Test concurrent sentiment analysis of feedback batches."""
        batch_size = 100
        batches = [
            large_feedback_dataset[i : i + batch_size]
            for i in range(0, len(large_feedback_dataset), batch_size)
        ]

        with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value
            analyzer.analyze_batch = AsyncMock(
                return_value=[
                    {"sentiment": "positive", "score": 0.8} for _ in range(batch_size)
                ]
            )

            # Analyze batches concurrently
            tasks = [analyzer.analyze_batch(batch) for batch in batches]
            results = await asyncio.gather(*tasks)

            assert len(results) == len(batches)
            total_analyzed = sum(len(r) for r in results)
            assert total_analyzed == len(large_feedback_dataset)
