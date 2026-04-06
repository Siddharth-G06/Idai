import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar   from './components/Navbar'
import Home     from './pages/Home'
import Promises from './pages/Promises'
import Compare  from './pages/Compare'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="min-h-screen pt-16">
        <Routes>
          <Route path="/"         element={<Home />} />
          <Route path="/promises" element={<Promises />} />
          <Route path="/compare"  element={<Compare />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
