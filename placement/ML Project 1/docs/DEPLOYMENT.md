# AWS Deployment Guide

Two paths: 5-minute local Docker, or a full EC2 rollout.

---

## Path A: Local Docker (fastest)

```powershell
copy .env.example .env       # then fill in secrets
docker compose up -d --build
docker compose exec symposium python scripts/run_etl.py --topics history
docker compose exec symposium python scripts/train_models.py
```

Open http://localhost:8501

---

## Path B: AWS EC2

### 1. Prerequisites

- AWS account (free tier works)
- MongoDB Atlas free M0 cluster (https://cloud.mongodb.com)
- Google Gemini API key (https://aistudio.google.com/apikey)

### 2. Create the EC2 instance

- **AMI**: Ubuntu Server 22.04 LTS
- **Instance type**: `t3.small` (2 vCPU, 2 GiB RAM) — enough for demo traffic
- **Storage**: 20 GiB gp3
- **Security group**:
  - Inbound TCP 22 from your IP (SSH)
  - Inbound TCP 8501 from anywhere (Streamlit) — restrict later
- **Key pair**: create/download and keep the `.pem`

### 3. Bootstrap

```bash
# on your laptop
scp -i key.pem deployment/aws/deploy_ec2.sh ubuntu@<HOST>:~
scp -i key.pem .env                             ubuntu@<HOST>:~/symposium/.env
ssh -i key.pem ubuntu@<HOST>
REPO_URL=https://github.com/YOUR_USER/symposium.git bash deploy_ec2.sh
```

That's it. `deploy_ec2.sh` installs Docker, pulls the repo, brings up
docker-compose, runs the first-time ETL, and trains the ML models.

### 4. (Optional) Ship raw data to S3

```powershell
python deployment\aws\upload_raw_to_s3.py --prefix raw/
```

Requires `boto3` and standard AWS credentials
(`aws configure`). The S3 bucket is your "cold storage" — the ETL can
reload from there instead of hitting Wikipedia if you want to demo
the pipeline without an internet round-trip.

### 5. (Optional) Point Power BI at RDS

Once you outgrow SQLite:

- Provision an `RDS PostgreSQL` db.t3.micro.
- Change `SQLITE_PATH` in `.env` to a PostgreSQL SQLAlchemy URL and
  swap `SqliteLoader` for a Postgres variant (all queries are ANSI).
- Point Power BI at the Postgres endpoint using the built-in
  connector — no CSV export step needed anymore.

---

## AWS services used

| Service | Role |
|---|---|
| **EC2** | Compute — runs the Docker Compose stack |
| **S3** | Raw data lake (`data/raw/` upload) |
| **RDS PostgreSQL** (optional) | Production DWH |
| **IAM** | Role for the EC2 instance to read/write S3 |
| **CloudWatch** | Streamlit + docker logs shipped via `awslogs` driver |
| **Route 53 + ACM** (optional) | HTTPS + friendly domain |

These map directly onto the Cognizant syllabus's **AWS Services**
line-item (Compute, Storage, Database, Networking, Security,
Management).

---

## Cost estimate (demo scale)

| Item | Monthly cost |
|---|---|
| EC2 t3.small (free-tier eligible) | ~$0-15 |
| S3 storage (< 1 GB) | ~$0.02 |
| RDS db.t3.micro (free-tier eligible) | ~$0-15 |
| MongoDB Atlas M0 | $0 |
| Data transfer | ~$1 |
| **Total** | ~$0-32 |
