import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { QUIZZES } from '../data/quizzes'
import { MODULES } from '../data/modules'
import { useGame } from '../context/GameContext'
import { X, CheckCircle, XCircle } from 'lucide-react'
import mascot from '../assets/mascot_stick.png'
import './QuizSector.css'

export default function QuizSector() {
    const { id } = useParams()
    const navigate = useNavigate()
    const { saveQuizScore, awardXP } = useGame()

    const module = MODULES.find(m => m.slug === id || m.id === id)
    const questions = QUIZZES[module?.id] || []

    const [currentIndex, setCurrentIndex] = useState(0)
    const [selectedOpt, setSelectedOpt] = useState(null)
    const [isChecked, setIsChecked] = useState(false)
    const [isCorrect, setIsCorrect] = useState(false)
    const [score, setScore] = useState(0)
    const [isFinished, setIsFinished] = useState(false)

    if (!module || !questions.length) return <div className="quiz-error">Quiz not found!</div>

    const currentQ = questions[currentIndex]
    const progress = (currentIndex / questions.length) * 100

    const handleCheck = () => {
        if (selectedOpt === null) return

        if (!isChecked) {
            const correct = selectedOpt === currentQ.answer
            setIsCorrect(correct)
            setIsChecked(true)
            if (correct) {
                setScore(s => s + 1)
            }
        } else {
            // Next question
            if (currentIndex + 1 < questions.length) {
                setCurrentIndex(i => i + 1)
                setSelectedOpt(null)
                setIsChecked(false)
                setIsCorrect(false)
            } else {
                // Finish sequence
                setIsFinished(true)
                saveQuizScore(module.id, score + (isCorrect ? 1 : 0), questions.length)
            }
        }
    }

    if (isFinished) {
        return (
            <div className="quiz-sector-finish">
                <div className="finish-card animate-slide-up">
                    <img src={mascot} alt="Mascot" className="finish-mascot" />
                    <h2>Quiz Completed!</h2>
                    <p>You scored {score}/{questions.length}</p>
                    <div className="finish-actions">
                        <button className="btn btn-primary" onClick={() => navigate('/map')}>Back to Map</button>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="quiz-sector">
            {/* Header / Progress bar */}
            <div className="quiz-header">
                <button className="close-btn" onClick={() => navigate('/map')}><X size={24} /></button>
                <div className="progress-bar-container">
                    <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
                </div>
            </div>

            {/* Question Area */}
            <div className="quiz-content">
                <div className="quiz-question-wrap">
                    <img src={mascot} alt="Smart Owl Mascot" className="quiz-mascot" />
                    <div className="quiz-bubble">
                        <span className="quiz-diff-tag">{currentQ.difficulty}</span>
                        <h2 className="quiz-question">{currentQ.q}</h2>
                    </div>
                </div>

                <div className="quiz-options">
                    {currentQ.options.map((opt, idx) => {
                        let btnClass = 'quiz-opt'
                        if (selectedOpt === idx) btnClass += ' selected'
                        if (isChecked) {
                            if (idx === currentQ.answer) btnClass += ' correct'
                            else if (idx === selectedOpt) btnClass += ' incorrect'
                        }

                        return (
                            <button
                                key={idx}
                                className={btnClass}
                                onClick={() => !isChecked && setSelectedOpt(idx)}
                                disabled={isChecked}
                            >
                                <span className="opt-number">{idx + 1}</span>
                                <span className="opt-text">{opt}</span>
                            </button>
                        )
                    })}
                </div>
            </div>

            {/* Bottom Footer Action */}
            <div className={`quiz-footer ${isChecked ? (isCorrect ? 'footer-correct' : 'footer-incorrect') : ''}`}>
                <div className="footer-content">
                    {isChecked ? (
                        <div className="feedback-msg">
                            {isCorrect ? (
                                <><CheckCircle size={24} /> <span>Excellent!</span></>
                            ) : (
                                <><XCircle size={24} /> <span>Correct Answer: {currentQ.options[currentQ.answer]}</span></>
                            )}
                            <p className="explanation">{currentQ.explanation}</p>
                        </div>
                    ) : (
                        <div /> // empty placholder
                    )}

                    <button
                        className={`btn ${isChecked ? (isCorrect ? 'btn-success' : 'btn-danger') : 'btn-primary'}`}
                        onClick={handleCheck}
                        disabled={selectedOpt === null && !isChecked}
                    >
                        {isChecked ? 'CONTINUE' : 'CHECK'}
                    </button>
                </div>
            </div>
        </div>
    )
}
