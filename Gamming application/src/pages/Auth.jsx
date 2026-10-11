import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGame } from '../context/GameContext'
import './Auth.css'

export default function Auth() {
    const [isLogin, setIsLogin] = useState(true)
    const [name, setName] = useState('')
    const { setPlayerName, awardXP } = useGame()
    const navigate = useNavigate()

    const handleSubmit = (e) => {
        e.preventDefault()
        if (name.trim()) {
            setPlayerName(name)
            if (!isLogin) {
                awardXP(50, 'Welcome Bonus!')
            }
            navigate('/map', { state: { justLoggedIn: true } })
        }
    }

    return (
        <div className="auth-page">
            <div className="stars-bg grid-bg" />
            <div className="auth-container animate-slide-up">
                <div className="auth-card glass">
                    <div className="auth-logo">⚡ AlgoQuest</div>
                    <h2 className="auth-title">
                        {isLogin ? 'Welcome Back, Challenger' : 'Join the Quest'}
                    </h2>
                    <p className="auth-subtitle">
                        {isLogin ? 'Resume your DSA journey and climb the leaderboard.' : 'Create an account to track your progress and earn badges.'}
                    </p>

                    <div className="auth-tabs">
                        <button type="button" className={`auth-tab ${isLogin ? 'active' : ''}`} onClick={() => setIsLogin(true)}>Sign In</button>
                        <button type="button" className={`auth-tab ${!isLogin ? 'active' : ''}`} onClick={() => setIsLogin(false)}>Sign Up</button>
                    </div>

                    <form onSubmit={handleSubmit} className="auth-form">
                        <div className="form-group">
                            <label>Username</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="e.g. CodeNinja99"
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Password</label>
                            <input type="password" placeholder="••••••••" required />
                        </div>
                        <button type="submit" className="btn btn-primary auth-submit">
                            {isLogin ? 'Sign In' : 'Create Account'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    )
}
