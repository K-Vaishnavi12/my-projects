import { useState, useRef } from 'react'
import { useGame } from '../context/GameContext'
import { Play, RotateCcw } from 'lucide-react'
import './Game.css'

const ROWS = 9, COLS = 15

function buildMaze() {
    // Build a maze with walls and paths
    const grid = Array.from({ length: ROWS }, (_, r) =>
        Array.from({ length: COLS }, (_, c) => {
            if (r === 0 || r === ROWS - 1 || c === 0 || c === COLS - 1) return 'wall'
            if (r % 2 === 0 && c % 2 === 0) return 'wall'
            if (Math.random() < 0.25) return 'wall'
            return 'open'
        })
    )
    grid[1][1] = 'open'; grid[ROWS - 2][COLS - 2] = 'open'
    return grid
}

const DIRECTIONS = [[0, 1], [1, 0], [0, -1], [-1, 0]]

export default function GraphGame({ module: mod }) {
    const { awardXP, completeModule } = useGame()
    const [grid, setGrid] = useState(buildMaze)
    const [visited, setVisited] = useState(new Set())
    const [path, setPath] = useState(new Set())
    const [algo, setAlgo] = useState('bfs')
    const [running, setRunning] = useState(false)
    const [score, setScore] = useState(0)
    const [msg, setMsg] = useState('')
    const [completed, setCompleted] = useState(false)
    const timerRef = useRef(null)
    const START = '1,1', GOAL = `${ROWS - 2},${COLS - 2}`

    function flash(m) { setMsg(m); setTimeout(() => setMsg(''), 3000) }
    function key(r, c) { return `${r},${c}` }
    function parseKey(k) { return k.split(',').map(Number) }
    function isOpen(r, c) {
        if (r < 0 || r >= ROWS || c < 0 || c >= COLS) return false
        return grid[r][c] !== 'wall'
    }

    function runAlgo() {
        if (running) return
        setRunning(true); setVisited(new Set()); setPath(new Set()); setMsg('')
        const steps = []
        const [sr, sc] = parseKey(START)
        const [gr, gc] = parseKey(GOAL)
        const visitedSet = new Set([START])
        const prev = {}

        if (algo === 'bfs') {
            const queue = [[sr, sc]]
            while (queue.length) {
                const [r, c] = queue.shift()
                steps.push({ type: 'visit', k: key(r, c) })
                if (r === gr && c === gc) { steps.push({ type: 'done' }); break }
                for (const [dr, dc] of DIRECTIONS) {
                    const nr = r + dr, nc = c + dc, nk = key(nr, nc)
                    if (isOpen(nr, nc) && !visitedSet.has(nk)) {
                        visitedSet.add(nk); prev[nk] = key(r, c); queue.push([nr, nc])
                    }
                }
            }
        } else {
            // DFS
            const stack = [[sr, sc]]
            while (stack.length) {
                const [r, c] = stack.pop()
                if (visitedSet.has(key(r, c)) && key(r, c) !== START) { visitedSet.add(key(r, c)); continue }
                visitedSet.add(key(r, c))
                steps.push({ type: 'visit', k: key(r, c) })
                if (r === gr && c === gc) { steps.push({ type: 'done' }); break }
                for (const [dr, dc] of DIRECTIONS) {
                    const nr = r + dr, nc = c + dc, nk = key(nr, nc)
                    if (isOpen(nr, nc) && !visitedSet.has(nk)) {
                        prev[nk] = key(r, c); stack.push([nr, nc])
                    }
                }
            }
        }

        // Trace path back
        let cur = GOAL
        const pathSet = new Set()
        while (cur && cur !== START) { pathSet.add(cur); cur = prev[cur] }
        pathSet.add(START)

        let i = 0
        const vis = new Set()
        timerRef.current = setInterval(() => {
            if (i >= steps.length) {
                clearInterval(timerRef.current); setRunning(false)
                setPath(pathSet)
                const pts = algo === 'bfs' ? 25 : 20
                setScore(s => s + pts); awardXP(pts, `${algo.toUpperCase()} Solved!`)
                flash(`${algo.toUpperCase()} found the path! ${pathSet.size} cells in path, ${vis.size} cells explored.`)
                if (!completed) { setCompleted(true); completeModule(mod.id, mod.badgeId) }
                return
            }
            const step = steps[i++]
            if (step.type === 'visit') { vis.add(step.k); setVisited(new Set(vis)) }
        }, 60)
    }

    function reset() {
        clearInterval(timerRef.current); setRunning(false)
        setGrid(buildMaze()); setVisited(new Set()); setPath(new Set()); setMsg('')
    }

    function cellClass(r, c) {
        const k = key(r, c)
        if (k === START) return 'start'
        if (k === GOAL) return 'goal'
        if (grid[r][c] === 'wall') return 'wall'
        if (path.has(k)) return 'path'
        if (visited.has(k)) return 'visited'
        return 'open'
    }

    function cellChar(r, c) {
        const k = key(r, c)
        if (k === START) return '🟦'
        if (k === GOAL) return '🏆'
        if (path.has(k)) return '·'
        return ''
    }

    return (
        <div className="game-container">
            <div className="game-hud">
                <div className="hud-item"><span className="hud-label">Score</span><span className="hud-val">{score}</span></div>
                <div className="hud-item">
                    <span className="hud-label">Algorithm</span>
                    <div style={{ display: 'flex', gap: 6, marginTop: 2 }}>
                        {['bfs', 'dfs'].map(a => (
                            <button key={a} className={`btn btn-sm ${algo === a ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => { if (!running) { setAlgo(a); setVisited(new Set()); setPath(new Set()) } }}
                                style={{ padding: '4px 14px', fontSize: '0.75rem', fontFamily: 'var(--font-game)' }}>
                                {a === 'bfs' ? 'BFS (Queue)' : 'DFS (Stack)'}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {msg && <div className="result-banner success">{msg}</div>}

            <p className="game-section-title">
                🟦 = Start &nbsp;&nbsp; 🏆 = Goal &nbsp;&nbsp;
                <span style={{ color: 'var(--neon-blue)' }}>■ Explored</span> &nbsp;&nbsp;
                <span style={{ color: 'var(--neon-green)' }}>· Path Found</span>
            </p>

            <div style={{ display: 'flex', justifyContent: 'center', overflowX: 'auto', paddingBottom: 8 }}>
                <div className="maze-grid" style={{ gridTemplateColumns: `repeat(${COLS}, 36px)` }}>
                    {Array.from({ length: ROWS }, (_, r) =>
                        Array.from({ length: COLS }, (_, c) => (
                            <div key={`${r}-${c}`} className={`maze-cell ${cellClass(r, c)}`}>
                                {cellChar(r, c)}
                            </div>
                        ))
                    )}
                </div>
            </div>

            <div className="game-controls">
                <button className="btn btn-primary" onClick={runAlgo} disabled={running}>
                    <Play size={16} /> {running ? 'Exploring...' : `Run ${algo.toUpperCase()}`}
                </button>
                <button className="btn btn-secondary" onClick={reset}><RotateCcw size={16} /> New Maze</button>
            </div>

            <div className="game-tip">
                💡 <strong>BFS</strong> uses a Queue → finds the <em>shortest</em> path. <strong>DFS</strong> uses a Stack/Recursion → goes deep before backtracking.
                Both are O(V+E) where V = cells, E = connections.
            </div>
        </div>
    )
}
