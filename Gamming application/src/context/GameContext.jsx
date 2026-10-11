import { createContext, useContext, useState, useEffect } from 'react'

const GameContext = createContext()

const BADGES = [
    { id: 'array_master', name: 'Array Master', icon: '🔢', desc: 'Complete the Arrays module', xp: 100 },
    { id: 'chain_builder', name: 'Chain Builder', icon: '🔗', desc: 'Complete Linked Lists module', xp: 150 },
    { id: 'stack_lord', name: 'Stack Lord', icon: '📚', desc: 'Complete Stacks & Queues module', xp: 150 },
    { id: 'tree_climber', name: 'Tree Climber', icon: '🌳', desc: 'Complete the Trees module', xp: 200 },
    { id: 'sort_racer', name: 'Sort Racer', icon: '⚡', desc: 'Complete the Sorting module', xp: 200 },
    { id: 'maze_explorer', name: 'Maze Explorer', icon: '🗺️', desc: 'Complete the Graphs module', xp: 250 },
    { id: 'quiz_whiz', name: 'Quiz Whiz', icon: '🧠', desc: 'Score 100% on any quiz', xp: 100 },
    { id: 'algo_master', name: 'AlgoQuest Master', icon: '👑', desc: 'Complete all 6 modules', xp: 500 },
]

const LEVEL_THRESHOLDS = [0, 100, 250, 500, 900, 1400, 2100, 3000, 4200, 6000, 10000]

function getLevel(xp) {
    let level = 1
    for (let i = 0; i < LEVEL_THRESHOLDS.length; i++) {
        if (xp >= LEVEL_THRESHOLDS[i]) level = i + 1
        else break
    }
    return level
}

function getXPForNextLevel(xp) {
    const level = getLevel(xp)
    const next = LEVEL_THRESHOLDS[level] ?? LEVEL_THRESHOLDS[LEVEL_THRESHOLDS.length - 1]
    const prev = LEVEL_THRESHOLDS[level - 1] ?? 0
    return { current: xp - prev, needed: next - prev, next }
}

export function GameProvider({ children }) {
    const [playerName, setPlayerName] = useState(() => localStorage.getItem('aq_name') || 'Player One')
    const [xp, setXp] = useState(() => parseInt(localStorage.getItem('aq_xp') || '0'))
    const [completedModules, setCompletedModules] = useState(() => JSON.parse(localStorage.getItem('aq_completed') || '[]'))
    const [earnedBadges, setEarnedBadges] = useState(() => JSON.parse(localStorage.getItem('aq_badges') || '[]'))
    const [quizScores, setQuizScores] = useState(() => JSON.parse(localStorage.getItem('aq_quiz') || '{}'))
    const [streak, setStreak] = useState(() => parseInt(localStorage.getItem('aq_streak') || '0'))
    const [xpToast, setXpToast] = useState(null)

    useEffect(() => { localStorage.setItem('aq_xp', xp) }, [xp])
    useEffect(() => { localStorage.setItem('aq_completed', JSON.stringify(completedModules)) }, [completedModules])
    useEffect(() => { localStorage.setItem('aq_badges', JSON.stringify(earnedBadges)) }, [earnedBadges])
    useEffect(() => { localStorage.setItem('aq_quiz', JSON.stringify(quizScores)) }, [quizScores])
    useEffect(() => { localStorage.setItem('aq_name', playerName) }, [playerName])

    function showXpToast(amount, label) {
        setXpToast({ amount, label })
        setTimeout(() => setXpToast(null), 2500)
    }

    function awardXP(amount, reason) {
        setXp(prev => prev + amount)
        showXpToast(amount, reason)
    }

    function completeModule(moduleId, badgeId) {
        if (!completedModules.includes(moduleId)) {
            setCompletedModules(prev => {
                const updated = [...prev, moduleId]
                if (updated.length === 6 && !earnedBadges.includes('algo_master')) {
                    awardXP(500, 'AlgoQuest Master!')
                    setEarnedBadges(b => [...b, 'algo_master'])
                }
                return updated
            })
        }
        if (badgeId && !earnedBadges.includes(badgeId)) {
            setEarnedBadges(prev => [...prev, badgeId])
            const badge = BADGES.find(b => b.id === badgeId)
            if (badge) awardXP(badge.xp, `Badge: ${badge.name}`)
        }
    }

    function saveQuizScore(moduleId, score, total) {
        const newScore = { score, total, pct: Math.round((score / total) * 100) }
        setQuizScores(prev => {
            const existing = prev[moduleId]
            if (!existing || newScore.pct > existing.pct) {
                if (newScore.pct === 100 && !earnedBadges.includes('quiz_whiz')) {
                    setEarnedBadges(b => [...b, 'quiz_whiz'])
                    awardXP(100, 'Quiz Whiz!')
                }
                const xpEarned = Math.round((newScore.pct / 100) * 50)
                awardXP(xpEarned, `Quiz: +${xpEarned} XP`)
                return { ...prev, [moduleId]: newScore }
            }
            return prev
        })
    }

    const level = getLevel(xp)
    const xpProgress = getXPForNextLevel(xp)

    return (
        <GameContext.Provider value={{
            playerName, setPlayerName,
            xp, awardXP,
            completedModules, completeModule,
            earnedBadges,
            quizScores, saveQuizScore,
            streak,
            level, xpProgress,
            BADGES,
            xpToast,
        }}>
            {children}
            {xpToast && (
                <div className="xp-toast">
                    ⚡ +{xpToast.amount} XP — {xpToast.label}
                </div>
            )}
        </GameContext.Provider>
    )
}

export function useGame() { return useContext(GameContext) }
