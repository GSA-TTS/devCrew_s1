"""
Issue #41: Data Pipeline Module
Implements Airflow DAGs for customer data ETL and feedback processing.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator


# Default DAG arguments
default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "email": ["data-team@example.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}


# ETL Functions
def extract_customer_data(**context) -> List[Dict[str, Any]]:
    """
    Extract customer data from source database.

    Args:
        context: Airflow context

    Returns:
        List of customer records
    """
    # Get PostgreSQL hook
    pg_hook = PostgresHook(postgres_conn_id="customer_db")

    # Extract data
    sql = """
        SELECT
            customer_id,
            email,
            full_name,
            phone,
            company,
            address,
            metadata,
            is_active,
            created_at,
            updated_at
        FROM customers
        WHERE deleted_at IS NULL
        AND updated_at >= NOW() - INTERVAL '1 day'
    """

    records = pg_hook.get_records(sql)

    # Convert to dict
    customers = []
    for record in records:
        customers.append(
            {
                "customer_id": record[0],
                "email": record[1],
                "full_name": record[2],
                "phone": record[3],
                "company": record[4],
                "address": record[5],
                "metadata": record[6],
                "is_active": record[7],
                "created_at": record[8],
                "updated_at": record[9],
            }
        )

    # Push to XCom
    context["ti"].xcom_push(key="customer_data", value=customers)

    return customers


def transform_customer_data(**context) -> List[Dict[str, Any]]:
    """
    Transform customer data.

    Args:
        context: Airflow context

    Returns:
        Transformed customer records
    """
    # Pull from XCom
    customers = context["ti"].xcom_pull(
        key="customer_data", task_ids="extract_customer_data"
    )

    transformed_customers = []

    for customer in customers:
        # Clean and normalize data
        transformed = {
            "customer_id": customer["customer_id"],
            "email": customer["email"].lower().strip(),
            "full_name": customer["full_name"].strip() if customer["full_name"] else None,  # noqa: E501
            "phone": customer["phone"],
            "company": customer["company"],
            "address": customer["address"],
            "metadata": customer["metadata"],
            "is_active": customer["is_active"],
            "created_at": customer["created_at"],
            "updated_at": customer["updated_at"],
        }

        # Add derived fields
        transformed["email_domain"] = customer["email"].split("@")[1]
        transformed["has_phone"] = customer["phone"] is not None
        transformed["has_company"] = customer["company"] is not None

        transformed_customers.append(transformed)

    # Push to XCom
    context["ti"].xcom_push(key="transformed_data", value=transformed_customers)

    return transformed_customers


def load_customer_data(**context) -> int:
    """
    Load customer data to analytics database.

    Args:
        context: Airflow context

    Returns:
        Number of records loaded
    """
    # Pull from XCom
    customers = context["ti"].xcom_pull(
        key="transformed_data", task_ids="transform_customer_data"
    )

    # Get PostgreSQL hook for analytics database
    pg_hook = PostgresHook(postgres_conn_id="analytics_db")

    # Prepare batch insert
    insert_sql = """
        INSERT INTO customer_analytics (
            customer_id, email, email_domain, full_name,
            phone, has_phone, company, has_company,
            address, metadata, is_active,
            created_at, updated_at, loaded_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        ON CONFLICT (customer_id)
        DO UPDATE SET
            email = EXCLUDED.email,
            email_domain = EXCLUDED.email_domain,
            full_name = EXCLUDED.full_name,
            phone = EXCLUDED.phone,
            has_phone = EXCLUDED.has_phone,
            company = EXCLUDED.company,
            has_company = EXCLUDED.has_company,
            address = EXCLUDED.address,
            metadata = EXCLUDED.metadata,
            is_active = EXCLUDED.is_active,
            updated_at = EXCLUDED.updated_at,
            loaded_at = NOW()
    """

    # Execute batch insert
    records = [
        (
            c["customer_id"],
            c["email"],
            c["email_domain"],
            c["full_name"],
            c["phone"],
            c["has_phone"],
            c["company"],
            c["has_company"],
            c["address"],
            c["metadata"],
            c["is_active"],
            c["created_at"],
            c["updated_at"],
        )
        for c in customers
    ]

    pg_hook.insert_rows(
        table="customer_analytics",
        rows=records,
        target_fields=[
            "customer_id",
            "email",
            "email_domain",
            "full_name",
            "phone",
            "has_phone",
            "company",
            "has_company",
            "address",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ],
    )

    return len(records)


def validate_data_quality(**context) -> Dict[str, Any]:
    """
    Validate data quality.

    Args:
        context: Airflow context

    Returns:
        Validation results
    """
    # Pull from XCom
    customers = context["ti"].xcom_pull(
        key="transformed_data", task_ids="transform_customer_data"
    )

    validation_results = {
        "total_records": len(customers),
        "valid_emails": 0,
        "valid_phones": 0,
        "active_customers": 0,
        "errors": [],
    }

    for customer in customers:
        # Validate email
        if "@" in customer["email"] and "." in customer["email"]:
            validation_results["valid_emails"] += 1
        else:
            validation_results["errors"].append(
                f"Invalid email: {customer['customer_id']}"
            )

        # Count valid phones
        if customer["has_phone"]:
            validation_results["valid_phones"] += 1

        # Count active customers
        if customer["is_active"]:
            validation_results["active_customers"] += 1

    # Calculate quality score
    validation_results["quality_score"] = (
        validation_results["valid_emails"] / validation_results["total_records"] * 100
    )

    return validation_results


# Feedback ETL Functions
def extract_feedback_data(**context) -> List[Dict[str, Any]]:
    """
    Extract feedback data from source.

    Args:
        context: Airflow context

    Returns:
        List of feedback records
    """
    # Get PostgreSQL hook
    pg_hook = PostgresHook(postgres_conn_id="customer_db")

    # Extract feedback data
    sql = """
        SELECT
            feedback_id,
            customer_id,
            feedback_type,
            subject,
            content,
            source,
            rating,
            status,
            created_at
        FROM feedback
        WHERE created_at >= NOW() - INTERVAL '1 day'
    """

    records = pg_hook.get_records(sql)

    feedbacks = []
    for record in records:
        feedbacks.append(
            {
                "feedback_id": record[0],
                "customer_id": record[1],
                "feedback_type": record[2],
                "subject": record[3],
                "content": record[4],
                "source": record[5],
                "rating": record[6],
                "status": record[7],
                "created_at": record[8],
            }
        )

    context["ti"].xcom_push(key="feedback_data", value=feedbacks)

    return feedbacks


def process_feedback_sentiment(**context) -> List[Dict[str, Any]]:
    """
    Process feedback sentiment analysis.

    Args:
        context: Airflow context

    Returns:
        Feedback with sentiment scores
    """
    # Pull from XCom
    feedbacks = context["ti"].xcom_pull(
        key="feedback_data", task_ids="extract_feedback_data"
    )

    processed_feedbacks = []

    for feedback in feedbacks:
        # Simple sentiment analysis based on keywords
        content_lower = feedback["content"].lower()

        positive_keywords = ["great", "excellent", "love", "good", "amazing", "happy"]
        negative_keywords = ["bad", "terrible", "hate", "poor", "awful", "unhappy"]

        positive_count = sum(
            1 for keyword in positive_keywords if keyword in content_lower
        )
        negative_count = sum(
            1 for keyword in negative_keywords if keyword in content_lower
        )

        # Calculate sentiment score
        if positive_count > negative_count:
            sentiment = "positive"
            sentiment_score = 0.7 + (positive_count * 0.1)
        elif negative_count > positive_count:
            sentiment = "negative"
            sentiment_score = 0.3 - (negative_count * 0.1)
        else:
            sentiment = "neutral"
            sentiment_score = 0.5

        # Clamp sentiment score
        sentiment_score = max(0.0, min(1.0, sentiment_score))

        processed = feedback.copy()
        processed["sentiment"] = sentiment
        processed["sentiment_score"] = sentiment_score

        processed_feedbacks.append(processed)

    context["ti"].xcom_push(key="processed_feedback", value=processed_feedbacks)

    return processed_feedbacks


# DAG: Customer Data ETL
customer_etl_dag = DAG(
    "customer_data_etl",
    default_args=default_args,
    description="Extract, transform, and load customer data",
    schedule_interval="0 2 * * *",  # Daily at 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["customer", "etl", "daily"],
)

with customer_etl_dag:
    extract_task = PythonOperator(
        task_id="extract_customer_data",
        python_callable=extract_customer_data,
        provide_context=True,
    )

    transform_task = PythonOperator(
        task_id="transform_customer_data",
        python_callable=transform_customer_data,
        provide_context=True,
    )

    validate_task = PythonOperator(
        task_id="validate_data_quality",
        python_callable=validate_data_quality,
        provide_context=True,
    )

    load_task = PythonOperator(
        task_id="load_customer_data",
        python_callable=load_customer_data,
        provide_context=True,
    )

    extract_task >> transform_task >> validate_task >> load_task


# DAG: Feedback Processing
feedback_processing_dag = DAG(
    "feedback_processing",
    default_args=default_args,
    description="Process and analyze customer feedback",
    schedule_interval="0 */6 * * *",  # Every 6 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["feedback", "processing", "sentiment"],
)

with feedback_processing_dag:
    extract_feedback_task = PythonOperator(
        task_id="extract_feedback_data",
        python_callable=extract_feedback_data,
        provide_context=True,
    )

    process_sentiment_task = PythonOperator(
        task_id="process_feedback_sentiment",
        python_callable=process_feedback_sentiment,
        provide_context=True,
    )

    extract_feedback_task >> process_sentiment_task


# DAG: Data Enrichment
data_enrichment_dag = DAG(
    "customer_data_enrichment",
    default_args=default_args,
    description="Enrich customer data with additional attributes",
    schedule_interval="0 3 * * *",  # Daily at 3 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["customer", "enrichment", "daily"],
)


def enrich_customer_data(**context) -> int:
    """
    Enrich customer data with additional attributes.

    Args:
        context: Airflow context

    Returns:
        Number of enriched records
    """
    pg_hook = PostgresHook(postgres_conn_id="customer_db")

    # Enrich with customer tenure
    sql = """
        UPDATE customers
        SET metadata = jsonb_set(
            COALESCE(metadata, '{}'::jsonb),
            '{tenure_days}',
            to_jsonb(EXTRACT(DAY FROM NOW() - created_at)::int)
        )
        WHERE deleted_at IS NULL
    """

    pg_hook.run(sql)

    return 1


with data_enrichment_dag:
    enrich_task = PythonOperator(
        task_id="enrich_customer_data",
        python_callable=enrich_customer_data,
        provide_context=True,
    )


# DAG: Data Quality Monitoring
data_quality_dag = DAG(
    "data_quality_monitoring",
    default_args=default_args,
    description="Monitor data quality metrics",
    schedule_interval="0 */4 * * *",  # Every 4 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["quality", "monitoring"],
)


def check_data_quality_metrics(**context) -> Dict[str, Any]:
    """
    Check data quality metrics.

    Args:
        context: Airflow context

    Returns:
        Quality metrics
    """
    pg_hook = PostgresHook(postgres_conn_id="customer_db")

    metrics = {}

    # Check for duplicate emails
    duplicate_sql = """
        SELECT COUNT(*) as duplicates
        FROM (
            SELECT email, COUNT(*) as cnt
            FROM customers
            WHERE deleted_at IS NULL
            GROUP BY email
            HAVING COUNT(*) > 1
        ) dups
    """
    result = pg_hook.get_first(duplicate_sql)
    metrics["duplicate_emails"] = result[0]

    # Check for missing data
    missing_sql = """
        SELECT
            COUNT(CASE WHEN full_name IS NULL THEN 1 END) as missing_names,
            COUNT(CASE WHEN phone IS NULL THEN 1 END) as missing_phones,
            COUNT(CASE WHEN company IS NULL THEN 1 END) as missing_companies
        FROM customers
        WHERE deleted_at IS NULL
    """
    result = pg_hook.get_first(missing_sql)
    metrics["missing_names"] = result[0]
    metrics["missing_phones"] = result[1]
    metrics["missing_companies"] = result[2]

    # Check for inactive customers
    inactive_sql = """
        SELECT COUNT(*)
        FROM customers
        WHERE deleted_at IS NULL
        AND is_active = false
    """
    result = pg_hook.get_first(inactive_sql)
    metrics["inactive_customers"] = result[0]

    return metrics


with data_quality_dag:
    quality_check_task = PythonOperator(
        task_id="check_data_quality_metrics",
        python_callable=check_data_quality_metrics,
        provide_context=True,
    )
