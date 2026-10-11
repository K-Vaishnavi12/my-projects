import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import WorldMap from './pages/WorldMap'
import ModulePage from './pages/ModulePage'
import Profile from './pages/Profile'
import Leaderboard from './pages/Leaderboard'
import Auth from './pages/Auth'
import QuizSector from './pages/QuizSector'

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/map" element={<WorldMap />} />
          <Route path="/module/:id" element={<ModulePage />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="/quiz/:id" element={<QuizSector />} />
        </Routes>
      </main>
    </div>
  )
}
