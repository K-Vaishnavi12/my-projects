import { useState } from 'react'
import { useGame } from '../context/GameContext'
import { Plus, Trash2, Search, RotateCcw } from 'lucide-react'
import './Game.css'

export default function LinkedListGame({ module: mod }) {
    const { awardXP, completeModule } = useGame()
    const [nodes, setNodes] = useState([10, 20, 30, 40])
    const [inputVal, setInputVal] = useState('')
    const [searchVal, setSearchVal] = useState('')
    const [highlighted, setHighlighted] = useState(null)
    const [score, setScore] = useState(0)
    const [completed, setCompleted] = useState(false)
    const [msg, setMsg] = useState('')

    function flash(msg) { setMsg(msg); setTimeout(() => setMsg(''), 2500) }

    function prepend() {
        const v = parseInt(inputVal); if (isNaN(v)) return
        setNodes(n => [v, ...n])
        xpAction(10, `Prepend O(1) → ${v}`)
        flash(`Prepended ${v} at head!`)
        setInputVal('')
    }

    function append() {
        const v = parseInt(inputVal); if (isNaN(v)) return
        setNodes(n => [...n, v])
        xpAction(10, `Append O(n) → ${v}`)
        flash(`Appended ${v} at tail!`)
        setInputVal('')
    }

    function deleteNode(i) {
        setNodes(n => n.filter((_, idx) => idx !== i))
        xpAction(10, 'Delete O(n)')
        flash(`Deleted node at index ${i}!`)
    }

    function searchNode() {
        const v = parseInt(searchVal); if (isNaN(v)) return
        const idx = nodes.indexOf(v)
        setHighlighted(idx)
        flash(idx >= 0 ? `Found ${v} at index ${idx} ✅` : `${v} not found ❌`)
        xpAction(10, 'Search O(n)')
        setTimeout(() => setHighlighted(null), 2000)
    }

    function reverse() {
        setNodes(n => [...n].reverse())
        xpAction(15, 'Reverse O(n)')
        flash('Reversed the linked list!')
    }

    function xpAction(pts, label) {
        setScore(s => s + pts)
        awardXP(pts, label)
        if (!completed) { setCompleted(true); completeModule(mod.id, mod.badgeId) }
    }

    return (
        <div className="game-container">
            <div className="game-hud">
                <div className="hud-item"><span className="hud-label">Score</span><span className="hud-val">{score}</span></div>
                <div className="hud-item"><span className="hud-label">Length</span><span className="hud-val">{nodes.length}</span></div>
                <div className="hud-item"><span className="hud-label">Head</span><span className="hud-val">{nodes[0] ?? 'null'}</span></div>
                <div className="hud-item"><span className="hud-label">Tail</span><span className="hud-val">{nodes[nodes.length - 1] ?? 'null'}</span></div>
            </div>

            <p className="game-section-title">LINKED LIST VISUALIZATION</p>
            <div className="ll-display">
                {nodes.length === 0 && <span className="ll-null" style={{ color: 'var(--text-muted)' }}>Empty List</span>}
                {nodes.map((val, idx) => (
                    <div key={`${val}-${idx}`} className="ll-node">
                        <div className={`ll-box ${idx === 0 ? 'head-node' : ''} ${idx === highlighted ? 'highlight' : ''}`}
                            onClick={() => deleteNode(idx)} title="Click to delete">
                            <span className="ll-data">{val}</span>
                            <span className="ll-next">next →</span>
                        </div>
                        {idx < nodes.length - 1 && <span className="ll-arrow">→</span>}
                    </div>
                ))}
                <span className="ll-null">→ null</span>
            </div>

            {msg && <div className="result-banner success">{msg}</div>}

            <div className="game-controls">
                <input className="game-input" type="number" placeholder="Node value..."
                    value={inputVal} onChange={e => setInputVal(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && append()} style={{ maxWidth: 160 }} />
                <button className="btn btn-primary btn-sm" onClick={prepend}><Plus size={14} /> Prepend O(1)</button>
                <button className="btn btn-secondary btn-sm" onClick={append}><Plus size={14} /> Append O(n)</button>
                <button className="btn btn-secondary btn-sm" onClick={reverse}><RotateCcw size={14} /> Reverse</button>
            </div>
            <div className="game-controls" style={{ marginTop: 8 }}>
                <input className="game-input" type="number" placeholder="Search value..."
                    value={searchVal} onChange={e => setSearchVal(e.target.value)}
                    style={{ maxWidth: 160 }} />
                <button className="btn btn-secondary btn-sm" onClick={searchNode}><Search size={14} /> Search O(n)</button>
            </div>

            <div className="game-tip">
                💡 <strong>Tip:</strong> Prepend = O(1) (change head pointer). Append = O(n) (traverse to end). Click any node to delete it.
            </div>
        </div>
    )
}
