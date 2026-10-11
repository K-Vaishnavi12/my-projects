# Data Analytics Portfolio — SaaS & Marketing

Two end-to-end analytics projects: **SaaS Customer Churn & Revenue Retention** and **Ad Spend Incrementality & Attribution Modeling**.

---

## 1. SaaS Customer Churn & Revenue Retention (IT / SaaS)

**Business problem:** Subscription churn impacting ARR.

| Area | Details |
|------|--------|
| **Data sources** | Kaggle Telecom Churn, simulated SaaS subscription logs |
| **Tech stack** | Python, SQL, Power BI, Pandas |
| **Key analysis** | Cohort retention, churn probability segmentation, SQL revenue lifetime |
| **KPIs** | Monthly Churn Rate, Customer Lifetime Value, Net Revenue Retention |
| **Impact** | Simulated 22% churn reduction, 18% LTV improvement |

**Resume bullets:**
- Performed cohort analysis across 5K+ users to reduce churn by 22%.
- Designed ARR tracking dashboard for revenue retention strategy.

**Folder:** [`01_saas_churn_revenue/`](01_saas_churn_revenue/)

---

## 2. Ad Spend Incrementality & Attribution Modeling (SaaS / Marketing)

**Business problem:** Optimize marketing spend and attribute revenue to channels.

| Area | Details |
|------|--------|
| **Data sources** | Campaign logs, conversion events, spend by channel |
| **Tech stack** | Python, SQL, Pandas, statistical modeling |
| **Key analysis** | Incrementality tests, multi-touch attribution, ROI by channel |
| **KPIs** | CAC, ROAS, Incremental Lift, Attribution share |

**Folder:** [`02_ad_spend_attribution/`](02_ad_spend_attribution/)

---

## Setup

```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Place datasets in each module’s `data/` folder (see module READMEs for expected files).

---

## Interactive dashboard

Open **`dashboard/index.html`** in a browser (or run a local server from the `dashboard/` folder) for an interactive UI with animations, hover effects, and charts. See [`dashboard/README.md`](dashboard/README.md).

## Project structure

```
├── README.md
├── requirements.txt
├── config/
├── dashboard/          # Web UI (HTML/CSS/JS + Chart.js)
├── 01_saas_churn_revenue/
│   ├── data/
│   ├── notebooks/
│   ├── scripts/
│   ├── sql/
│   └── power_bi/
└── 02_ad_spend_attribution/
    ├── data/
    ├── notebooks/
    ├── scripts/
    └── sql/
```
