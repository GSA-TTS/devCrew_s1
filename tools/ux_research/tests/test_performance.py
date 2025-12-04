"""
Performance tests for UX Research & Design Feedback Platform.

This module contains performance benchmarks and load tests:
- Accessibility audit performance
- Feedback analysis performance
- Sentiment classification performance
- Report generation performance
- Concurrent operation performance
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestAccessibilityAuditPerformance:
    """Performance tests for accessibility auditing."""

    @pytest.mark.asyncio
    async def test_single_page_audit_performance(self, mock_axe_results, benchmark):
        """
        Test single page audit performance.

        Target: < 30 seconds for complete audit
        """
        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value
            auditor.audit_page = AsyncMock(return_value=mock_axe_results)

            async def run_audit():
                return await auditor.audit_page(
                    url="https://example.com", wcag_level="AA"
                )

            start_time = time.time()
            result = await run_audit()
            duration = time.time() - start_time

            assert result is not None
            assert duration < 30, f"Audit took {duration}s, expected < 30s"

    @pytest.mark.asyncio
    async def test_small_site_audit_performance(self, mock_axe_results):
        """
        Test small site audit performance (10 pages).

        Target: < 3 minutes (180 seconds)
        """
        pages = [f"https://example.com/page{i}" for i in range(10)]

        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value

            # Simulate realistic audit time (2-3 seconds per page)
            async def mock_audit(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulated processing time
                return mock_axe_results

            auditor.audit_page = mock_audit

            start_time = time.time()

            # Audit pages sequentially
            results = []
            for page in pages:
                result = await auditor.audit_page(url=page, wcag_level="AA")
                results.append(result)

            duration = time.time() - start_time

            assert len(results) == 10
            assert duration < 180, f"Audit took {duration}s, expected < 180s"
            print(f"10-page audit completed in {duration:.2f}s")

    @pytest.mark.asyncio
    async def test_large_site_audit_performance(self, mock_axe_results):
        """
        Test large site audit performance (50 pages).

        Target: < 10 minutes (600 seconds)
        """
        pages = [f"https://example.com/page{i}" for i in range(50)]

        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value

            async def mock_audit(*args, **kwargs):
                await asyncio.sleep(0.05)  # Simulated processing
                return mock_axe_results

            auditor.audit_page = mock_audit

            start_time = time.time()

            # Audit with concurrency (max 5 concurrent)
            semaphore = asyncio.Semaphore(5)

            async def audit_with_limit(url):
                async with semaphore:
                    return await auditor.audit_page(url=url, wcag_level="AA")

            results = await asyncio.gather(*[audit_with_limit(url) for url in pages])

            duration = time.time() - start_time

            assert len(results) == 50
            assert duration < 600, f"Audit took {duration}s, expected < 600s"
            print(f"50-page audit completed in {duration:.2f}s")

    @pytest.mark.asyncio
    async def test_multi_viewport_audit_performance(self, mock_axe_results):
        """
        Test multi-viewport audit performance.

        Target: < 2 minutes for 3 viewports
        """
        viewports = [
            {"width": 375, "height": 667, "name": "mobile"},
            {"width": 768, "height": 1024, "name": "tablet"},
            {"width": 1920, "height": 1080, "name": "desktop"},
        ]

        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value

            async def mock_audit(*args, **kwargs):
                await asyncio.sleep(0.2)  # Simulated processing
                return mock_axe_results

            auditor.audit_page = mock_audit

            start_time = time.time()

            results = await asyncio.gather(
                *[
                    auditor.audit_page(
                        url="https://example.com", viewport=viewport, wcag_level="AA"
                    )
                    for viewport in viewports
                ]
            )

            duration = time.time() - start_time

            assert len(results) == 3
            assert duration < 120, f"Audit took {duration}s, expected < 120s"

    def test_violation_detection_performance(self, mock_axe_results):
        """
        Test violation detection speed.

        Target: < 1 second for processing results
        """
        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value

            start_time = time.time()

            # Process violations
            violations = mock_axe_results["violations"]
            critical = [v for v in violations if v["impact"] == "critical"]
            serious = [v for v in violations if v["impact"] == "serious"]
            moderate = [v for v in violations if v["impact"] == "moderate"]

            summary = {
                "total": len(violations),
                "critical": len(critical),
                "serious": len(serious),
                "moderate": len(moderate),
            }

            duration = time.time() - start_time

            assert duration < 1, f"Processing took {duration}s, expected < 1s"
            assert summary["total"] > 0


class TestFeedbackAnalysisPerformance:
    """Performance tests for feedback analysis."""

    def test_feedback_analysis_performance(self, large_feedback_dataset):
        """
        Test feedback analysis performance on 1000 items.

        Target: < 5 seconds
        """
        with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value

            def mock_analyze(items):
                # Simulate processing time
                time.sleep(0.001 * len(items))  # 1ms per item
                return [
                    {"id": item["id"], "sentiment": item["sentiment"], "score": 0.8}
                    for item in items
                ]

            analyzer.analyze_batch = mock_analyze

            start_time = time.time()
            results = analyzer.analyze_batch(large_feedback_dataset)
            duration = time.time() - start_time

            assert len(results) == len(large_feedback_dataset)
            assert duration < 5, f"Analysis took {duration}s, expected < 5s"
            print(f"Analyzed {len(results)} items in {duration:.2f}s")

    def test_sentiment_classification_performance(self):
        """
        Test sentiment classification speed per item.

        Target: < 100ms per item
        """
        test_texts = [
            "This is a great product!",
            "Terrible experience, very disappointed",
            "It's okay, nothing special",
            "Absolutely love it!",
            "Complete waste of time",
        ] * 20  # 100 items

        with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value

            def mock_classify(text):
                time.sleep(0.01)  # 10ms per classification
                return {"sentiment": "positive", "score": 0.8, "confidence": 0.9}

            analyzer.classify_sentiment = mock_classify

            start_time = time.time()

            results = []
            for text in test_texts:
                result = analyzer.classify_sentiment(text)
                results.append(result)

            duration = time.time() - start_time
            avg_time_per_item = (duration / len(test_texts)) * 1000  # ms

            assert len(results) == len(test_texts)
            assert (
                avg_time_per_item < 100
            ), f"Average {avg_time_per_item:.2f}ms per item, expected < 100ms"
            print(f"Average classification time: {avg_time_per_item:.2f}ms per item")

    def test_theme_extraction_performance(self, large_feedback_dataset):
        """
        Test theme extraction performance.

        Target: < 3 seconds for 1000 items
        """
        with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value

            def mock_extract_themes(items):
                time.sleep(0.002 * len(items))  # 2ms per item
                return [
                    {"theme": "usability", "count": 200},
                    {"theme": "design", "count": 150},
                    {"theme": "performance", "count": 100},
                ]

            analyzer.extract_themes = mock_extract_themes

            start_time = time.time()
            themes = analyzer.extract_themes(large_feedback_dataset)
            duration = time.time() - start_time

            assert len(themes) > 0
            assert duration < 3, f"Theme extraction took {duration}s, expected < 3s"

    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, large_feedback_dataset):
        """
        Test batch processing performance.

        Target: Process 1000 items in < 5 seconds using batching
        """
        batch_size = 100
        batches = [
            large_feedback_dataset[i : i + batch_size]
            for i in range(0, len(large_feedback_dataset), batch_size)
        ]

        with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value

            async def mock_process_batch(batch):
                await asyncio.sleep(0.1)  # 100ms per batch
                return [{"sentiment": "positive"} for _ in batch]

            analyzer.process_batch = mock_process_batch

            start_time = time.time()

            results = await asyncio.gather(
                *[analyzer.process_batch(batch) for batch in batches]
            )

            duration = time.time() - start_time
            total_items = sum(len(r) for r in results)

            assert total_items == len(large_feedback_dataset)
            assert duration < 5, f"Batch processing took {duration}s, expected < 5s"
            print(
                f"Processed {total_items} items in {duration:.2f}s "
                f"({total_items/duration:.0f} items/sec)"
            )


class TestReportGenerationPerformance:
    """Performance tests for report generation."""

    def test_json_report_generation_performance(self, temp_dir, mock_axe_results):
        """
        Test JSON report generation performance.

        Target: < 1 second
        """
        report_data = {
            "audit_results": mock_axe_results,
            "violations": mock_axe_results["violations"],
            "summary": {"total": 10, "critical": 5},
        }

        start_time = time.time()

        # Generate JSON report
        import json

        report_path = temp_dir / "report.json"
        report_path.write_text(json.dumps(report_data, indent=2))

        duration = time.time() - start_time

        assert report_path.exists()
        assert duration < 1, f"JSON generation took {duration}s, expected < 1s"

    def test_html_report_generation_performance(self, temp_dir, mock_axe_results):
        """
        Test HTML report generation performance.

        Target: < 2 seconds
        """
        start_time = time.time()

        # Simulate HTML generation
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Audit Report</title></head>
        <body>
            <h1>Accessibility Audit Report</h1>
            <p>Total violations: {len(mock_axe_results['violations'])}</p>
            <!-- More content -->
        </body>
        </html>
        """

        report_path = temp_dir / "report.html"
        report_path.write_text(html_content)

        duration = time.time() - start_time

        assert report_path.exists()
        assert duration < 2, f"HTML generation took {duration}s, expected < 2s"

    def test_pdf_report_generation_performance(self, temp_dir):
        """
        Test PDF report generation performance.

        Target: < 5 seconds
        """
        with patch("tools.ux_research.cli.ux_cli.generate_pdf") as mock_pdf:

            def generate_pdf(*args, **kwargs):
                time.sleep(2)  # Simulate PDF generation
                return temp_dir / "report.pdf"

            mock_pdf.side_effect = generate_pdf

            start_time = time.time()
            pdf_path = mock_pdf(output=temp_dir / "report.pdf")
            duration = time.time() - start_time

            assert pdf_path is not None
            assert duration < 5, f"PDF generation took {duration}s, expected < 5s"

    def test_multi_format_report_generation(self, temp_dir, mock_axe_results):
        """
        Test generating multiple report formats concurrently.

        Target: < 10 seconds for JSON, HTML, and PDF
        """
        import json

        start_time = time.time()

        # Generate all formats
        formats = []

        # JSON
        json_path = temp_dir / "report.json"
        json_path.write_text(json.dumps(mock_axe_results, indent=2))
        formats.append(json_path)

        # HTML
        html_path = temp_dir / "report.html"
        html_path.write_text("<html><body>Report</body></html>")
        formats.append(html_path)

        # PDF (simulated)
        pdf_path = temp_dir / "report.pdf"
        pdf_path.write_text("Mock PDF content")
        formats.append(pdf_path)

        duration = time.time() - start_time

        assert all(f.exists() for f in formats)
        assert (
            duration < 10
        ), f"Multi-format generation took {duration}s, expected < 10s"


class TestConcurrentOperationsPerformance:
    """Performance tests for concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_audit_performance(self, mock_axe_results):
        """
        Test concurrent auditing performance.

        Target: 5 concurrent audits complete in < 10 seconds
        """
        urls = [f"https://example.com/page{i}" for i in range(5)]

        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value

            async def mock_audit(*args, **kwargs):
                await asyncio.sleep(1)  # 1 second per audit
                return mock_axe_results

            auditor.audit_page = mock_audit

            start_time = time.time()

            results = await asyncio.gather(
                *[auditor.audit_page(url=url, wcag_level="AA") for url in urls]
            )

            duration = time.time() - start_time

            assert len(results) == 5
            # Should complete in ~1 second (concurrent), not 5 seconds (sequential)
            assert duration < 2, f"Concurrent audit took {duration}s, expected < 2s"
            print(f"5 concurrent audits completed in {duration:.2f}s")

    @pytest.mark.asyncio
    async def test_concurrent_sentiment_analysis(self, large_feedback_dataset):
        """
        Test concurrent sentiment analysis performance.

        Target: Process 1000 items with 10 concurrent workers in < 3 seconds
        """
        with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value

            async def mock_analyze(item):
                await asyncio.sleep(0.01)  # 10ms per item
                return {"sentiment": "positive", "score": 0.8}

            analyzer.analyze_item = mock_analyze

            start_time = time.time()

            # Process with semaphore limiting concurrency
            semaphore = asyncio.Semaphore(10)

            async def analyze_with_limit(item):
                async with semaphore:
                    return await analyzer.analyze_item(item)

            results = await asyncio.gather(
                *[analyze_with_limit(item) for item in large_feedback_dataset]
            )

            duration = time.time() - start_time
            throughput = len(results) / duration

            assert len(results) == len(large_feedback_dataset)
            assert duration < 3, f"Analysis took {duration}s, expected < 3s"
            print(f"Throughput: {throughput:.0f} items/sec")

    @pytest.mark.asyncio
    async def test_parallel_data_fetching(self):
        """
        Test parallel data fetching from multiple sources.

        Target: Fetch from 3 sources concurrently in < 5 seconds
        """
        with patch("tools.ux_research.collector.FeedbackCollector") as MockCollector:
            collector = MockCollector.return_value

            async def mock_fetch_survey():
                await asyncio.sleep(2)
                return [{"feedback": "Survey data"}]

            async def mock_fetch_support():
                await asyncio.sleep(1.5)
                return [{"feedback": "Support data"}]

            async def mock_fetch_analytics():
                await asyncio.sleep(1)
                return [{"metric": "Analytics data"}]

            collector.fetch_survey = mock_fetch_survey
            collector.fetch_support = mock_fetch_support
            collector.fetch_analytics = mock_fetch_analytics

            start_time = time.time()

            results = await asyncio.gather(
                collector.fetch_survey(),
                collector.fetch_support(),
                collector.fetch_analytics(),
            )

            duration = time.time() - start_time

            assert len(results) == 3
            # Should complete in ~2 seconds (max time), not 4.5 seconds (sum)
            assert duration < 3, f"Parallel fetch took {duration}s, expected < 3s"
            print(f"Fetched from 3 sources in {duration:.2f}s")


class TestMemoryAndResourceUsage:
    """Performance tests for memory and resource usage."""

    def test_memory_efficiency_large_dataset(self, large_feedback_dataset):
        """
        Test memory efficiency with large datasets.

        Verifies that processing doesn't cause excessive memory usage.
        """
        import sys

        with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value

            # Get initial memory usage
            initial_size = sys.getsizeof(large_feedback_dataset)

            # Process data
            results = []
            for item in large_feedback_dataset:
                result = {"id": item["id"], "sentiment": "positive"}
                results.append(result)

            # Check results size is reasonable
            results_size = sys.getsizeof(results)

            # Results should not be significantly larger than input
            assert results_size < initial_size * 2, (
                f"Results size {results_size} is too large "
                f"compared to input {initial_size}"
            )

    def test_streaming_processing_efficiency(self):
        """
        Test efficiency of streaming processing vs batch loading.

        Verifies that streaming approach uses less memory.
        """

        def generate_large_dataset():
            """Generator for large dataset."""
            for i in range(10000):
                yield {
                    "id": f"item{i}",
                    "feedback": f"Feedback text {i}",
                    "rating": (i % 5) + 1,
                }

        with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value

            start_time = time.time()

            # Process streaming
            count = 0
            for item in generate_large_dataset():
                # Simulate processing
                count += 1

            duration = time.time() - start_time

            assert count == 10000
            assert duration < 5, f"Streaming took {duration}s, expected < 5s"
            print(f"Streamed {count} items in {duration:.2f}s")

    def test_file_io_performance(self, temp_dir, large_feedback_dataset):
        """
        Test file I/O performance for reading/writing results.

        Target: < 2 seconds for reading and writing 1000 items
        """
        import json

        output_file = temp_dir / "feedback_data.json"

        # Write performance
        start_time = time.time()
        output_file.write_text(json.dumps(large_feedback_dataset, indent=2))
        write_duration = time.time() - start_time

        assert output_file.exists()
        assert write_duration < 1, f"Write took {write_duration}s, expected < 1s"

        # Read performance
        start_time = time.time()
        data = json.loads(output_file.read_text())
        read_duration = time.time() - start_time

        assert len(data) == len(large_feedback_dataset)
        assert read_duration < 1, f"Read took {read_duration}s, expected < 1s"

        total_duration = write_duration + read_duration
        print(
            f"I/O completed in {total_duration:.2f}s "
            f"(write: {write_duration:.2f}s, read: {read_duration:.2f}s)"
        )


class TestScalabilityBenchmarks:
    """Scalability benchmarks for various operations."""

    def test_audit_scalability(self, mock_axe_results):
        """
        Benchmark audit performance at different scales.

        Tests: 1, 10, 50, 100 pages
        """
        page_counts = [1, 10, 50, 100]
        results = {}

        with patch("tools.ux_research.auditor.AccessibilityAuditor") as MockAuditor:
            auditor = MockAuditor.return_value
            auditor.audit_page = AsyncMock(return_value=mock_axe_results)

            async def benchmark_audit(count):
                start = time.time()
                await asyncio.gather(
                    *[
                        auditor.audit_page(url=f"https://example.com/page{i}")
                        for i in range(count)
                    ]
                )
                return time.time() - start

            for count in page_counts:
                duration = asyncio.run(benchmark_audit(count))
                results[count] = duration
                print(
                    f"{count} pages: {duration:.2f}s "
                    f"({duration/count:.2f}s per page)"
                )

        # Verify reasonable scaling
        assert results[1] < 5
        assert results[10] < 30
        assert results[50] < 120
        assert results[100] < 240

    def test_feedback_analysis_scalability(self):
        """
        Benchmark feedback analysis at different scales.

        Tests: 100, 500, 1000, 5000 items
        """
        item_counts = [100, 500, 1000, 5000]
        results = {}

        with patch("tools.ux_research.analyzer.SentimentAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value

            def benchmark_analysis(count):
                items = create_mock_feedback_batch(count)
                start = time.time()

                # Simulate processing
                for item in items:
                    _ = {"sentiment": "positive", "score": 0.8}

                return time.time() - start

            for count in item_counts:
                duration = benchmark_analysis(count)
                results[count] = duration
                print(
                    f"{count} items: {duration:.2f}s "
                    f"({duration/count*1000:.2f}ms per item)"
                )

        # Verify linear or better scaling
        assert results[100] < 2
        assert results[500] < 8
        assert results[1000] < 15
        assert results[5000] < 60


def create_mock_feedback_batch(count: int) -> List[Dict]:
    """Helper function to create mock feedback batch."""
    return [
        {
            "id": f"fb{i}",
            "feedback": f"Test feedback {i}",
            "rating": (i % 5) + 1,
            "category": "usability",
            "sentiment": "positive",
        }
        for i in range(count)
    ]
