# Analytics Command Center — Interactive Dashboard

A single-page, interactive web dashboard for the **SaaS Churn & Revenue** and **Ad Spend Attribution** projects.

## Features

- **Animated hero** with floating KPI cards and gradient typography
- **Scroll-triggered reveals** for section headers, KPI cards, and charts
- **Counter animations** on KPI cards when they enter view
- **Header** that hides on scroll-down and reappears on scroll-up
- **Hover effects** on cards (lift, glow, border highlight)
- **Charts** (Chart.js): cohort retention curves, churn segments, MRR trend, attribution by channel, spend vs revenue

## How to run

1. Open `index.html` in a modern browser (Chrome, Edge, Firefox), or
2. Serve the folder with a local server (recommended for best behavior):
   ```bash
   cd dashboard
   python -m http.server 8080
   ```
   Then open http://localhost:8080

No build step or Node.js required. Uses Chart.js from CDN.
