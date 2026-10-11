import { useState } from 'react'
import { useGame } from '../context/GameContext'
import './Game.css'

class BST {
    constructor() { this.root = null }
    insert(val) { this.root = this._ins(this.root, val) }
    _ins(node, val) {
        if (!node) return { val, left: null, right: null }
        if (val < node.val) return { ...node, left: this._ins(node.left, val) }
        if (val > node.val) return { ...node, right: this._ins(node.right, val) }
        return node
    }
    search(node, val, path = []) {
        if (!node) return { found: false, path }
        path.push(node.val)
        if (node.val === val) return { found: true, path }
        if (val < node.val) return this.search(node.left, val, path)
        return this.search(node.right, val, path)
    }
    inorder(node, res = []) {
        if (!node) return res
        this.inorder(node.left, res); res.push(node.val); this.inorder(node.right, res)
        return res
    }
}

function TreeNodeComp({ node, highlightPath, depth = 0 }) {
    if (!node) return null
    const isHighlighted = highlightPath.includes(node.val)
    const isRoot = depth === 0
    return (
        <div className="tree-node-wrap">
            <div className={`tree-node ${isHighlighted ? 'highlighted' : ''} ${isRoot ? 'root-node' : ''}`}
                style={{ boxShadow: isHighlighted ? '0 0 18px rgba(34,211,160,0.6)' : undefined }}>
                {node.val}
            </div>
            {(node.left || node.right) && (
                <>
                    <div className="tree-edge" />
                    <div className="tree-children">
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            {node.left ? <TreeNodeComp node={node.left} highlightPath={highlightPath} depth={depth + 1} /> :
                                <div style={{ width: 46 }} />}
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            {node.right ? <TreeNodeComp node={node.right} highlightPath={highlightPath} depth={depth + 1} /> :
                                <div style={{ width: 46 }} />}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default function TreeGame({ module: mod }) {
    const { awardXP, completeModule } = useGame()
    const [bst] = useState(() => new BST())
    const [root, setRoot] = useState(() => {
        const b = new BST()
            ;[50, 30, 70, 20, 40, 60, 80].forEach(v => b.insert(v))
        return b.root
    })
    const [inputVal, setInputVal] = useState('')
    const [searchVal, setSearchVal] = useState('')
    const [highlightPath, setHighlightPath] = useState([])
    const [score, setScore] = useState(0)
    const [msg, setMsg] = useState('')
    const [completed, setCompleted] = useState(false)

    function flash(m) { setMsg(m); setTimeout(() => setMsg(''), 2500) }
    function xpAction(pts, label) {
        setScore(s => s + pts); awardXP(pts, label)
        if (!completed) { setCompleted(true); completeModule(mod.id, mod.badgeId) }
    }

    function insertNode() {
        const v = parseInt(inputVal); if (isNaN(v) || v < 1 || v > 999) return
        bst.root = root
        bst.insert(v)
        setRoot({ ...bst.root })
        flash(`Inserted ${v} into BST!`)
        xpAction(15, `BST Insert`)
        setInputVal('')
        setHighlightPath([])
    }

    function searchNode() {
        const v = parseInt(searchVal); if (isNaN(v)) return
        const { found, path } = bst.search(root, v)
        setHighlightPath(path)
        flash(found ? `Found ${v}! Path: ${path.join(' → ')}` : `${v} not in BST`)
        xpAction(10, 'BST Search')
    }

    const sorted = (() => {
        const res = []; function inorder(n) { if (!n) return; inorder(n.left); res.push(n.val); inorder(n.right); } inorder(root); return res
    })()

    return (
        <div className="game-container">
            <div className="game-hud">
                <div className="hud-item"><span className="hud-label">Score</span><span className="hud-val">{score}</span></div>
                <div className="hud-item"><span className="hud-label">Root</span><span className="hud-val">{root?.val}</span></div>
                <div className="hud-item"><span className="hud-label">In-Order</span><span style={{ fontSize: '0.7rem', color: 'var(--neon-green)', fontFamily: 'var(--font-code)' }}>{sorted.join(', ')}</span></div>
            </div>

            {msg && <div className={`result-banner ${msg.includes('not') ? 'fail' : 'success'}`}>{msg}</div>}

            <p className="game-section-title">BST VISUALIZATION (click nodes to see path)</p>
            <div className="tree-display">
                <TreeNodeComp node={root} highlightPath={highlightPath} />
            </div>

            <div className="game-controls">
                <input className="game-input" type="number" min="1" max="999" placeholder="Insert value (1–999)..."
                    value={inputVal} onChange={e => setInputVal(e.target.value)} onKeyDown={e => e.key === 'Enter' && insertNode()}
                    style={{ maxWidth: 220 }} />
                <button className="btn btn-primary btn-sm" onClick={insertNode}>Insert Node</button>
            </div>
            <div className="game-controls" style={{ marginTop: 8 }}>
                <input className="game-input" type="number" placeholder="Search value..."
                    value={searchVal} onChange={e => setSearchVal(e.target.value)} style={{ maxWidth: 220 }} />
                <button className="btn btn-secondary btn-sm" onClick={searchNode}>Search O(log n)</button>
                <button className="btn btn-secondary btn-sm" onClick={() => setHighlightPath([])}>Clear</button>
            </div>

            <div className="game-tip">
                💡 <strong>BST Property:</strong> Left child &lt; Parent &lt; Right child. In-order traversal gives sorted output!
                Try inserting: 55, 25, 65, 15, 35
            </div>
        </div>
    )
}
