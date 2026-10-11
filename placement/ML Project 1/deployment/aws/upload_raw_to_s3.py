"""One-shot: upload the raw data lake to S3 for ETL replay."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from loguru import logger

from symposium.config import get_settings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="raw/", help="S3 key prefix")
    args = ap.parse_args()

    try:
        import boto3
    except ImportError:
        raise SystemExit(
            "Install boto3 first: pip install boto3"
        )

    s = get_settings()
    bucket = s.aws_s3_bucket
    region = s.aws_region

    session = boto3.Session(region_name=region)
    s3 = session.client("s3")

    n = 0
    for f in Path(s.raw_data_dir).rglob("*.json"):
        rel = f.relative_to(s.raw_data_dir).as_posix()
        key = f"{args.prefix.rstrip('/')}/{rel}"
        s3.upload_file(str(f), bucket, key)
        n += 1
    logger.success(f"Uploaded {n} files to s3://{bucket}/{args.prefix}")


if __name__ == "__main__":
    main()
