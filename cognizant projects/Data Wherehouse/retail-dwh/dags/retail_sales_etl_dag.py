"""Airflow DAG: retail_sales_etl (v2)

Full end-to-end orchestration:

    wait_for_source_file
            |
    +-------+-------+
    |               |
  sales           returns
  TaskGroup       TaskGroup
    |               |
    +-------+-------+
            |
     load_dimensions_scd2
            |
     fact_group (fact_sales + fact_returns)
            |
     data_quality_checks
            |
     refresh_marts (fan-out: sales_daily, customer_360, inventory)
            |
     mark_run_success

Features shown:
- FileSensor (waits for source CSV to arrive)
- TaskGroups (visual grouping in the UI)
- Fan-out / fan-in dependencies
- Branching (skip returns if returns.jsonl not present)
- Task-level retries with exponential backoff
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

from etl.extract         import extract
from etl.load_staging    import load_staging
from etl.load_dim_scd2   import load_dim_customer, load_dim_product, load_dim_store
from etl.load_fact       import load_fact_sales
from etl.generate_returns import generate_returns
from etl.load_returns    import load_returns_staging, load_fact_returns
from etl.data_quality    import run_checks
from etl.refresh_marts   import refresh_sales_daily, refresh_customer_360, refresh_inventory


RAW_DIR = Path(os.getenv("RAW_DIR", "/opt/airflow/data/raw"))

default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["alerts@example.com"],
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}


def _batch_id(**ctx) -> str:
    return ctx["dag_run"].run_id.replace(":", "_")


# ----------------------------- task callables ------------------------

def task_extract_sales(**ctx):
    p = extract("Superstore.csv", _batch_id(**ctx))
    ctx["ti"].xcom_push(key="parquet_path", value=str(p))


def task_load_sales_staging(**ctx):
    p = ctx["ti"].xcom_pull(task_ids="sales.extract_sales", key="parquet_path")
    load_staging(p)


def task_generate_returns(**ctx):
    generate_returns(return_rate=0.07, seed=42,
                     out_path=RAW_DIR / "returns.jsonl")


def task_check_returns_file(**ctx):
    """Branch: skip returns pipeline if the file doesn't exist."""
    if (RAW_DIR / "returns.jsonl").exists():
        return "returns.load_returns_staging"
    return "returns.skip_returns"


def task_load_returns_staging(**ctx):
    load_returns_staging(batch_id=_batch_id(**ctx))


def task_load_dims(**ctx):
    load_dim_store()
    load_dim_customer()
    load_dim_product()


def task_load_fact_sales(**ctx):
    load_fact_sales(batch_id=_batch_id(**ctx))


def task_load_fact_returns(**ctx):
    load_fact_returns(batch_id=_batch_id(**ctx))


def task_dq(**ctx):
    run_checks(batch_id=_batch_id(**ctx))


# --------------------------------- DAG -------------------------------

with DAG(
    dag_id="retail_sales_etl",
    description="End-to-end retail sales + returns ETL into star-schema DWH with marts",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["retail", "dwh", "etl", "scd2", "marts"],
) as dag:

    # 1. Wait for the source CSV to arrive (up to 10 minutes)
    wait_for_source = FileSensor(
        task_id="wait_for_source_file",
        filepath=str(RAW_DIR / "Superstore.csv"),
        poke_interval=15,
        timeout=600,
        mode="reschedule",   # frees the worker while waiting
    )

    # 2. Sales branch (extract + stage)
    with TaskGroup("sales") as sales_group:
        extract_sales = PythonOperator(
            task_id="extract_sales",
            python_callable=task_extract_sales,
        )
        stage_sales = PythonOperator(
            task_id="load_sales_staging",
            python_callable=task_load_sales_staging,
        )
        extract_sales >> stage_sales

    # 3. Returns branch (generate + branch + stage)
    with TaskGroup("returns") as returns_group:
        gen_returns = PythonOperator(
            task_id="generate_returns",
            python_callable=task_generate_returns,
        )
        branch = BranchPythonOperator(
            task_id="check_returns_file",
            python_callable=task_check_returns_file,
        )
        stage_returns = PythonOperator(
            task_id="load_returns_staging",
            python_callable=task_load_returns_staging,
        )
        skip_returns = EmptyOperator(task_id="skip_returns")

        gen_returns >> branch >> [stage_returns, skip_returns]

    # 4. Dimensions (SCD2)
    dims = PythonOperator(
        task_id="load_dimensions_scd2",
        python_callable=task_load_dims,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # 5. Facts (fan-out)
    with TaskGroup("facts") as facts_group:
        fact_sales = PythonOperator(
            task_id="load_fact_sales",
            python_callable=task_load_fact_sales,
        )
        fact_returns = PythonOperator(
            task_id="load_fact_returns",
            python_callable=task_load_fact_returns,
            trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
        )
        # fact_returns depends on fact_sales because it looks up dim keys via fact_sales
        fact_sales >> fact_returns

    # 6. Data quality gate
    dq = PythonOperator(
        task_id="data_quality_checks",
        python_callable=task_dq,
    )

    # 7. Refresh marts (fan-out - independent)
    with TaskGroup("refresh_marts") as marts_group:
        m1 = PythonOperator(task_id="mart_sales_daily",  python_callable=lambda: refresh_sales_daily())
        m2 = PythonOperator(task_id="mart_customer_360", python_callable=lambda: refresh_customer_360())
        m3 = PythonOperator(task_id="mart_inventory",    python_callable=lambda: refresh_inventory())

    done = EmptyOperator(task_id="mark_run_success")

    # ---------------------------- wiring -----------------------------
    wait_for_source >> [sales_group, returns_group] >> dims >> facts_group >> dq >> marts_group >> done
