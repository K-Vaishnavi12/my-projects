"""SCD Type 2 loader for dim_customer, dim_product, and Type-1 dim_store.

Algorithm (per SCD2 dim):
    1. Build the "incoming" snapshot from staging (one row per business key).
    2. Compute a stable ``row_hash`` over the tracked attributes.
    3. Compare vs the current version in the dim table:
         a. NEW business keys              -> INSERT new current row.
         b. CHANGED attributes (hash diff) -> expire current + INSERT new
                                              current with version+1.
         c. UNCHANGED                      -> do nothing.
    4. Type-1 dims (store, ship_mode) just upsert on the natural key.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Iterable

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

from etl.utils.db import get_engine

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_row(values: Iterable) -> str:
    joined = "||".join("" if v is None else str(v) for v in values)
    return hashlib.md5(joined.encode("utf-8")).hexdigest()


def _read_staging_distinct(conn: Connection, columns: list[str], source_table: str = "staging.superstore_raw") -> pd.DataFrame:
    col_list = ", ".join(columns)
    sql = f"SELECT DISTINCT {col_list} FROM {source_table} WHERE {columns[0]} IS NOT NULL"
    return pd.read_sql(text(sql), conn)


# ---------------------------------------------------------------------------
# SCD Type 2 core
# ---------------------------------------------------------------------------

def _scd2_upsert(
    conn: Connection,
    dim_table: str,           # e.g. "core.dim_customer"
    surrogate_key: str,       # e.g. "customer_key"
    business_key: str,        # e.g. "customer_id"
    tracked_cols: list[str],  # attributes whose changes create a new version
    incoming: pd.DataFrame,
) -> tuple[int, int]:
    """Perform the SCD2 merge. Returns (inserted, expired)."""

    # 1. compute incoming row_hash
    incoming = incoming.copy()
    incoming["row_hash"] = incoming[tracked_cols].apply(
        lambda r: _hash_row(r.values), axis=1
    )

    # 2. fetch current versions
    current = pd.read_sql(
        text(
            f"SELECT {business_key}, row_hash "
            f"FROM {dim_table} WHERE is_current = TRUE"
        ),
        conn,
    )

    merged = incoming.merge(current, on=business_key, how="left", suffixes=("", "_curr"))

    new_rows     = merged[merged["row_hash_curr"].isna()]
    changed_rows = merged[
        merged["row_hash_curr"].notna() & (merged["row_hash"] != merged["row_hash_curr"])
    ]

    inserted = 0
    expired  = 0

    # 3a. expire the current version for changed keys
    if len(changed_rows):
        keys = changed_rows[business_key].tolist()
        conn.execute(
            text(
                f"UPDATE {dim_table} "
                f"SET is_current = FALSE, effective_to = NOW() "
                f"WHERE is_current = TRUE AND {business_key} = ANY(:keys)"
            ),
            {"keys": keys},
        )
        expired = len(changed_rows)

    # 3b. insert NEW + CHANGED as fresh current rows
    to_insert = pd.concat([new_rows, changed_rows], ignore_index=True)
    if len(to_insert):
        insert_cols = [business_key] + tracked_cols + ["row_hash"]
        payload = to_insert[insert_cols].copy()
        payload["is_current"]     = True
        # Use a sentinel start date so historical facts (older than the load
        # time) still match this "current" version on the as-of join.
        payload["effective_from"] = pd.Timestamp("1900-01-01")
        payload["effective_to"]   = pd.Timestamp("9999-12-31")

        schema, table = dim_table.split(".")
        payload.to_sql(
            table, conn, schema=schema, if_exists="append",
            index=False, method="multi", chunksize=500,
        )

        # Backfill correct version numbers for keys that now have >1 row
        conn.execute(text(f"""
            WITH ranked AS (
                SELECT {business_key},
                       {surrogate_key} AS pk,
                       ROW_NUMBER() OVER (
                           PARTITION BY {business_key}
                           ORDER BY effective_from
                       ) AS v
                FROM {dim_table}
            )
            UPDATE {dim_table} d
            SET    version = r.v
            FROM   ranked r
            WHERE  d.{surrogate_key} = r.pk
              AND  d.version <> r.v
        """))
        inserted = len(to_insert)

    log.info("%s: inserted=%s expired=%s", dim_table, inserted, expired)
    return inserted, expired


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def load_dim_customer() -> tuple[int, int]:
    """Superstore customers can appear at multiple cities (shipping addresses).
    Geography belongs to dim_store, not dim_customer, so we only track
    name + segment here (the actually customer-stable attributes)."""
    engine = get_engine()
    with engine.begin() as conn:
        incoming = _read_staging_distinct(conn, [
            "customer_id", "customer_name", "segment",
        ])
        # de-dupe defensively (shouldn't be needed but safety net)
        incoming = incoming.drop_duplicates(subset=["customer_id"], keep="last")
        tracked = ["customer_name", "segment"]
        return _scd2_upsert(conn, "core.dim_customer", "customer_key",
                            "customer_id", tracked, incoming)


def load_dim_product() -> tuple[int, int]:
    engine = get_engine()
    with engine.begin() as conn:
        incoming = _read_staging_distinct(conn, [
            "product_id", "product_name", "category", "sub_category",
        ])
        incoming = incoming.drop_duplicates(subset=["product_id"], keep="last")
        tracked = ["product_name", "category", "sub_category"]
        return _scd2_upsert(conn, "core.dim_product", "product_key",
                            "product_id", tracked, incoming)


def load_dim_store() -> int:
    """Type-1 upsert on the natural key."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO core.dim_store (country, region, state, city, postal_code)
            SELECT DISTINCT country, region, state, city, postal_code
            FROM   staging.superstore_raw
            WHERE  country IS NOT NULL
            ON CONFLICT (country, region, state, city, postal_code) DO NOTHING
        """))
        return conn.execute(text("SELECT COUNT(*) FROM core.dim_store")).scalar_one()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dim_store()
    load_dim_customer()
    load_dim_product()
