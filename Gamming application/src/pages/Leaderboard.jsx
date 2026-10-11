import { useGame } from '../context/GameContext'
import { MODULES } from '../data/modules'
import { Trophy, Medal } from 'lucide-react'
import './Leaderboard.css'

function makeLeaderboard(quizScores, completedModules, xp, playerName, level) {
    const bots = [
        { name: 'PythonProwler', xp: 3200, completed: 6, level: 8 },
        { name: 'AlgoAce99', xp: 2750, completed: 5, level: 7 },
        { name: 'ByteBrawler', xp: 1980, completed: 4, level: 6 },
        { name: 'RecurseRocket', xp: 1500, completed: 4, level: 5 },
        { name: 'NodeNinja', xp: 1100, completed: 3, level: 4 },
        { name: 'HashHero', xp: 800, completed: 2, level: 3 },
        { name: 'SortSamurai', xp: 450, completed: 1, level: 2 },
        { name: 'LoopLord', xp: 200, completed: 1, level: 1 },
    ]
    const you = { name: playerName || 'You', xp, completed: completedModules.length, level, isYou: true }
    return [...bots, you].sort((a, b) => b.xp - a.xp).map((p, i) => ({ ...p, rank: i + 1 }))
}

const RANK_COLORS = ['#facc15', '#c0c0c0', '#cd7f32']

export default function Leaderboard() {
    const { playerName, xp, level, completedModules, quizScores } = useGame()
    const board = makeLeaderboard(quizScores, completedModules, xp, playerName, level)
    const yourEntry = board.find(p => p.isYou)

    return (
        <div className="leaderboard-page">
            <div className="stars-bg" />
            <div className="lb-header">
                <h1 className="section-title" style={{ fontSize: '2rem' }}>🏆 Leaderboard</h1>
                <p style={{ color: 'var(--text-secondary)' }}>Compete with other AlgoQuesters. Your rank updates as you earn XP!</p>
                {yourEntry && (
                    <div className="your-rank-pill">
                        Your Rank: <strong>#{yourEntry.rank}</strong> — {yourEntry.xp.toLocaleString()} XP
                    </div>
                )}
            </div>

            <div className="lb-table card">
                <div className="lb-row lb-thead">
                    <span>#</span><span>Player</span><span>Level</span><span>Worlds</span><span>XP</span>
                </div>
                {board.map(p => (
                    <div key={p.rank} className={`lb-row ${p.isYou ? 'lb-you' : ''} ${p.rank <= 3 ? 'lb-top' : ''}`}>
                        <span className="lb-rank">
                            {p.rank <= 3
                                ? <span style={{ color: RANK_COLORS[p.rank - 1], fontSize: '1.2rem' }}>
                                    {p.rank === 1 ? '🥇' : p.rank === 2 ? '🥈' : '🥉'}
                                </span>
                                : <span className="rank-num">#{p.rank}</span>}
                        </span>
                        <span className="lb-name">
                            <div className="lb-avatar">{p.name[0]}</div>
                            {p.name} {p.isYou && <span className="you-tag">YOU</span>}
                        </span>
                        <span className="lb-level"><span className="level-pill">LVL {p.level}</span></span>
                        <span className="lb-worlds">{p.completed}/6</span>
                        <span className="lb-xp">{p.xp.toLocaleString()} <span style={{ color: 'var(--neon-yellow)', fontSize: '0.7rem' }}>XP</span></span>
                    </div>
                ))}
            </div>
        </div>
    )
}
