import { useState } from 'react'
import { CheckCircle, XCircle, ChevronRight, RotateCcw } from 'lucide-react'
import { useGame } from '../context/GameContext'

export default function QuizPanel({ questions, moduleId }) {
    const [current, setCurrent] = useState(0)
    const [selected, setSelected] = useState(null)
    const [answered, setAnswered] = useState(false)
    const [score, setScore] = useState(0)
    const [done, setDone] = useState(false)
    const { saveQuizScore } = useGame()

    function handleSelect(idx) {
        if (answered) return
        setSelected(idx)
        setAnswered(true)
        if (idx === questions[current].answer) {
            setScore(s => s + 1)
        }
    }

    function handleNext() {
        if (current + 1 >= questions.length) {
            setDone(true)
            saveQuizScore(moduleId, score + (selected === questions[current].answer ? 1 : 0), questions.length)
        } else {
            setCurrent(c => c + 1)
            setSelected(null)
            setAnswered(false)
        }
    }

    function handleReset() {
        setCurrent(0); setSelected(null); setAnswered(false); setScore(0); setDone(false)
    }

    if (done) {
        const finalScore = score + (selected === questions[current]?.answer ? 1 : 0)
        const pct = Math.round((finalScore / questions.length) * 100)
        return (
            <div className="quiz-done">
                <div className="quiz-score-circle" style={{
                    background: pct >= 75
                        ? 'conic-gradient(var(--neon-green) 0% ' + pct + '%, rgba(255,255,255,0.06) 0%)'
                        : 'conic-gradient(var(--neon-orange) 0% ' + pct + '%, rgba(255,255,255,0.06) 0%)'
                }}>
                    <div className="quiz-score-inner">
                        <span className="quiz-score-num">{pct}%</span>
                        <span className="quiz-score-label">Score</span>
                    </div>
                </div>
                <h3 className="quiz-done-title">
                    {pct === 100 ? '🏆 Perfect Score!' : pct >= 75 ? '🎉 Great Job!' : pct >= 50 ? '👍 Not Bad!' : '💪 Keep Practicing!'}
                </h3>
                <p className="quiz-done-sub">You got {finalScore} out of {questions.length} correct</p>
                <button className="btn btn-secondary btn-sm" onClick={handleReset} style={{ marginTop: 16 }}>
                    <RotateCcw size={14} /> Try Again
                </button>
            </div>
        )
    }

    const q = questions[current]
    return (
        <div className="quiz-panel">
            <div className="quiz-header">
                <span className="quiz-progress">Question {current + 1} / {questions.length}</span>
                <span className="quiz-score-mini">Score: {score}</span>
            </div>
            <div className="progress-track" style={{ marginBottom: 20, height: 6 }}>
                <div className="progress-fill" style={{ width: `${(current / questions.length) * 100}%`, height: '100%' }} />
            </div>
            <h3 className="quiz-question">{q.q}</h3>
            <div className="quiz-options">
                {q.options.map((opt, idx) => {
                    let cls = 'quiz-option'
                    if (answered) {
                        if (idx === q.answer) cls += ' correct'
                        else if (idx === selected) cls += ' wrong'
                    }
                    return (
                        <button key={idx} className={cls} onClick={() => handleSelect(idx)}>
                            <span className="quiz-opt-letter">{String.fromCharCode(65 + idx)}.</span> {opt}
                            {answered && idx === q.answer && <CheckCircle size={16} className="opt-icon" />}
                            {answered && idx === selected && idx !== q.answer && <XCircle size={16} className="opt-icon" />}
                        </button>
                    )
                })}
            </div>
            {answered && (
                <div className="quiz-explanation">
                    💡 <strong>Explanation:</strong> {q.explanation}
                </div>
            )}
            {answered && (
                <button className="btn btn-primary btn-sm" onClick={handleNext} style={{ marginTop: 16 }}>
                    {current + 1 >= questions.length ? 'See Results' : 'Next'} <ChevronRight size={14} />
                </button>
            )}
        </div>
    )
}
