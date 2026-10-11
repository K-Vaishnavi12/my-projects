import { useState } from 'react'
import { useGame } from '../context/GameContext'
import './Game.css'

export default function StackQueueGame({ module: mod }) {
    const { awardXP, completeModule } = useGame()
    const [stack, setStack] = useState([1, 2, 3])
    const [queue, setQueue] = useState(['A', 'B', 'C'])
    const [stackInput, setStackInput] = useState('')
    const [queueInput, setQueueInput] = useState('')
    const [score, setScore] = useState(0)
    const [completed, setCompleted] = useState(false)
    const [msg, setMsg] = useState('')
    const [bracketExpr, setBracketExpr] = useState('({[]})')
    const [bracketResult, setBracketResult] = useState(null)
    const [mode, setMode] = useState('stack') // 'stack' | 'queue' | 'bracket'

    function flash(m) { setMsg(m); setTimeout(() => setMsg(''), 2500) }

    function xpAction(pts, label) {
        setScore(s => s + pts); awardXP(pts, label)
        if (!completed) { setCompleted(true); completeModule(mod.id, mod.badgeId) }
    }

    // Stack ops
    function push() {
        if (!stackInput.trim()) return
        setStack(s => [...s, stackInput.trim()])
        flash(`Pushed "${stackInput}" onto stack!`)
        xpAction(10, 'Stack Push O(1)')
        setStackInput('')
    }
    function pop() {
        if (!stack.length) return flash('Stack is empty!')
        const top = stack[stack.length - 1]
        setStack(s => s.slice(0, -1))
        flash(`Popped "${top}" from stack!`)
        xpAction(10, 'Stack Pop O(1)')
    }

    // Queue ops
    function enqueue() {
        if (!queueInput.trim()) return
        setQueue(q => [...q, queueInput.trim()])
        flash(`Enqueued "${queueInput}"!`)
        xpAction(10, 'Queue Enqueue O(1)')
        setQueueInput('')
    }
    function dequeue() {
        if (!queue.length) return flash('Queue is empty!')
        const front = queue[0]
        setQueue(q => q.slice(1))
        flash(`Dequeued "${front}" from front!`)
        xpAction(10, 'Queue Dequeue O(1)')
    }

    // Bracket matching
    function checkBrackets() {
        const pairs = { ')': '(', ']': '[', '}': '{' }
        const stk = []
        let steps = []
        for (const ch of bracketExpr) {
            if ('([{'.includes(ch)) { stk.push(ch); steps.push(`Push '${ch}'`) }
            else if (')]}'.includes(ch)) {
                if (!stk.length || stk[stk.length - 1] !== pairs[ch]) {
                    setBracketResult(false); flash(`❌ Unmatched '${ch}'!`); return
                }
                const popped = stk.pop(); steps.push(`Match '${popped}' ↔ '${ch}'`)
            }
        }
        const balanced = stk.length === 0
        setBracketResult(balanced)
        flash(balanced ? '✅ Balanced! All brackets match.' : '❌ Unbalanced! Unclosed brackets remain.')
        xpAction(20, 'Bracket Check!')
    }

    return (
        <div className="game-container">
            <div className="game-hud">
                <div className="hud-item"><span className="hud-label">Score</span><span className="hud-val">{score}</span></div>
                <div className="hud-item">
                    <span className="hud-label">Mode</span>
                    <div style={{ display: 'flex', gap: 6, marginTop: 2 }}>
                        {['stack', 'queue', 'bracket'].map(m => (
                            <button key={m} className={`btn btn-sm ${mode === m ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => setMode(m)} style={{ padding: '4px 10px', fontSize: '0.7rem' }}>
                                {m === 'stack' ? '📚 Stack' : m === 'queue' ? '🚶 Queue' : '🔲 Brackets'}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {msg && <div className={`result-banner ${msg.includes('❌') ? 'fail' : 'success'}`}>{msg}</div>}

            {mode === 'stack' && (
                <>
                    <p className="game-section-title">STACK (LIFO — Last In, First Out)</p>
                    <div className="stack-display">
                        {stack.length === 0 && <p className="stack-empty">Stack is empty</p>}
                        {stack.map((v, i) => (
                            <div key={i} className={`stack-item ${i === stack.length - 1 ? 'top' : ''}`}>
                                {v} {i === stack.length - 1 && <span style={{ fontSize: '0.65rem', marginLeft: 8 }}>← TOP</span>}
                            </div>
                        ))}
                    </div>
                    <div className="game-controls">
                        <input className="game-input" placeholder="Value to push..." value={stackInput}
                            onChange={e => setStackInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && push()} style={{ maxWidth: 200 }} />
                        <button className="btn btn-primary btn-sm" onClick={push}>Push ↑</button>
                        <button className="btn btn-danger btn-sm" onClick={pop}>Pop ↓</button>
                    </div>
                </>
            )}

            {mode === 'queue' && (
                <>
                    <p className="game-section-title">QUEUE (FIFO — First In, First Out)</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--neon-blue)' }}>← Dequeue (front)</span>
                        <div className="queue-display" style={{ flex: 1 }}>
                            {queue.length === 0 && <span style={{ color: 'var(--text-muted)' }}>Queue is empty</span>}
                            {queue.map((v, i) => (
                                <div key={i} className={`queue-item ${i === 0 ? 'front' : ''}`}>
                                    {v}<span className="queue-label">{i === 0 ? 'FRONT' : i === queue.length - 1 ? 'BACK' : i}</span>
                                </div>
                            ))}
                        </div>
                        <span style={{ fontSize: '0.8rem', color: 'var(--neon-green)' }}>Enqueue (back) →</span>
                    </div>
                    <div className="game-controls">
                        <input className="game-input" placeholder="Value to enqueue..." value={queueInput}
                            onChange={e => setQueueInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && enqueue()} style={{ maxWidth: 200 }} />
                        <button className="btn btn-primary btn-sm" onClick={enqueue}>Enqueue →</button>
                        <button className="btn btn-danger btn-sm" onClick={dequeue}>← Dequeue</button>
                    </div>
                </>
            )}

            {mode === 'bracket' && (
                <>
                    <p className="game-section-title">BRACKET BALANCE CHECKER (using Stack)</p>
                    <div style={{ marginBottom: 16 }}>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 12 }}>
                            A stack is used to verify whether brackets are balanced. Every opening bracket is pushed; every closing bracket pops the stack and checks for a match.
                        </p>
                        <div className="game-controls">
                            <input className="game-input" value={bracketExpr}
                                onChange={e => { setBracketExpr(e.target.value); setBracketResult(null) }}
                                placeholder="e.g. ({[]})" />
                            <button className="btn btn-primary" onClick={checkBrackets}>Check</button>
                        </div>
                        {bracketResult !== null && (
                            <div className={`result-banner ${bracketResult ? 'success' : 'fail'}`} style={{ marginTop: 12 }}>
                                {bracketResult ? '✅ BALANCED — All brackets match!' : '❌ UNBALANCED — Fix your brackets!'}
                            </div>
                        )}
                        <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            {['({[]})', '((()))', '{[}]', '(((', '()[]{}'].map(ex => (
                                <button key={ex} className="btn btn-secondary btn-sm" onClick={() => { setBracketExpr(ex); setBracketResult(null) }}
                                    style={{ fontFamily: 'var(--font-code)' }}>{ex}</button>
                            ))}
                        </div>
                    </div>
                </>
            )}

            <div className="game-tip">
                💡 <strong>Stack:</strong> push/pop are O(1). <strong>Queue:</strong> enqueue/dequeue are O(1) with deque. <strong>Bracket matching</strong> uses a stack!
            </div>
        </div>
    )
}
