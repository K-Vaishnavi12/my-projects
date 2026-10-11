import { useGame } from '../context/GameContext'
import { MODULES } from '../data/modules'
import { Link } from 'react-router-dom'
import { Zap, Star, Trophy, Flame } from 'lucide-react'
import './Profile.css'

const LEVEL_TITLES = [
    'Novice Coder', 'Array Apprentice', 'Loop Learner', 'Stack Scholar',
    'Tree Trekker', 'Graph Guru', 'Sort Sage', 'DSA Wizard',
    'Algorithm Ace', 'AlgoQuest Legend'
]

export default function Profile() {
    const { playerName, setPlayerName, xp, level, xpProgress, completedModules, earnedBadges, quizScores, streak, BADGES } = useGame()

    return (
        <div className="profile-page">
            <div className="stars-bg" />

            {/* ── HERO CARD ── */}
            <div className="profile-hero card">
                <div className="avatar">{playerName?.[0]?.toUpperCase() || 'P'}</div>
                <div className="profile-info">
                    <input
                        className="name-input"
                        value={playerName}
                        onChange={e => setPlayerName(e.target.value)}
                        maxLength={20}
                        placeholder="Your name"
                    />
                    <p className="level-title">{LEVEL_TITLES[Math.min(level - 1, LEVEL_TITLES.length - 1)]}</p>
                    <div className="xp-bar-wrap">
                        <div className="xp-bar-label">
                            <span>Level {level}</span>
                            <span>{xpProgress.current} / {xpProgress.needed} XP</span>
                        </div>
                        <div className="progress-track">
                            <div className="progress-fill" style={{ width: `${Math.min((xpProgress.current / xpProgress.needed) * 100, 100)}%`, height: 10 }} />
                        </div>
                        <p className="xp-hint">Level {level + 1} at {xpProgress.next} total XP</p>
                    </div>
                </div>
                <div className="profile-stats">
                    <div className="pstat"><Zap size={20} color="var(--neon-yellow)" /><span className="pstat-val">{xp.toLocaleString()}</span><span className="pstat-lbl">Total XP</span></div>
                    <div className="pstat"><Star size={20} color="var(--neon-blue)" /><span className="pstat-val">{completedModules.length}/6</span><span className="pstat-lbl">Worlds</span></div>
                    <div className="pstat"><Trophy size={20} color="var(--neon-purple)" /><span className="pstat-val">{earnedBadges.length}</span><span className="pstat-lbl">Badges</span></div>
                    <div className="pstat"><Flame size={20} color="var(--neon-orange)" /><span className="pstat-val">{streak}</span><span className="pstat-lbl">Streak</span></div>
                </div>
            </div>

            <div className="profile-grid">
                {/* ── MODULES PROGRESS ── */}
                <div className="card">
                    <h2 className="section-title" style={{ fontSize: '1.1rem' }}>Module Progress</h2>
                    {MODULES.map(mod => {
                        const done = completedModules.includes(mod.id)
                        const score = quizScores[mod.id]
                        return (
                            <div key={mod.id} className="mod-row">
                                <span className="mod-row-icon" style={{ background: mod.gradient }}>{mod.icon}</span>
                                <div className="mod-row-info">
                                    <span className="mod-row-name">{mod.title}</span>
                                    {score && <span className="mod-row-score">Quiz: {score.pct}%</span>}
                                </div>
                                <span className={`mod-row-status ${done ? 'done' : 'pending'}`}>
                                    {done ? '✅ Done' : '⏳ Pending'}
                                </span>
                                <Link to={`/module/${mod.id}`} className="btn btn-secondary btn-sm">
                                    {done ? 'Replay' : 'Play'}
                                </Link>
                            </div>
                        )
                    })}
                </div>

                {/* ── BADGES ── */}
                <div className="card">
                    <h2 className="section-title" style={{ fontSize: '1.1rem' }}>Badges</h2>
                    <div className="badges-grid">
                        {BADGES.map(badge => {
                            const earned = earnedBadges.includes(badge.id)
                            return (
                                <div key={badge.id} className={`badge-card ${earned ? 'earned' : 'locked-badge'}`}>
                                    <div className="badge-icon">{badge.icon}</div>
                                    <div className="badge-name">{badge.name}</div>
                                    <div className="badge-desc">{badge.desc}</div>
                                    <div className="badge-xp">+{badge.xp} XP</div>
                                    {!earned && <div className="badge-lock-overlay">🔒</div>}
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>
        </div>
    )
}
