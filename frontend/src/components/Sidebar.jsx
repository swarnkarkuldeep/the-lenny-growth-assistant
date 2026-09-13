import React from 'react'
import { PlusIcon, TrashIcon } from './Icons'
import './Sidebar.css'

// Backend TIMESTAMP columns are stored/serialized without a UTC offset
// (naive datetimes). `new Date("2026-09-13T05:30:00")` would otherwise be
// parsed as *local* time by the browser, skewing every relative time by the
// viewer's UTC offset (e.g. reading "6h ago" for a session created seconds
// ago). Treat any offset-less ISO string as UTC explicitly.
function toUtcDate(iso) {
  const hasOffset = /Z$|[+-]\d{2}:?\d{2}$/.test(iso)
  return new Date(hasOffset ? iso : `${iso}Z`)
}

function formatRelative(iso) {
  const date = toUtcDate(iso)
  const diffMs = Date.now() - date.getTime()
  const diffMin = Math.round(diffMs / 60000)
  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.round(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.round(diffHr / 24)
  if (diffDay < 7) return `${diffDay}d ago`
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export default function Sidebar({ sessions, activeId, onSelect, onCreate, onDelete, creating }) {
  return (
    <nav className="sidebar" aria-label="Sessions">
      <div className="sidebar__head">
        <span className="sidebar__title">Tracklist</span>
        <button
          type="button"
          className="sidebar__new"
          onClick={onCreate}
          disabled={creating}
          aria-label="Start new session"
        >
          <PlusIcon />
          New
        </button>
      </div>

      {sessions.length === 0 ? (
        <p className="sidebar__empty">No sessions yet. Start one to begin researching.</p>
      ) : (
        <ol className="sidebar__list">
          {sessions.map((session, index) => (
            <li key={session.id} className="sidebar__row" data-active={session.id === activeId || undefined}>
              <button
                type="button"
                className="sidebar__row-main"
                onClick={() => onSelect(session.id)}
                aria-current={session.id === activeId ? 'true' : undefined}
              >
                <span className="sidebar__track-no">{String(index + 1).padStart(2, '0')}</span>
                <span className="sidebar__meta">
                  <span className="sidebar__meta-title">Session {session.id.slice(0, 8)}</span>
                  <span className="sidebar__meta-sub">{formatRelative(session.created_at)}</span>
                </span>
              </button>
              <button
                type="button"
                className="sidebar__delete"
                aria-label="Delete session"
                onClick={() => onDelete(session.id)}
              >
                <TrashIcon />
              </button>
            </li>
          ))}
        </ol>
      )}
    </nav>
  )
}
