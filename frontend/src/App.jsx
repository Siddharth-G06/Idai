import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import PartyPage from './pages/PartyPage'
import Compare from './pages/Compare'
import Navbar from './components/Navbar'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="min-h-screen pt-20 px-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/party/dmk" element={<PartyPage party="DMK" />} />
          <Route path="/party/admk" element={<PartyPage party="ADMK" />} />
          <Route path="/compare" element={<Compare />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
