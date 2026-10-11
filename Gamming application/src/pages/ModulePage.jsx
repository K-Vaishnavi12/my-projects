import { useParams, Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { ArrowLeft, Trophy } from 'lucide-react'
import { MODULES } from '../data/modules'
import { PYTHON_CODE } from '../data/pythonCode'
import { useGame } from '../context/GameContext'
import CodeViewer from '../components/CodeViewer'
import QuizPanel from '../components/QuizPanel'
import '../components/QuizPanel.css'
import ArrayGame from '../games/ArrayGame'
import LinkedListGame from '../games/LinkedListGame'
import StackQueueGame from '../games/StackQueueGame'
import TreeGame from '../games/TreeGame'
import SortingGame from '../games/SortingGame'
import GraphGame from '../games/GraphGame'
import './ModulePage.css'

const GAME_MAP = {
    'arrays': ArrayGame,
    'linked-lists': LinkedListGame,
    'stacks': StackQueueGame,
    'trees': TreeGame,
    'sorting': SortingGame,
    'graphs': GraphGame,
}

const CODE_MAP = {
    'arrays': 'arrays',
    'linked-lists': 'linked_lists',
    'stacks': 'stacks',
    'trees': 'trees',
    'sorting': 'sorting',
    'graphs': 'graphs',
}

const TABS = ['🎮 Play', '🐍 Code', '🧠 Quiz']

export default function ModulePage() {
    const { id } = useParams()
    const navigate = useNavigate()
    const mod = MODULES.find(m => m.id === id)
    const [tab, setTab] = useState(0)
    const { completedModules, quizScores } = useGame()

    if (!mod) return (
        <div style={{ textAlign: 'center', padding: 80 }}>
            <h2>Module not found</h2>
            <Link to="/map" className="btn btn-primary" style={{ marginTop: 24 }}>Back to Map</Link>
        </div>
    )

    const GameComponent = GAME_MAP[id]
    const codeKey = CODE_MAP[id]
    const score = quizScores[id]
    const completed = completedModules.includes(id)

    return (
        <div className="module-page">
            <div className="mp-header" style={{ '--mod-color': mod.color, '--mod-glow': mod.glowColor }}>
                <button className="back-btn" onClick={() => navigate('/map')}>
                    <ArrowLeft size={18} /> Back
                </button>
                <div className="mp-title-row">
                    <div className="mp-icon" style={{ background: mod.gradient }}>{mod.icon}</div>
                    <div>
                        <div className={`badge ${mod.difficulty === 'Beginner' ? 'badge-green' :
                                mod.difficulty === 'Intermediate' ? 'badge-orange' : 'badge-purple'
                            }`} style={{ marginBottom: 6 }}>{mod.difficulty}</div>
                        <h1 className="mp-title">{mod.title}</h1>
                        <p className="mp-desc">{mod.description}</p>
                    </div>
                </div>
                <div className="mp-meta">
                    <span>⚡ +{mod.xpReward} XP reward</span>
                    {score && <span><Trophy size={14} color="var(--neon-yellow)" /> Best Quiz: {score.pct}%</span>}
                    {completed && <span style={{ color: 'var(--neon-green)' }}>✅ Completed</span>}
                </div>
            </div>

            <div className="mp-body">
                <div className="tab-bar">
                    {TABS.map((t, i) => (
                        <button key={i} className={`tab-btn ${tab === i ? 'active' : ''}`} onClick={() => setTab(i)}>
                            {t}
                        </button>
                    ))}
                </div>

                <div className="tab-content">
                    {tab === 0 && GameComponent && <GameComponent module={mod} />}
                    {tab === 1 && (
                        <div>
                            <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>
                                Annotated Python code for <strong>{mod.title}</strong> with complexity analysis.
                            </p>
                            <CodeViewer code={PYTHON_CODE[codeKey] || '# Code coming soon!'} />
                        </div>
                    )}
                    {tab === 2 && (
                        <QuizPanel questions={mod.quiz} moduleId={mod.id} />
                    )}
                </div>
            </div>
        </div>
    )
}
