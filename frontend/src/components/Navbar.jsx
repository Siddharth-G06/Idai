import { NavLink } from 'react-router-dom'
import { BarChart3, List, GitCompare } from 'lucide-react'

const links = [
  { to: '/',         label: 'Dashboard', icon: BarChart3  },
  { to: '/promises', label: 'Promises',  icon: List       },
  { to: '/compare',  label: 'Compare',   icon: GitCompare },
]

export default function Navbar() {
  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
      background: 'rgba(10,13,20,0.85)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
      height: '64px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 24px',
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: 'linear-gradient(135deg,#22d3ee,#6366f1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, fontWeight: 800,
        }}>வ</div>
        <div>
          <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontWeight: 700, fontSize: 17, letterSpacing: '-0.02em', color: '#f1f5f9' }}>
            Vaakazhipeer
          </div>
          <div style={{ fontSize: 10, color: '#64748b', letterSpacing: '.08em', textTransform: 'uppercase' }}>
            Promise Tracker · Tamil Nadu
          </div>
        </div>
      </div>

      {/* Links */}
      <div style={{ display: 'flex', gap: 4 }}>
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 14px', borderRadius: 8,
              fontSize: 13, fontWeight: 500,
              textDecoration: 'none',
              transition: 'all .2s',
              color:      isActive ? '#22d3ee' : '#94a3b8',
              background: isActive ? 'rgba(34,211,238,.1)' : 'transparent',
            })}
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
