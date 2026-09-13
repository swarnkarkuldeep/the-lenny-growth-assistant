import React, { useEffect, useMemo, useRef, useState } from 'react'
import { api, apiErrorMessage } from '../api'
import { extractCitationsFromText, hasNoSupportStatement } from '../lib/citations'
import ProviderSwitch from './ProviderSwitch'
import CitationChip from './CitationChip'
import SafeMarkdown from './SafeMarkdown'
import { AlertIcon, SendIcon } from './Icons'
import './ChatPane.css'

const EXAMPLE_QUESTIONS = [
  'What makes a good pricing model for a B2B SaaS product?',
  'How do successful PMs reduce user churn?',
  'What separates a strong product sense from a weak one?',
]

function normalizeMessage(raw) {
  const citations = raw.citations ?? extractCitationsFromText(raw.content)
  return {
    id: raw.id,
    role: raw.role,
    content: raw.content,
    provider: raw.provider ?? null,
    citations,
    ungrounded:
      raw.role === 'assistant' &&
      citations.length === 0 &&
      !hasNoSupportStatement(raw.content) &&
      raw.validation_passed === false,
  }
}

export default function ChatPane({
  sessionId,
  provider,
  onProviderChange,
  onGenerateEssay,
  onGenerateArtifact,
  generating,
}) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loadingSession, setLoadingSession] = useState(false)
  const [error, setError] = useState(null)
  const streamEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    if (!sessionId) {
      setMessages([])
      return
    }
    setLoadingSession(true)
    setError(null)
    api
      .getSession(sessionId)
      .then((res) => {
        if (cancelled) return
        setMessages((res.data.messages || []).map(normalizeMessage))
      })
      .catch((err) => {
        if (cancelled) return
        setError(apiErrorMessage(err))
      })
      .finally(() => {
        if (!cancelled) setLoadingSession(false)
      })
    return () => {
      cancelled = true
    }
  }, [sessionId])

  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, sending])

  const canGenerate = useMemo(
    () => messages.some((m) => m.role === 'user') && !sending,
    [messages, sending]
  )

  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || !sessionId || sending) return

    const optimisticUser = { id: `local-${Date.now()}`, role: 'user', content: text, citations: [] }
    setMessages((prev) => [...prev, optimisticUser])
    setInput('')
    setSending(true)
    setError(null)

    try {
      const res = await api.chat(sessionId, text, provider)
      const { response, message_id } = res.data
      setMessages((prev) => [
        ...prev,
        normalizeMessage({
          id: message_id,
          role: 'assistant',
          content: response.response_text,
          provider: response.provider,
          citations: response.citations,
          validation_passed: response.validation_passed,
        }),
      ])
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  async function handleEssay() {
    setError(null)
    try {
      await onGenerateEssay(provider)
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  async function handleArtifact(type) {
    setError(null)
    try {
      await onGenerateArtifact(type, provider)
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  if (!sessionId) {
    return (
      <div className="deck deck--empty">
        <p className="deck__placeholder">Select or start a session to begin.</p>
      </div>
    )
  }

  return (
    <div className="deck">
      <div className="deck__stream" aria-live="polite">
        {messages.length === 0 && !loadingSession ? (
          <div className="deck__welcome">
            <p className="deck__welcome-lede">
              Ask a question about product, growth, or strategy. Every answer is
              grounded in Lenny&rsquo;s Podcast, with cue points back to the source.
            </p>
            <div className="deck__examples">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  className="deck__example-card"
                  onClick={() => setInput(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="deck-row" data-role={msg.role}>
              <div className="deck-row__meta">
                <span className="deck-row__role">{msg.role === 'user' ? 'You' : 'Assistant'}</span>
                {msg.provider && (
                  <span className="deck-row__provider">{msg.provider === 'cloud' ? 'gemini' : 'ollama'}</span>
                )}
              </div>
              <div className="deck-row__bubble">
                {msg.role === 'assistant' ? (
                  <SafeMarkdown className="deck-row__prose">{msg.content}</SafeMarkdown>
                ) : (
                  <p className="deck-row__prose deck-row__prose--plain">{msg.content}</p>
                )}
                {msg.ungrounded && (
                  <p className="deck-row__flag">
                    <AlertIcon /> This response did not include a source citation.
                  </p>
                )}
                {msg.citations.length > 0 && (
                  <div className="deck-row__citations">
                    {msg.citations.map((c, i) => (
                      <CitationChip key={i} citation={c} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {sending && (
          <div className="deck-row" data-role="assistant">
            <div className="deck-row__meta">
              <span className="deck-row__role">Assistant</span>
            </div>
            <div className="deck-row__bubble deck-row__bubble--loading">
              <span className="deck-spinner" aria-hidden="true" />
              Retrieving and generating a grounded response…
            </div>
          </div>
        )}

        {error && (
          <div className="deck-error" role="alert">
            <AlertIcon />
            <span>{error}</span>
            <button type="button" onClick={() => setError(null)} aria-label="Dismiss error">
              Dismiss
            </button>
          </div>
        )}

        <div ref={streamEndRef} />
      </div>

      <div className="deck__controls">
        {canGenerate && (
          <div className="deck__actions">
            <button
              type="button"
              className="deck__cta"
              onClick={handleEssay}
              disabled={generating}
            >
              {generating ? 'Working…' : 'Cut an Essay'}
            </button>
            <button
              type="button"
              className="deck__cta deck__cta--ghost"
              onClick={() => handleArtifact('markdown')}
              disabled={generating}
            >
              Generate Markdown
            </button>
            <button
              type="button"
              className="deck__cta deck__cta--ghost"
              onClick={() => handleArtifact('html')}
              disabled={generating}
            >
              Generate HTML
            </button>
          </div>
        )}

        <form className="deck__composer" onSubmit={handleSend}>
          <label htmlFor="composer-input" className="sr-only">
            Ask a question
          </label>
          <input
            id="composer-input"
            ref={inputRef}
            type="text"
            placeholder={sending ? 'Waiting for response…' : 'Ask a question…'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sending}
            autoComplete="off"
          />
          <ProviderSwitch value={provider} onChange={onProviderChange} disabled={sending} />
          <button
            type="submit"
            className="deck__send"
            disabled={sending || !input.trim()}
            aria-label="Send message"
          >
            <SendIcon />
          </button>
        </form>
      </div>
    </div>
  )
}
