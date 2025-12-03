"""
Example usage of Sprint Analytics Engine.

This script demonstrates how to use the SprintAnalytics class for
comprehensive sprint reporting and analysis.
"""

from datetime import datetime, timedelta
from pathlib import Path

from sprint_analytics import (IssueData, SprintAnalytics, SprintConfig,
                              SprintData)


def create_sample_data():
    """Create sample sprint data for demonstration."""
    sprints = []
    base_date = datetime(2024, 1, 1)

    for i in range(10):
        sprint_start = base_date + timedelta(weeks=i * 2)
        sprint_end = sprint_start + timedelta(days=13)
        sprint_id = f"SPRINT-{i+1:03d}"
        sprint_name = f"Sprint {i+1}"

        # Create sample issues
        issues = []
        for j in range(15):
            issue = IssueData(
                issue_id=f"{sprint_id}-{j+1}",
                issue_type="story" if j % 3 != 0 else "bug",
                status="done" if j < 12 else "in_progress",
                story_points=float((j % 5) + 1),
                created_date=sprint_start + timedelta(days=j % 7),
                completed_date=(
                    sprint_start + timedelta(days=(j % 7) + 3) if j < 12 else None
                ),
                sprint_id=sprint_id,
                sprint_name=sprint_name,
                assignee=f"dev-{j % 4 + 1}",
                labels=["frontend" if j % 2 == 0 else "backend"],
                priority="high" if j % 5 == 0 else "medium",
            )
            issues.append(issue)

        # Calculate committed and completed points
        committed_points = sum(issue.story_points or 0 for issue in issues)
        completed_points = sum(
            issue.story_points or 0
            for issue in issues
            if issue.completed_date is not None
        )

        sprint = SprintData(
            sprint_id=sprint_id,
            sprint_name=sprint_name,
            start_date=sprint_start,
            end_date=sprint_end,
            committed_points=committed_points,
            completed_points=completed_points,
            team_capacity=45.0,
            issues=issues,
        )
        sprints.append(sprint)

    return sprints


def main():
    """Demonstrate Sprint Analytics usage."""
    print("Sprint Analytics Engine - Example Usage")
    print("=" * 60)

    # Configure analytics
    config = SprintConfig(
        output_dir=Path("example_reports"),
        chart_format="png",
        include_weekends=False,
        confidence_level=0.95,
        velocity_window=5,
        dpi=300,
    )

    # Initialize analytics engine
    analytics = SprintAnalytics(config)

    # Load sample data
    print("\n1. Loading sample sprint data...")
    sprints = create_sample_data()
    for sprint in sprints:
        analytics.add_sprint(sprint)
    print(f"   Loaded {len(sprints)} sprints")

    # Calculate velocity metrics
    print("\n2. Calculating velocity metrics...")
    velocity = analytics.calculate_velocity()
    print(f"   Mean Velocity: {velocity.mean_velocity:.1f} points")
    print(f"   Median Velocity: {velocity.median_velocity:.1f} points")
    print(f"   Std Dev: {velocity.std_dev:.1f}")
    print(f"   Trend: {velocity.velocity_trend}")
    print(f"   Trend %: {velocity.trend_percentage:.1f}%")

    # Calculate cycle time metrics
    print("\n3. Calculating cycle time metrics...")
    cycle_time = analytics.calculate_cycle_time()
    print(f"   Avg Cycle Time: {cycle_time.avg_cycle_time_days:.1f} days")
    print(f"   Median Cycle Time: {cycle_time.median_cycle_time_days:.1f} days")
    print(f"   P90 Cycle Time: {cycle_time.p90_cycle_time:.1f} days")
    print(f"   Issues Analyzed: {cycle_time.issues_analyzed}")

    # Calculate predictability metrics
    print("\n4. Calculating predictability metrics...")
    predictability = analytics.calculate_predictability()
    print(f"   Commitment Accuracy: {predictability.commitment_accuracy:.1f}%")
    print(f"   Consistency Score: {predictability.consistency_score:.1f}")
    print(f"   Prediction Confidence: " f"{predictability.prediction_confidence:.2f}")
    print(f"   Risk Level: {predictability.risk_level}")

    # Forecast release
    print("\n5. Forecasting release completion...")
    target_points = 150.0
    forecast = analytics.forecast_release(target_points)
    print(f"   Target Points: {forecast.target_points}")
    print(f"   Estimated Sprints: {forecast.estimated_sprints}")
    print(
        f"   Estimated Completion: "
        f"{forecast.estimated_completion_date.strftime('%Y-%m-%d')}"
    )
    print(
        f"   Confidence Interval: "
        f"{forecast.confidence_interval_low}-{forecast.confidence_interval_high} "
        f"sprints"
    )
    print(f"   Completion Probability: {forecast.completion_probability:.1%}")

    # Generate charts
    print("\n6. Generating charts...")

    # Burndown chart for latest sprint
    latest_sprint = sprints[-1]
    burndown_path = analytics.generate_burndown_chart(latest_sprint.sprint_id)
    print(f"   Burndown chart: {burndown_path}")

    # Burnup chart
    burnup_path = analytics.generate_burnup_chart(latest_sprint.sprint_id)
    print(f"   Burnup chart: {burnup_path}")

    # Velocity chart
    velocity_path = analytics.generate_velocity_chart()
    print(f"   Velocity chart: {velocity_path}")

    # Cycle time chart
    cycle_time_path = analytics.generate_cycle_time_chart()
    print(f"   Cycle time chart: {cycle_time_path}")

    # Export data
    print("\n7. Exporting data...")
    csv_path = analytics.export_to_csv()
    print(f"   CSV export: {csv_path}")

    json_path = analytics.export_to_json()
    print(f"   JSON export: {json_path}")

    # Generate comprehensive report
    print("\n8. Generating comprehensive report...")
    report = analytics.generate_comprehensive_report()
    print(f"   Total Sprints: {report['summary']['total_sprints']}")
    print(
        f"   Overall Completion Rate: "
        f"{report['summary']['overall_completion_rate']:.1f}%"
    )
    print(f"   Recommendations:")
    for rec in report["recommendations"]:
        print(f"     - {rec}")

    print("\n" + "=" * 60)
    print("Sprint Analytics Example Complete!")
    print(f"All reports saved to: {config.output_dir}")


if __name__ == "__main__":
    main()
