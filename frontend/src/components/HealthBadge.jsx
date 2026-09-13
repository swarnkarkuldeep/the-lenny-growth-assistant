import React from 'react'
import './HealthBadge.css'

/**
 * A VU-meter-style status dot, not a flat pill - the dot itself carries a real
 * state (idle / connected / degraded / offline), matching the nixie-tube
 * challenger's "honest mechanical state change" raise.
 */
export default function HealthBadge({ health, loading }) {
  let state = 'idle'
  let label = 'Checking system…'

  if (!loading && health) {
    if (health.status === 'ok') {
      state = 'good'
      label = 'System ready'
    } else {
      state = 'warn'
      label = 'System degraded'
    }
  } else if (!loading && !health) {
    state = 'bad'
    label = 'Backend unreachable'
  }

  const detail = health
    ? `Postgres: ${health.postgres} · Ollama: ${health.ollama} · Gemini key: ${health.gemini_api_key}`
    : ''

  return (
    <div className="health-badge" title={detail || undefined}>
      <span className="health-badge__dot" data-state={state} aria-hidden="true" />
      <span className="health-badge__label">{label}</span>
    </div>
  )
}
