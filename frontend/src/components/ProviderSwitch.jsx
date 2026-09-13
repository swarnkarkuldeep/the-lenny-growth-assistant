import React from 'react'
import './ProviderSwitch.css'

/**
 * A two-position hardware-style switch, not a <select>. "cloud" = Gemini API,
 * "local" = Ollama running on the evaluator's machine.
 */
export default function ProviderSwitch({ value, onChange, disabled }) {
  const setValue = (next) => {
    if (disabled || next === value) return
    onChange(next)
  }

  return (
    <div
      className="provider-switch"
      role="radiogroup"
      aria-label="Generation provider"
      data-disabled={disabled || undefined}
    >
      <button
        type="button"
        role="radio"
        aria-checked={value === 'cloud'}
        className="provider-switch__option"
        data-active={value === 'cloud' || undefined}
        onClick={() => setValue('cloud')}
        disabled={disabled}
      >
        Cloud <span className="provider-switch__sub">Gemini</span>
      </button>
      <button
        type="button"
        role="radio"
        aria-checked={value === 'local'}
        className="provider-switch__option"
        data-active={value === 'local' || undefined}
        onClick={() => setValue('local')}
        disabled={disabled}
      >
        Local <span className="provider-switch__sub">Ollama</span>
      </button>
      <span className="provider-switch__thumb" data-position={value} aria-hidden="true" />
    </div>
  )
}
