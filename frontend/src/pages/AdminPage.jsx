import { Route, Routes, useNavigate } from 'react-router-dom'
import ParticipantTable from '../components/admin/ParticipantTable'
import ReminderPanel from '../components/admin/ReminderPanel'
import ResponseViewer from '../components/admin/ResponseViewer'
import StatsOverview from '../components/admin/StatsOverview'
import { useAdminAuth } from '../hooks/useAdminAuth'

function NavItem({ href, label, active }) {
  return (
    <a
      href={href}
      className={`block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
        active ? 'bg-indigo-50 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      {label}
    </a>
  )
}

export default function AdminPage() {
  const { logout } = useAdminAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/admin/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col p-4 gap-1">
        <div className="flex items-center gap-2 mb-6 px-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
            V
          </div>
          <span className="font-bold text-gray-900">Voxora</span>
        </div>
        <NavItem href="/admin" label="Dashboard" />
        <NavItem href="/admin/participants" label="Participants" />
        <NavItem href="/admin/reminders" label="Reminders" />
        <div className="mt-auto">
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-100 transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-8 overflow-auto">
        <Routes>
          <Route path="/" element={<StatsOverview />} />
          <Route path="/participants" element={<ParticipantTable />} />
          <Route path="/reminders" element={<ReminderPanel />} />
          <Route path="/sessions/:sessionId" element={<ResponseViewer />} />
        </Routes>
      </main>
    </div>
  )
}
