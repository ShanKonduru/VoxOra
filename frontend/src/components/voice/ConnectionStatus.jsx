import { useSessionStore } from '../../store/sessionStore'

const STATUS_CONFIG = {
  idle:          { label: 'Idle',          color: 'badge-gray'   },
  connecting:    { label: 'Connecting…',   color: 'badge-yellow' },
  connected:     { label: 'Connected',     color: 'badge-green'  },
  listening:     { label: 'Listening…',    color: 'badge-blue'   },
  processing:    { label: 'Processing…',   color: 'badge-yellow' },
  disconnected:  { label: 'Disconnected',  color: 'badge-gray'   },
  error:         { label: 'Error',         color: 'badge-red'    },
  completed:     { label: 'Completed',     color: 'badge-green'  },
}

export default function ConnectionStatus() {
  const wsStatus = useSessionStore((s) => s.wsStatus)
  const config = STATUS_CONFIG[wsStatus] || STATUS_CONFIG.idle

  return (
    <span className={config.color}>
      <span className="mr-1.5 inline-block w-1.5 h-1.5 rounded-full bg-current" />
      {config.label}
    </span>
  )
}
