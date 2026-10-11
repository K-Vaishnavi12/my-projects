"""One-shot: build FAISS snapshots from Mongo (for offline dev)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from symposium.vectorstore.local_faiss import LocalFaissStore


def main() -> None:
    store = LocalFaissStore()
    store.build_from_mongo()
    print("FAISS indexes written to", store.snapshot_dir)


if __name__ == "__main__":
    main()
