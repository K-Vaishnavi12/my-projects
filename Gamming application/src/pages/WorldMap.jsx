import { Link } from 'react-router-dom'
import { useGame } from '../context/GameContext'
import { MODULES } from '../data/modules'
import { Lock, CheckCircle, ChevronRight, Star } from 'lucide-react'
import mascot from '../assets/mascot_stick.png'
import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import './WorldMap.css'

export default function WorldMap() {
    const { completedModules, xp, playerName } = useGame()
    const location = useLocation()
    const navigate = useNavigate()
    const [mascotMsg, setMascotMsg] = useState("Hey, hi! Ready to conquer some algorithms today?")
    const [showWelcome, setShowWelcome] = useState(location.state?.justLoggedIn || false)
    const [navigatingToQuiz, setNavigatingToQuiz] = useState(false)

    useEffect(() => {
        const messages = [
            "Hey, hi! Ready to conquer some algorithms today?",
            "How is the day going? Let's solve some problems!",
            "Don't forget to check out the quizzes to earn extra XP!",
            "You're doing great! Keep up the good work!",
            "Need help? Take your time to review the concepts!"
        ]
        const interval = setInterval(() => {
            setMascotMsg(messages[Math.floor(Math.random() * messages.length)])
        }, 8000)
        return () => clearInterval(interval)
    }, [])

    function isUnlocked(idx) {
        if (idx === 0) return true
        return completedModules.includes(MODULES[idx - 1].id)
    }

    const handleQuizClick = (e, moduleId) => {
        e.preventDefault()
        setNavigatingToQuiz(true)
        setTimeout(() => {
            navigate(`/quiz/${moduleId}`)
        }, 2000)
    }

    return (
        <div className="worldmap">
            <div className="stars-bg" />

            {/* Mascot Popup */}
            {!showWelcome && !navigatingToQuiz && (
                <div className="floating-mascot">
                    <div className="mascot-bubble" key={mascotMsg}>{mascotMsg}</div>
                    <img src={mascot} alt="Mascot" className="path-mascot hover-bounce" />
                </div>
            )}

            {/* Login Welcome Overlay */}
            {showWelcome && (
                <div className="welcome-overlay">
                    <div className="welcome-popup animate-slide-up">
                        <img src={mascot} alt="Mascot" className="welcome-mascot float-anim" />
                        <div className="welcome-content">
                            <h2>Hi, {playerName}! 👋</h2>
                            <p>Ready to conquer some algorithms today and earn new badges?</p>
                            <div className="welcome-actions">
                                <button className="btn btn-primary" onClick={() => setShowWelcome(false)}>Start Learning</button>
                                <button className="btn btn-secondary" onClick={() => navigate('/leaderboard')}>View Leaderboard</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Quiz Navigation Overlay */}
            {navigatingToQuiz && (
                <div className="quiz-nav-overlay">
                    <div className="quiz-nav-anim">
                        <img src={mascot} alt="Mascot Flying" className="nav-mascot-img" />
                        <h2>Navigating to Quiz Sector...</h2>
                    </div>
                </div>
            )}

            <div className="wm-header">
                <h1 className="section-title" style={{ fontSize: '2rem', marginBottom: 8 }}>🗺️ World Map</h1>
                <p style={{ color: 'var(--text-secondary)' }}>Complete each world to unlock the next. Earn XP and badges!</p>
                <div className="wm-progress-bar">
                    <div className="wm-pb-fill" style={{ width: `${(completedModules.length / MODULES.length) * 100}%` }} />
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: 6 }}>
                    {completedModules.length} / {MODULES.length} Worlds Completed
                </p>
            </div>

            <div className="modules-grid">
                {MODULES.map((mod, idx) => {
                    const unlocked = isUnlocked(idx)
                    const completed = completedModules.includes(mod.id)
                    return (
                        <div
                            key={mod.id}
                            className={`module-card card ${completed ? 'completed' : ''} ${!unlocked ? 'locked' : ''}`}
                            style={{ '--mod-color': mod.color, '--mod-glow': mod.glowColor, animationDelay: `${idx * 0.1}s` }}
                        >
                            <div className="module-header">
                                <div className="module-icon-wrap" style={{ background: mod.gradient }}>
                                    <span className="module-icon">{mod.icon}</span>
                                </div>
                                <div className="module-status-icon">
                                    {completed ? <CheckCircle size={22} color="var(--neon-green)" /> :
                                        !unlocked ? <Lock size={18} color="var(--text-muted)" /> :
                                            <Star size={18} color={mod.color} />}
                                </div>
                            </div>
                            <div className={`diff-badge badge ${mod.difficulty === 'Beginner' ? 'badge-green' :
                                mod.difficulty === 'Intermediate' ? 'badge-orange' : 'badge-purple'
                                }`}>{mod.difficulty}</div>
                            <h3 className="module-title">{mod.title}</h3>
                            <p className="module-desc">{mod.description}</p>
                            <div className="module-concepts">
                                {mod.concepts.map((c, ci) => (
                                    <span key={ci} className="concept-tag">{c}</span>
                                ))}
                            </div>
                            <div className="module-footer">
                                <span className="module-xp">⚡ +{mod.xpReward} XP</span>
                                {unlocked ? (
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <Link to={`/module/${mod.id}`} className="btn btn-primary btn-sm">
                                            {completed ? 'Replay' : 'Play'} <ChevronRight size={14} />
                                        </Link>
                                        <button
                                            onClick={(e) => handleQuizClick(e, mod.id)}
                                            className="btn btn-secondary btn-sm"
                                            style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                                        >
                                            Quiz
                                        </button>
                                    </div>
                                ) : (
                                    <button className="btn btn-secondary btn-sm" disabled style={{ opacity: 0.5, cursor: 'not-allowed' }}>
                                        <Lock size={12} /> Locked
                                    </button>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
