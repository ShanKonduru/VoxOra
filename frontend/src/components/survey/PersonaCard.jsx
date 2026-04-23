export default function PersonaCard({ persona }) {
  if (!persona) return null

  const initials = persona.name?.charAt(0) ?? 'V'
  const colors = {
    nova:    'bg-purple-100 text-purple-700',
    onyx:    'bg-gray-100 text-gray-700',
    shimmer: 'bg-pink-100 text-pink-700',
    echo:    'bg-blue-100 text-blue-700',
    alloy:   'bg-green-100 text-green-700',
    fable:   'bg-orange-100 text-orange-700',
  }
  const colorClass = colors[persona.voice_id] || 'bg-indigo-100 text-indigo-700'

  return (
    <div className="flex items-center gap-3">
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${colorClass}`}
      >
        {initials}
      </div>
      <div>
        <p className="text-sm font-semibold text-gray-900">{persona.name}</p>
        <p className="text-xs text-gray-500">{persona.accent}</p>
      </div>
    </div>
  )
}
