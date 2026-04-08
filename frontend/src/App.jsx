import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import PartyPage from './pages/PartyPage'
import Compare from './pages/Compare'
import About from './pages/About'
import HealthBanner from './components/HealthBanner'

export default function App() {
  return (
    <>
      <HealthBanner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/parties/:partyId" element={<PartyPage />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </BrowserRouter>
    </>
  )
}
