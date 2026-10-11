import { useState, useRef, useEffect } from 'react'
import { useGame } from '../context/GameContext'
import { Play, RotateCcw } from 'lucide-react'
import './Game.css'

const ALGOS = [
    { id: 'bubble', name: 'Bubble Sort', color: '#38bdf8', complexity: 'O(n²)' },
    { id: 'selection', name: 'Selection Sort', color: '#a855f7', complexity: 'O(n²)' },
    { id: 'merge', name: 'Merge Sort', color: '#22d3a0', complexity: 'O(n log n)' },
    { id: 'quick', name: 'Quick Sort', color: '#facc15', complexity: 'O(n log n)' },
]

function generateBars(n = 18) {
    return Array.from({ length: n }, () => Math.floor(Math.random() * 90) + 10)
}

function* bubbleGen(arr) {
    const a = [...arr]; const n = a.length
    for (let i = 0; i < n; i++) {
        for (let j = 0; j < n - i - 1; j++) {
            yield { arr: [...a], comparing: [j, j + 1] }
            if (a[j] > a[j + 1]) { [a[j], a[j + 1]] = [a[j + 1], a[j]]; yield { arr: [...a], swapping: [j, j + 1] } }
        }
        yield { arr: [...a], sorted: Array.from({ length: i + 1 }, (_, k) => n - 1 - k) }
    }
    yield { arr: [...a], done: true }
}

function* selectionGen(arr) {
    const a = [...arr]; const n = a.length; const sorted = []
    for (let i = 0; i < n; i++) {
        let min = i
        for (let j = i + 1; j < n; j++) { yield { arr: [...a], comparing: [min, j] }; if (a[j] < a[min]) min = j }
        if (min !== i) { [a[i], a[min]] = [a[min], a[i]]; yield { arr: [...a], swapping: [i, min] } }
        sorted.push(i)
        yield { arr: [...a], sorted: [...sorted] }
    }
    yield { arr: [...a], done: true }
}

function* mergeGen(arr) {
    const a = [...arr]
    yield* mergeHelper(a, 0, a.length - 1)
    yield { arr: [...a], done: true }
}
function* mergeHelper(a, l, r) {
    if (l >= r) return
    const m = Math.floor((l + r) / 2)
    yield* mergeHelper(a, l, m)
    yield* mergeHelper(a, m + 1, r)
    const left = a.slice(l, m + 1), right = a.slice(m + 1, r + 1)
    let i = 0, j = 0, k = l
    while (i < left.length && j < right.length) {
        yield { arr: [...a], comparing: [k, l + i < m + 1 ? l + i : m + 1 + j] }
        if (left[i] <= right[j]) a[k++] = left[i++]
        else a[k++] = right[j++]
        yield { arr: [...a], swapping: [k - 1] }
    }
    while (i < left.length) { a[k++] = left[i++]; yield { arr: [...a] } }
    while (j < right.length) { a[k++] = right[j++]; yield { arr: [...a] } }
}

function* quickGen(arr) {
    const a = [...arr]
    yield* quickHelper(a, 0, a.length - 1)
    yield { arr: [...a], done: true }
}
function* quickHelper(a, l, r) {
    if (l >= r) return
    const pivot = a[r]; let i = l
    for (let j = l; j < r; j++) {
        yield { arr: [...a], comparing: [j, r] }
        if (a[j] <= pivot) { [a[i], a[j]] = [a[j], a[i]]; yield { arr: [...a], swapping: [i, j] }; i++ }
    }
    [a[i], a[r]] = [a[r], a[i]]; yield { arr: [...a], swapping: [i] }
    yield* quickHelper(a, l, i - 1)
    yield* quickHelper(a, i + 1, r)
}

const GEN_MAP = { bubble: bubbleGen, selection: selectionGen, merge: mergeGen, quick: quickGen }

export default function SortingGame({ module: mod }) {
    const { awardXP, completeModule } = useGame()
    const [bars, setBars] = useState(generateBars)
    const [selected, setSelected] = useState('bubble')
    const [frame, setFrame] = useState(null)
    const [running, setRunning] = useState(false)
    const [score, setScore] = useState(0)
    const [completed, setCompleted] = useState(false)
    const [speed, setSpeed] = useState(60)
    const genRef = useRef(null)
    const timerRef = useRef(null)

    function reset() {
        clearInterval(timerRef.current); setRunning(false)
        setBars(generateBars()); setFrame(null)
    }

    function run() {
        if (running) { clearInterval(timerRef.current); setRunning(false); return }
        genRef.current = GEN_MAP[selected](bars)
        setRunning(true)
        timerRef.current = setInterval(() => {
            const { value, done } = genRef.current.next()
            if (done || value?.done) {
                clearInterval(timerRef.current); setRunning(false)
                setFrame({ arr: value?.arr ?? bars, done: true })
                const pts = 30; setScore(s => s + pts); awardXP(pts, `${selected} Sort done!`)
                if (!completed) { setCompleted(true); completeModule(mod.id, mod.badgeId) }
            } else {
                setFrame(value)
                if (value?.arr) setBars(value.arr)
            }
        }, speed)
    }

    useEffect(() => () => clearInterval(timerRef.current), [])

    const algo = ALGOS.find(a => a.id === selected)

    return (
        <div className="game-container">
            <div className="game-hud">
                <div className="hud-item"><span className="hud-label">Score</span><span className="hud-val">{score}</span></div>
                <div className="hud-item">
                    <span className="hud-label">Algorithm</span>
                    <select className="algo-select" value={selected} onChange={e => { setSelected(e.target.value); reset() }} disabled={running}>
                        {ALGOS.map(a => <option key={a.id} value={a.id}>{a.name} {a.complexity}</option>)}
                    </select>
                </div>
                <div className="hud-item">
                    <span className="hud-label">Speed</span>
                    <input type="range" min="20" max="200" value={speed} onChange={e => setSpeed(Number(e.target.value))}
                        style={{ width: 80 }} />
                </div>
                {frame?.done && <span className="badge badge-green">✅ Sorted!</span>}
            </div>

            <p className="game-section-title">SORTING VISUALIZATION — {algo?.name} ({algo?.complexity})</p>
            <div className="sort-display">
                {bars.map((h, i) => {
                    let cls = 'sort-bar'
                    if (frame?.comparing?.includes(i)) cls += ' comparing'
                    else if (frame?.swapping?.includes(i)) cls += ' swapping'
                    else if (frame?.sorted?.includes(i)) cls += ' sorted'
                    else if (frame?.done) cls += ' sorted'
                    return (
                        <div key={i} className={cls}
                            style={{ height: `${h}%`, background: frame?.done ? 'var(--neon-green)' : algo?.color }}
                        />
                    )
                })}
            </div>

            <div className="game-controls">
                <button className="btn btn-primary" onClick={run}>
                    <Play size={16} /> {running ? 'Pause ⏸' : 'Start Race ▶'}
                </button>
                <button className="btn btn-secondary" onClick={reset}><RotateCcw size={16} /> New Array</button>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {ALGOS.map(a => (
                        <span key={a.id} className={`badge ${selected === a.id ? 'badge-blue' : 'badge-purple'}`}
                            style={{ cursor: 'pointer' }} onClick={() => { if (!running) { setSelected(a.id); reset() } }}>
                            {a.name}
                        </span>
                    ))}
                </div>
            </div>

            <div className="legend">
                <span className="legend-item"><span className="lbox" style={{ background: 'var(--neon-yellow)' }} />Comparing</span>
                <span className="legend-item"><span className="lbox" style={{ background: 'var(--neon-red)' }} />Swapping</span>
                <span className="legend-item"><span className="lbox" style={{ background: 'var(--neon-green)' }} />Sorted</span>
            </div>

            <div className="game-tip">
                💡 Merge Sort and Quick Sort are O(n log n) — much faster than Bubble/Selection O(n²) for large arrays. Watch the number of operations!
            </div>
        </div>
    )
}
