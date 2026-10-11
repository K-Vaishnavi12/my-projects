import { useState, useCallback } from 'react'
import { useGame } from '../context/GameContext'
import { Search, RefreshCw, CheckCircle } from 'lucide-react'
import './Game.css'

function generateArray(size = 12) {
    const arr = Array.from({ length: size }, (_, i) => (i + 1) * 7 + Math.floor(Math.random() * 5))
    return [...new Set(arr)].sort((a, b) => a - b).slice(0, size)
}

export default function ArrayGame({ module: mod }) {
    const { awardXP, completeModule } = useGame()
    const [arr] = useState(generateArray)
    const [target, setTarget] = useState('')
    const [steps, setSteps] = useState([])
    const [stepIdx, setStepIdx] = useState(-1)
    const [found, setFound] = useState(null)
    const [mode, setMode] = useState('binary') // binary | linear
    const [score, setScore] = useState(0)
    const [completed, setCompleted] = useState(false)

    function runSearch() {
        const t = parseInt(target)
        if (isNaN(t)) return
        const newSteps = []

        if (mode === 'binary') {
            let left = 0, right = arr.length - 1
            while (left <= right) {
                const mid = Math.floor((left + right) / 2)
                newSteps.push({ left, right, mid, status: arr[mid] === t ? 'found' : arr[mid] < t ? 'go-right' : 'go-left' })
                if (arr[mid] === t) { setFound(mid); break }
                else if (arr[mid] < t) left = mid + 1
                else right = mid - 1
            }
            if (newSteps[newSteps.length - 1]?.status !== 'found') setFound(-1)
        } else {
            for (let i = 0; i < arr.length; i++) {
                newSteps.push({ scanIdx: i, status: arr[i] === t ? 'found' : 'scanning' })
                if (arr[i] === t) { setFound(i); break }
            }
            if (!newSteps.find(s => s.status === 'found')) setFound(-1)
        }

        setSteps(newSteps)
        setStepIdx(0)
        const pts = 20
        setScore(s => s + pts)
        awardXP(pts, 'Search completed!')
        if (!completed) { setCompleted(true); completeModule(mod.id, mod.badgeId) }
    }

    const currentStep = steps[stepIdx] ?? null

    function getCellClass(idx) {
        if (!currentStep) return ''
        if (mode === 'binary') {
            const { left, right, mid } = currentStep
            if (idx === mid) return 'cell-mid'
            if (idx >= left && idx <= right) return 'cell-active'
            return 'cell-dim'
        } else {
            if (idx === currentStep.scanIdx) return currentStep.status === 'found' ? 'cell-found' : 'cell-mid'
            if (idx < currentStep.scanIdx) return 'cell-dim'
            return ''
        }
    }

    return (
        <div className="game-container">
            <div className="game-hud">
                <div className="hud-item"><span className="hud-label">Score</span><span className="hud-val">{score}</span></div>
                <div className="hud-item"><span className="hud-label">Algorithm</span>
                    <select className="algo-select" value={mode} onChange={e => { setMode(e.target.value); setSteps([]); setStepIdx(-1); setFound(null) }}>
                        <option value="binary">Binary Search O(log n)</option>
                        <option value="linear">Linear Search O(n)</option>
                    </select>
                </div>
                <div className="hud-item"><span className="hud-label">Steps</span><span className="hud-val">{steps.length}</span></div>
            </div>

            <div className="array-display">
                {arr.map((val, idx) => (
                    <div key={idx} className={`array-cell ${getCellClass(idx)}`}>
                        <span className="cell-val">{val}</span>
                        <span className="cell-idx">{idx}</span>
                    </div>
                ))}
            </div>

            {currentStep && mode === 'binary' && (
                <div className="step-info">
                    <span className="step-badge">Mid = {currentStep.mid}</span>
                    <span className="step-badge" style={{ background: 'rgba(56,189,248,0.1)' }}>Left = {currentStep.left}</span>
                    <span className="step-badge" style={{ background: 'rgba(168,85,247,0.1)' }}>Right = {currentStep.right}</span>
                    <span className={`step-badge ${currentStep.status === 'found' ? 'badge-green' : 'badge-orange'}`}>
                        {currentStep.status === 'found' ? '✅ Found!' : currentStep.status === 'go-right' ? '→ Go Right' : '← Go Left'}
                    </span>
                </div>
            )}

            {found !== null && (
                <div className={`result-banner ${found >= 0 ? 'success' : 'fail'}`}>
                    {found >= 0 ? <><CheckCircle size={18} /> Found {target} at index [{found}] in {steps.length} step{steps.length !== 1 ? 's' : ''}!</>
                        : `❌ ${target} not found in array`}
                </div>
            )}

            <div className="game-controls">
                <input
                    className="game-input" type="number" placeholder="Enter target value..."
                    value={target} onChange={e => setTarget(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && runSearch()}
                />
                <button className="btn btn-primary" onClick={runSearch} disabled={!target}>
                    <Search size={16} /> Search
                </button>
                {steps.length > 1 && (
                    <>
                        <button className="btn btn-secondary btn-sm" onClick={() => setStepIdx(i => Math.max(0, i - 1))} disabled={stepIdx <= 0}>◀ Prev</button>
                        <button className="btn btn-secondary btn-sm" onClick={() => setStepIdx(i => Math.min(steps.length - 1, i + 1))} disabled={stepIdx >= steps.length - 1}>Next ▶</button>
                    </>
                )}
            </div>

            <div className="legend">
                <span className="legend-item"><span className="lbox cell-mid" />Middle / Scanning</span>
                <span className="legend-item"><span className="lbox cell-active" />Search Range</span>
                <span className="legend-item"><span className="lbox cell-dim" />Eliminated</span>
                <span className="legend-item"><span className="lbox cell-found" />Found</span>
            </div>

            <div className="game-tip">
                💡 <strong>Tip:</strong> Binary Search divides the array in half each step → only {Math.ceil(Math.log2(arr.length))} steps max for {arr.length} elements!
                Try values: <strong>{arr[2]}</strong>, <strong>{arr[6]}</strong>, <strong>{arr[arr.length - 1]}</strong>
            </div>
        </div>
    )
}
