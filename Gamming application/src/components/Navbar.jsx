import { Link, useLocation } from 'react-router-dom'
import { useGame } from '../context/GameContext'
import { Map, User, Trophy, Zap, Home, LogIn } from 'lucide-react'
import './Navbar.css'

export default function Navbar() {
    const { xp, level } = useGame()
    const location = useLocation()
    const isActive = (path) => location.pathname === path

    return (
        <nav className="navbar glass">
            <Link to="/" className="navbar-brand">
                <span className="brand-icon">⚡</span>
                <span className="brand-text">AlgoQuest</span>
            </Link>
            <div className="navbar-links">
                <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
                    <Home size={16} /><span>Home</span>
                </Link>
                <Link to="/map" className={`nav-link ${isActive('/map') ? 'active' : ''}`}>
                    <Map size={16} /><span>World Map</span>
                </Link>
                <Link to="/leaderboard" className={`nav-link ${isActive('/leaderboard') ? 'active' : ''}`}>
                    <Trophy size={16} /><span>Ranks</span>
                </Link>
                <Link to="/profile" className={`nav-link ${isActive('/profile') ? 'active' : ''}`}>
                    <User size={16} /><span>Profile</span>
                </Link>
                <Link to="/auth" className={`nav-link ${isActive('/auth') ? 'active' : ''}`}>
                    <LogIn size={16} /><span>Sign In</span>
                </Link>
            </div>
            <div className="navbar-xp">
                <Zap size={14} className="xp-icon" />
                <span className="xp-value">{xp.toLocaleString()} XP</span>
                <span className="level-badge">LVL {level}</span>
            </div>
        </nav>
    )
}
