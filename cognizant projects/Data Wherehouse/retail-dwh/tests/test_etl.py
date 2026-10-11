"""Pytest unit tests for the ETL library.

Run with:
    docker exec -e PYTHONPATH=/opt/airflow retail_airflow \\
        pytest /opt/airflow/tests -v
"""

from __future__ import annotations

import pandas as pd
import pytest

from etl.load_dim_scd2 import _hash_row


class TestRowHash:
    def test_same_values_produce_same_hash(self):
        assert _hash_row(["A", "B", 1]) == _hash_row(["A", "B", 1])

    def test_different_values_produce_different_hash(self):
        assert _hash_row(["A", "B", 1]) != _hash_row(["A", "B", 2])

    def test_none_and_empty_string_collide(self):
        # documented behaviour: None and "" both serialise to ""
        assert _hash_row([None, "x"]) == _hash_row(["", "x"])

    def test_column_order_matters(self):
        assert _hash_row(["A", "B"]) != _hash_row(["B", "A"])

    def test_hash_is_hex_md5_length(self):
        h = _hash_row(["anything"])
        assert len(h) == 32
        int(h, 16)   # will raise if not hex


class TestReturnsGenerator:
    """Property tests on the returns generator - runs only if a DB is up."""

    def test_generator_is_deterministic_with_seed(self, tmp_path, monkeypatch):
        pytest.importorskip("sqlalchemy")
        # This test needs a live Postgres so we skip if the engine can't connect.
        try:
            from etl.utils.db import get_engine
            get_engine().connect().close()
        except Exception:
            pytest.skip("Postgres not reachable - skipping integration test")

        from etl.generate_returns import generate_returns
        a = generate_returns(return_rate=0.05, seed=99, out_path=tmp_path / "a.jsonl")
        b = generate_returns(return_rate=0.05, seed=99, out_path=tmp_path / "b.jsonl")
        assert a.read_text() == b.read_text()


class TestExtractSchemaValidation:
    def test_missing_column_raises(self, tmp_path, monkeypatch):
        # write a bad CSV
        bad = tmp_path / "bad.csv"
        bad.write_text("Row ID,Order ID\n1,X\n")
        monkeypatch.setenv("RAW_DIR", str(tmp_path))

        from etl.extract import extract
        with pytest.raises(ValueError, match="Missing expected columns"):
            extract(source_file="bad.csv", batch_id="t")


# ---------------------------------------------------------------------
# Small pure-python tests on the SCD2 change-detection logic
# ---------------------------------------------------------------------

def _detect_changes(current: pd.DataFrame, incoming: pd.DataFrame, bk: str) -> tuple[int, int]:
    """Mirror of the diff logic in _scd2_upsert - kept as a pure function
    so it can be unit tested without a DB."""
    merged = incoming.merge(current, on=bk, how="left", suffixes=("", "_curr"))
    new_rows     = merged[merged["row_hash_curr"].isna()]
    changed_rows = merged[
        merged["row_hash_curr"].notna() & (merged["row_hash"] != merged["row_hash_curr"])
    ]
    return len(new_rows), len(changed_rows)


class TestScd2ChangeDetection:
    def test_all_new(self):
        current  = pd.DataFrame({"customer_id": [], "row_hash": []})
        incoming = pd.DataFrame({"customer_id": ["A", "B"], "row_hash": ["h1", "h2"]})
        n, c = _detect_changes(current, incoming, "customer_id")
        assert (n, c) == (2, 0)

    def test_all_unchanged(self):
        current  = pd.DataFrame({"customer_id": ["A"], "row_hash": ["h1"]})
        incoming = pd.DataFrame({"customer_id": ["A"], "row_hash": ["h1"]})
        n, c = _detect_changes(current, incoming, "customer_id")
        assert (n, c) == (0, 0)

    def test_one_changed_one_new(self):
        current  = pd.DataFrame({"customer_id": ["A"], "row_hash": ["h1"]})
        incoming = pd.DataFrame({"customer_id": ["A", "B"], "row_hash": ["h2", "hB"]})
        n, c = _detect_changes(current, incoming, "customer_id")
        assert (n, c) == (1, 1)
