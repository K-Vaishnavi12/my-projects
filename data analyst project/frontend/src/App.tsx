import React, { useEffect, useRef, useState } from 'react';
import { motion, useInView, animate } from 'framer-motion';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';
import { Line, Doughnut, Bar } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

// Global Chart configuration
ChartJS.defaults.color = '#64748b'; // Slate 500
ChartJS.defaults.borderColor = '#f1f5f9'; // Slate 100
ChartJS.defaults.font.family = '"Inter", system-ui, sans-serif';
(ChartJS.defaults.plugins.tooltip as any).backgroundColor = '#0f172a'; // Slate 900
(ChartJS.defaults.plugins.tooltip as any).titleColor = '#ffffff';

const ACCENT_CHURN = '#0ea5e9'; // Light Blue
const ACCENT_ATTRIBUTION = '#f59e0b'; // Amber
const COLORS = [
    ACCENT_CHURN,
    '#38bdf8',
    '#7dd3fc',
    ACCENT_ATTRIBUTION,
    '#fbbf24',
    '#fcd34d',
];

const Counter = ({ from = 0, target, decimals = 0, duration = 1.5 }: { from?: number; target: number; decimals?: number; duration?: number; }) => {
    const nodeRef = useRef<HTMLSpanElement>(null);
    const inView = useInView(nodeRef, { once: true, margin: "0px 0px -80px 0px" });

    useEffect(() => {
        if (inView && nodeRef.current) {
            const controls = animate(from, target, {
                duration,
                ease: "easeOut",
                onUpdate(value) {
                    if (nodeRef.current) {
                        nodeRef.current.textContent = value.toFixed(decimals);
                    }
                }
            });
            return () => controls.stop();
        }
    }, [from, target, decimals, duration, inView]);

    return <span ref={nodeRef}>{from.toFixed(decimals)}</span>;
};

const FadeUp = ({ children, delay = 0, className = "" }: { children: React.ReactNode, delay?: number, className?: string }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "0px 0px -60px 0px" }}
            transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
            className={className}
        >
            {children}
        </motion.div>
    );
};

const KpiCard = ({ value, label, icon, decimals = 0, delay = 0, prefix = "", suffix = "" }: any) => {
    return (
        <FadeUp delay={delay} className="kpi-card">
            <div className="kpi-icon">{icon}</div>
            <span className="kpi-value">
                {prefix}<Counter target={value} decimals={decimals} />{suffix}
            </span>
            <span className="kpi-label">{label}</span>
        </FadeUp>
    );
}


function App() {
    const [headerHidden, setHeaderHidden] = useState(false);
    const [dateRange, setDateRange] = useState('YTD'); // State for demo filters
    const lastY = useRef(0);

    useEffect(() => {
        const handleScroll = () => {
            const y = window.scrollY;
            setHeaderHidden(y > 120 && y > lastY.current);
            lastY.current = y;
        };
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // Cohort Heatmap Data
    const periods = ['M0', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6'];
    const cohorts = ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05'];
    const retentionByCohort = cohorts.map((_, i) =>
        periods.map((_, j) => Math.round(100 - j * 11 - i * 1.5 - Math.random() * 5))
    );

    const cohortData = {
        labels: periods,
        datasets: cohorts.map((cohort, i) => ({
            label: cohort,
            data: retentionByCohort[i],
            borderColor: COLORS[i % COLORS.length],
            backgroundColor: COLORS[i % COLORS.length] + '15',
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointHoverRadius: 8,
        })),
    };

    const cohortOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { grid: { color: 'rgba(255,255,255,0.04)' } },
            y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.04)' } },
        },
        plugins: {
            legend: { position: 'bottom' as const },
            tooltip: { callbacks: { label: (c: any) => `${c.dataset.label}: ${c.raw}% retention` } },
        },
    };

    // Churn Segments Data
    const churnSegmentsData = {
        labels: ['Low', 'Medium', 'High', 'Critical'],
        datasets: [{
            data: [3200, 1200, 450, 150],
            backgroundColor: [ACCENT_CHURN, '#55efc4', ACCENT_ATTRIBUTION, '#ef4444'],
            borderColor: 'transparent',
            hoverOffset: 12,
        }],
    };

    const churnSegmentsOptions = {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '62%',
        plugins: {
            legend: { position: 'bottom' as const },
            tooltip: {
                callbacks: {
                    label: (c: any) => `${c.label}: ${c.raw} customers (${((c.raw / 5000) * 100).toFixed(1)}%)`,
                },
            },
        },
    };

    // MRR Trend Data - Dynamic based on dateRange
    const getMrrData = () => {
        if (dateRange === '30D') {
            return {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                mrr: [520, 525, 532, 535],
                churn: [4.2, 4.3, 4.1, 4.2]
            };
        } else if (dateRange === '90D') {
            return {
                labels: ['Oct', 'Nov', 'Dec'],
                mrr: [510, 520, 535],
                churn: [3.9, 4.2, 4.2]
            };
        }
        return { // YTD Default
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            mrr: [420, 445, 468, 455, 472, 488, 501, 495, 510, 528, 520, 535],
            churn: [5.2, 4.8, 4.5, 4.9, 4.2, 4.0, 4.1, 4.4, 3.9, 3.8, 4.2, 4.2]
        };
    };

    const currentMrr = getMrrData();
    const mrrTrendData = {
        labels: currentMrr.labels,
        datasets: [
            {
                label: 'MRR ($K)',
                data: currentMrr.mrr,
                borderColor: ACCENT_CHURN,
                backgroundColor: ACCENT_CHURN + '20',
                fill: true,
                tension: 0.35,
                yAxisID: 'y',
            },
            {
                label: 'Churn %',
                data: currentMrr.churn,
                borderColor: ACCENT_ATTRIBUTION,
                backgroundColor: 'transparent',
                borderDash: [4, 2],
                tension: 0.35,
                yAxisID: 'y1',
            },
        ],
    };

    const mrrTrendOptions = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index' as const, intersect: false },
        scales: {
            y: { type: 'linear' as const, position: 'left' as const, grid: { color: 'rgba(255,255,255,0.04)' } },
            y1: { type: 'linear' as const, position: 'right' as const, min: 0, max: 8, grid: { drawOnChartArea: false } },
        },
        plugins: {
            legend: { position: 'top' as const },
        },
    };

    // Attribution Data
    const attributionData = {
        labels: ['Google Paid', 'Meta', 'LinkedIn', 'Organic', 'Email'],
        datasets: [{
            label: 'Attributed conversions',
            data: [420, 380, 180, 520, 310],
            backgroundColor: [
                ACCENT_ATTRIBUTION,
                ACCENT_ATTRIBUTION + 'cc',
                ACCENT_ATTRIBUTION + '99',
                ACCENT_CHURN,
                ACCENT_CHURN + 'cc',
            ],
            borderColor: [ACCENT_ATTRIBUTION, ACCENT_ATTRIBUTION, ACCENT_ATTRIBUTION, ACCENT_CHURN, ACCENT_CHURN],
            borderWidth: 1,
            borderRadius: 6,
            hoverBackgroundColor: [ACCENT_ATTRIBUTION, ACCENT_ATTRIBUTION, ACCENT_ATTRIBUTION, ACCENT_CHURN, ACCENT_CHURN],
        }],
    };

    const attributionOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { grid: { display: false } },
            y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.04)' } },
        },
        plugins: {
            legend: { display: false },
            tooltip: { callbacks: { afterLabel: (c: any) => `Share: ${((c.raw / 1810) * 100).toFixed(1)}%` } },
        },
    };

    // Spend vs Revenue Data
    const spendRevenueData = {
        labels: ['Google', 'Meta', 'LinkedIn', 'Organic', 'Email'],
        datasets: [
            {
                label: 'Spend ($K)',
                data: [85, 62, 45, 0, 12],
                backgroundColor: ACCENT_ATTRIBUTION + '99',
                borderColor: ACCENT_ATTRIBUTION,
                borderWidth: 1,
                borderRadius: 6,
                yAxisID: 'y',
            },
            {
                label: 'Revenue ($K)',
                data: [280, 195, 98, 420, 145],
                backgroundColor: ACCENT_CHURN + '99',
                borderColor: ACCENT_CHURN,
                borderWidth: 1,
                borderRadius: 6,
                yAxisID: 'y',
            },
        ],
    };

    const spendRevenueOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { grid: { display: false } },
            y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.04)' } },
        },
        plugins: {
            legend: { position: 'top' as const },
        },
    };

    return (
        <>
            <div className="noise"></div>
            <div className="grid-bg"></div>

            <header className={`header ${headerHidden ? 'hidden' : ''}`}>
                <nav className="nav">
                    <a href="#hero" className="logo">
                        <span className="logo-bracket">[</span>ANALYTICS<span className="logo-bracket">]</span>
                    </a>
                    <div className="nav-controls">
                        <select
                            className="filter-select"
                            value={dateRange}
                            onChange={(e) => setDateRange(e.target.value)}
                        >
                            <option value="30D">Last 30 Days</option>
                            <option value="90D">Last 90 Days</option>
                            <option value="YTD">Year to Date</option>
                        </select>
                    </div>
                    <div className="nav-links">
                        <a href="#churn">Churn & Revenue</a>
                        <a href="#attribution">Ad Attribution</a>
                        <a href="#product">Product (A/B)</a>
                    </div>
                </nav>
            </header>

            <main>
                <section id="hero" className="hero">
                    <div className="hero-content">
                        <motion.div
                            className="hello-badge"
                            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, delay: 0.1 }}
                        >
                            👋 Hello, I'm a Data Analyst
                        </motion.div>
                        <motion.h1
                            className="hero-title"
                            initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }}
                        >
                            Turning raw data into <span className="accent">strategic business decisions.</span>
                        </motion.h1>
                        <motion.p
                            className="hero-desc"
                            initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.35 }}
                        >
                            I specialize in uncovering actionable insights from complex datasets. Browse my portfolio below to see how I tackle SaaS cohort retention, revenue forecasting, and multi-touch marketing attribution.
                        </motion.p>
                        <motion.div
                            className="hero-ctas"
                            initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.5 }}
                        >
                            <a href="#churn" className="btn btn-primary">Explore My Work</a>
                            <a href="mailto:hello@example.com" className="btn btn-ghost">Get in Touch</a>
                        </motion.div>
                    </div>

                    <div className="hero-visual">
                        <div className="mascot-backdrop"></div>
                        <img src="/mascot.png" alt="Data Analyst Mascot" className="mascot-image" />

                        <div className="floating-card card-1">
                            <div className="floating-icon">📊</div>
                            <div className="card-text">
                                <span className="card-kpi">22%</span>
                                <span className="card-label">Avg. Churn Reduction</span>
                            </div>
                        </div>
                        <div className="floating-card card-2">
                            <div className="floating-icon">📈</div>
                            <div className="card-text">
                                <span className="card-kpi">18%</span>
                                <span className="card-label">ROAS Improvement</span>
                            </div>
                        </div>
                    </div>
                </section>

                <section id="churn" className="section section-churn">
                    <FadeUp className="section-header">
                        <span className="section-tag">01 — SaaS / IT</span>
                        <h2>Churn & Revenue Retention</h2>
                        <p>Subscription churn impacting ARR. Cohort analysis, risk segmentation, NRR.</p>
                    </FadeUp>
                    <div className="kpi-row">
                        <KpiCard value={dateRange === '30D' ? 4.9 : dateRange === '90D' ? 4.5 : 4.2} decimals={1} delay={0.1} icon="↓" label="Monthly Churn Rate" suffix="%" />
                        <KpiCard value={dateRange === '30D' ? 1120 : dateRange === '90D' ? 1180 : 1247} delay={0.2} icon="$" label="Avg Customer LTV" prefix="$" />
                        <KpiCard value={dateRange === '30D' ? 95 : dateRange === '90D' ? 96 : 98} delay={0.3} icon="↗" label="Net Revenue Retention" suffix="%" />
                    </div>
                    <div className="charts-row">
                        <FadeUp delay={0.15} className="chart-card glass">
                            <h3>Cohort Retention Curves</h3>
                            <div className="chart-wrap">
                                <Line data={cohortData} options={cohortOptions} />
                            </div>
                        </FadeUp>
                        <FadeUp delay={0.25} className="chart-card glass">
                            <h3>Churn Risk Segments</h3>
                            <div className="chart-wrap">
                                <Doughnut data={churnSegmentsData} options={churnSegmentsOptions} />
                            </div>
                        </FadeUp>
                    </div>
                    <FadeUp delay={0.15} className="chart-card glass chart-full">
                        <h3>MRR & Churn Trend</h3>
                        <div className="chart-wrap">
                            <Line data={mrrTrendData} options={mrrTrendOptions} />
                        </div>
                    </FadeUp>
                </section>

                <section id="attribution" className="section section-attribution">
                    <FadeUp className="section-header">
                        <span className="section-tag">02 — Marketing / SaaS</span>
                        <h2>Ad Spend Incrementality & Attribution</h2>
                        <p>Optimize spend, attribute revenue to channels. Incrementality tests, multi-touch models.</p>
                    </FadeUp>
                    <div className="kpi-row">
                        <KpiCard value={42} delay={0.1} icon="↑" label="Incremental Lift" suffix="%" />
                        <KpiCard value={3.2} decimals={1} delay={0.2} icon="×" label="ROAS" suffix="×" />
                        <KpiCard value={89} delay={0.3} icon="%" label="Paid Attribution Share" suffix="%" />
                    </div>
                    <div className="charts-row">
                        <FadeUp delay={0.15} className="chart-card glass">
                            <h3>Attribution by Channel</h3>
                            <div className="chart-wrap">
                                <Bar data={attributionData} options={attributionOptions} />
                            </div>
                        </FadeUp>
                        <FadeUp delay={0.25} className="chart-card glass">
                            <h3>Spend vs Revenue by Channel</h3>
                            <div className="chart-wrap">
                                <Bar data={spendRevenueData} options={spendRevenueOptions} />
                            </div>
                        </FadeUp>
                    </div>
                </section>

                <section id="ml" className="section section-ml">
                    <FadeUp className="section-header">
                        <span className="section-tag" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' }}>03 — Predictive ML</span>
                        <h2>Customer Churn Prediction (Scikit-Learn)</h2>
                        <p>Random Forest Classification model identifying high-risk subscriptions based on usage telemetry and engagement scores.</p>
                    </FadeUp>
                    <div className="kpi-row">
                        <KpiCard value={88.4} decimals={1} delay={0.1} icon="🎯" label="Model Accuracy" suffix="%" />
                        <KpiCard value={0.82} decimals={2} delay={0.2} icon="⚖️" label="F1 Score" />
                        <KpiCard value={0.91} decimals={2} delay={0.3} icon="📈" label="ROC AUC" />
                    </div>
                    <div className="charts-row">
                        <FadeUp delay={0.15} className="chart-card glass chart-full">
                            <h3>Random Forest Feature Importance</h3>
                            <div className="chart-wrap" style={{ height: '250px' }}>
                                <Bar
                                    data={{
                                        labels: ['Engagement Score', 'Tenure (Months)', 'Support Tickets (30d)', 'Login Recency', 'Monthly MRR'],
                                        datasets: [{
                                            label: 'Relative Importance',
                                            data: [0.38, 0.25, 0.18, 0.12, 0.07],
                                            backgroundColor: '#8b5cf6',
                                            borderRadius: 4,
                                        }]
                                    }}
                                    options={{
                                        responsive: true, maintainAspectRatio: false,
                                        indexAxis: 'y',
                                        plugins: { legend: { display: false } },
                                        scales: { x: { grid: { color: 'rgba(255,255,255,0.04)' } }, y: { grid: { display: false } } }
                                    }}
                                />
                            </div>
                        </FadeUp>
                    </div>
                </section>

                <section id="product" className="section section-product">
                    <FadeUp className="section-header">
                        <span className="section-tag" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>04 — Product & UX</span>
                        <h2>A/B Testing & Product Analytics</h2>
                        <p>Analyze feature rollouts and measure statistical significance of conversion tests.</p>
                    </FadeUp>

                    <div className="kpi-row">
                        <KpiCard value={15.4} decimals={1} delay={0.1} icon="🔄" label="Checkout Conversion (Variant B)" suffix="%" />
                        <KpiCard value={0.012} decimals={3} delay={0.2} icon="📏" label="P-Value (Statistically Sig.)" />
                        <KpiCard value={99} delay={0.3} icon="✨" label="Confidence Level" suffix="%" />
                    </div>

                    <div className="charts-row">
                        <FadeUp delay={0.15} className="chart-card glass">
                            <h3>Conversion Rate Lift (Control vs Variant)</h3>
                            <div className="chart-wrap">
                                <Bar
                                    data={{
                                        labels: ['Control (Old Checkout)', 'Variant B (New 1-Click)'],
                                        datasets: [{
                                            label: 'Conversion Rate %',
                                            data: [12.8, 15.4],
                                            backgroundColor: ['#64748b', '#10b981'],
                                            borderRadius: 6,
                                        }]
                                    }}
                                    options={{
                                        responsive: true, maintainAspectRatio: false,
                                        plugins: { legend: { display: false } }
                                    }}
                                />
                            </div>
                        </FadeUp>
                        <FadeUp delay={0.25} className="chart-card glass">
                            <h3>Cumulative Revenue Impact</h3>
                            <div className="chart-wrap">
                                <Line
                                    data={{
                                        labels: ['Day 1', 'Day 3', 'Day 7', 'Day 14', 'Day 21', 'Day 30'],
                                        datasets: [
                                            { label: 'Control', data: [10, 28, 65, 120, 180, 240], borderColor: '#64748b' },
                                            { label: 'Variant B', data: [12, 35, 82, 160, 245, 320], borderColor: '#10b981', borderDash: [5, 5] }
                                        ]
                                    }}
                                    options={{ responsive: true, maintainAspectRatio: false }}
                                />
                            </div>
                        </FadeUp>
                    </div>
                </section>
            </main>

            <footer className="footer">
                <p>Data Analytics — Python, SQL, Pandas, Power BI</p>
            </footer>
        </>
    );
}

export default App;
