"""Export every dim + fact table to CSV for Power BI."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from symposium.dwh import Warehouse


def main() -> None:
    wh = Warehouse()
    paths = wh.export_all_csv()
    print(f"Exported {len(paths)} files:")
    for p in paths:
        print(f"  {p}")
    wh.close()


if __name__ == "__main__":
    main()
