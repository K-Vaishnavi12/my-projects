import { Link } from 'react-router-dom'
import { useGame } from '../context/GameContext'
import { ChevronRight, Zap, Trophy, Map, Calendar, Star, Code } from 'lucide-react'
import './Home.css'

const PARTICLES = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 3 + 1,
    delay: Math.random() * 4,
    dur: Math.random() * 6 + 6,
}))

const FEATURES = [
    { icon: '🎮', title: 'Play & Learn', desc: 'Interactive mini-games that teach DSA concepts visually and intuitively.' },
    { icon: '🐍', title: 'Python Code', desc: 'Every concept shown with clean, annotated Python code with syntax highlighting.' },
    { icon: '🧠', title: 'Quizzes', desc: 'Test your knowledge with smart quizzes and earn XP for every correct answer.' },
    { icon: '🏆', title: 'Achievements', desc: 'Unlock badges, level up, and compete on the global leaderboard.' },
]

const DSA_TOPICS = [
    { icon: '🔢', label: 'Arrays', color: '#38bdf8' },
    { icon: '🔗', label: 'Linked Lists', color: '#a855f7' },
    { icon: '📚', label: 'Stacks & Queues', color: '#22d3a0' },
    { icon: '🌳', label: 'Trees & BST', color: '#fb923c' },
    { icon: '⚡', label: 'Sorting Algos', color: '#facc15' },
    { icon: '🗺️', label: 'Graphs', color: '#ec4899' },
    { icon: '🔑', label: 'Hash Tables', color: '#10b981' },
    { icon: '🧠', label: 'Dynamic Programming', color: '#f43f5e' },
    { icon: '🏔️', label: 'Heaps', color: '#8b5cf6' },
    { icon: '🌲', label: 'Tries', color: '#14b8a6' },
]

const DAILY_CHALLENGE = {
    title: "Reverse a Linked List",
    xp: 150,
    topic: "Linked Lists",
    difficulty: "Medium"
}

const TESTIMONIALS = [
    { name: 'Alex M.', role: 'Student', text: '"AlgoQuest made learning trees so much easier. The visualizations are top tier!"', rating: 5 },
    { name: 'Sarah K.', role: 'Junior Dev', text: '"I finally understand Dijkstra\'s algorithm thanks to the interactive graphs module. 10/10."', rating: 5 },
    { name: 'David L.', role: 'CS Major', text: '"The Python code snippets combined with the games are exactly what I needed to pass my DSA class."', rating: 5 },
]

export default function Home() {
    const { xp, level, completedModules } = useGame()
    return (
        <div className="home">
            <div className="stars-bg grid-bg" />
            {PARTICLES.map(p => (
                <div key={p.id} className="particle" style={{
                    left: `${p.x}%`, top: `${p.y}%`,
                    width: p.size, height: p.size,
                    animationDelay: `${p.delay}s`,
                    animationDuration: `${p.dur}s`,
                }} />
            ))}

            {/* ── HERO ── */}
            <section className="hero">
                <div className="hero-badge animate-slide-up">
                    <Zap size={14} /> Learn DSA Through Gaming
                </div>
                <h1 className="hero-title animate-slide-up">
                    <span className="hero-title-main animate-neon-text">AlgoQuest</span>
                    <br />
                    <span className="hero-title-sub">Master Python DSA</span>
                </h1>
                <p className="hero-desc animate-slide-up">
                    Level up your coding skills by playing {DSA_TOPICS.length} interactive games, reading annotated Python code,
                    and crushing quizzes across Arrays, Trees, Graphs, and more.
                </p>
                <div className="hero-actions animate-slide-up">
                    <Link to="/map" className="btn btn-primary">
                        <Map size={18} /> Start Adventure <ChevronRight size={16} />
                    </Link>
                    <Link to="/leaderboard" className="btn btn-secondary">
                        <Trophy size={16} /> Leaderboard
                    </Link>
                </div>

                <div className="hero-stats animate-slide-up">
                    <div className="stat-pill"><span className="stat-val">{completedModules.length}/{DSA_TOPICS.length}</span><span className="stat-lbl">Modules Done</span></div>
                    <div className="stat-divider" />
                    <div className="stat-pill"><span className="stat-val">{xp.toLocaleString()}</span><span className="stat-lbl">XP Earned</span></div>
                    <div className="stat-divider" />
                    <div className="stat-pill"><span className="stat-val">LVL {level}</span><span className="stat-lbl">Your Level</span></div>
                </div>
            </section>

            {/* ── TOPICS ── */}
            <section className="topics-section">
                <h2 className="section-title" style={{ textAlign: 'center' }}>{DSA_TOPICS.length} DSA Worlds to Conquer</h2>
                <div className="topics-grid">
                    {DSA_TOPICS.map((t, i) => (
                        <div key={i} className="topic-chip" style={{ '--chip-color': t.color, animationDelay: `${i * 0.08}s` }}>
                            <span className="topic-icon">{t.icon}</span>
                            <span className="topic-label">{t.label}</span>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── FEATURES ── */}
            <section className="features-section">
                <h2 className="section-title" style={{ textAlign: 'center' }}>Why AlgoQuest?</h2>
                <div className="features-grid">
                    {FEATURES.map((f, i) => (
                        <div key={i} className="feature-card card" style={{ animationDelay: `${i * 0.1}s` }}>
                            <div className="feature-icon">{f.icon}</div>
                            <h3 className="feature-title">{f.title}</h3>
                            <p className="feature-desc">{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── DAILY CHALLENGE ── */}
            <section className="daily-section">
                <h2 className="section-title" style={{ textAlign: 'center' }}>Quest of the Day</h2>
                <div className="daily-card glass">
                    <div className="daily-header">
                        <div className="daily-title-wrap">
                            <Calendar className="daily-icon" size={24} />
                            <h3 className="daily-title">Daily Challenge</h3>
                        </div>
                        <span className="daily-xp">+{DAILY_CHALLENGE.xp} XP</span>
                    </div>
                    <div className="daily-body">
                        <h4 className="daily-task">{DAILY_CHALLENGE.title}</h4>
                        <div className="daily-tags">
                            <span className="daily-tag" style={{ '--tag-color': '#a855f7' }}>{DAILY_CHALLENGE.topic}</span>
                            <span className="daily-tag difficulty-medium">{DAILY_CHALLENGE.difficulty}</span>
                        </div>
                        <p className="daily-desc">Solve today's handpicked algorithm challenge to maintain your streak and earn bonus experience points!</p>
                        <Link to="/map" className="btn btn-primary btn-sm" style={{ display: 'inline-flex', gap: '8px', padding: '10px 20px', fontSize: '0.9rem' }}>
                            <Code size={16} /> Play Now
                        </Link>
                    </div>
                </div>
            </section>

            {/* ── TESTIMONIALS ── */}
            <section className="testimonials-section">
                <h2 className="section-title" style={{ textAlign: 'center' }}>Wall of Fame</h2>
                <div className="testimonials-grid">
                    {TESTIMONIALS.map((t, i) => (
                        <div key={i} className="test-card glass" style={{ animationDelay: `${i * 0.15}s` }}>
                            <div className="test-stars">
                                {[...Array(t.rating)].map((_, j) => <Star key={j} size={14} fill="#facc15" color="#facc15" />)}
                            </div>
                            <p className="test-text">{t.text}</p>
                            <div className="test-author">
                                <strong>{t.name}</strong> • <span>{t.role}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── CTA ── */}
            <section className="cta-section">
                <div className="cta-card glass">
                    <h2 className="cta-title">Ready to become an <span className="cta-highlight">Algorithm Master</span>?</h2>
                    <p className="cta-sub">Pick your first world and start leveling up your Python DSA skills today!</p>
                    <Link to="/map" className="btn btn-primary" style={{ fontSize: '1rem', padding: '14px 36px' }}>
                        <Map size={20} /> Open World Map
                    </Link>
                </div>
            </section>
        </div>
    )
}
