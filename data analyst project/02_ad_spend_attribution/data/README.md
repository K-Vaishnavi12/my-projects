# Data — Ad Spend & Attribution

## Expected files

1. **campaign_spend.csv**
   - campaign_id, channel, date, spend, impressions, clicks

2. **conversions.csv**
   - conversion_id, user_id, conversion_date, conversion_value, conversion_type (signup/trial/paid)

3. **touchpoints.csv** (for multi-touch attribution)
   - user_id, touch_date, channel, touch_order (position in journey), conversion_id (nullable)

Use `scripts/generate_sample_campaign_data.py` to create sample data if needed.
