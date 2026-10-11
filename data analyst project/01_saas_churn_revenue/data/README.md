# Data — SaaS Churn & Revenue

## Expected files

1. **Kaggle Telecom Churn**  
   - Download: https://www.kaggle.com/datasets/blastchar/telco-customer-churn  
   - Place `WA_Fn-UseC_-Telco-Customer-Churn.csv` here (or update paths in scripts).

2. **Simulated SaaS subscription logs** (optional)  
   - `subscriptions.csv` — subscription_id, customer_id, plan_id, mrr, start_date, end_date, status  
   - `customers.csv` — customer_id, signup_date, segment, region  
   - `events.csv` — event_id, customer_id, event_type, event_date  

Scripts in `scripts/` can generate sample data if real files are missing.
