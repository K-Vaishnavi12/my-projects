# Ad Spend Incrementality & Attribution Modeling (SaaS / Marketing)

**Business problem:** Optimize marketing spend and attribute revenue to channels.

## Data sources

- **Campaign logs** — spend by channel, campaign, date
- **Conversion events** — signups, trials, paid conversions with timestamps
- **Touchpoints** — user journey (channel touches before conversion)

Place files in `data/` (see `data/README.md` for schema).

## Tech stack

Python, SQL, Pandas, statistical modeling (scikit-learn, scipy)

## Key analysis

- **Incrementality** — holdout/test vs exposed; lift and confidence intervals
- **Multi-touch attribution** — linear, time-decay, position-based (U-shaped)
- **ROI by channel** — CAC, ROAS, incremental revenue per dollar spent

## KPIs

| KPI | Description |
|-----|-------------|
| CAC | Customer acquisition cost (spend / new customers) |
| ROAS | Return on ad spend (revenue / spend) |
| Incremental Lift | % lift in conversions from exposed vs control |
| Attribution Share | % of conversions attributed to each channel |

## Folder structure

- `data/` — campaign spend, conversions, touchpoints
- `notebooks/` — incrementality and attribution notebooks
- `scripts/` — incrementality tests, attribution models
- `sql/` — spend and conversion aggregation queries
