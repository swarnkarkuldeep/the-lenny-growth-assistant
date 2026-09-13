import React, { useCallback, useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatPane from './components/ChatPane'
import ArtifactViewer from './components/ArtifactViewer'
import HealthBadge from './components/HealthBadge'
import { api, apiErrorMessage } from './api'
import './App.css'

export default function App() {
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [creating, setCreating] = useState(false)
  const [health, setHealth] = useState(null)
  const [healthLoading, setHealthLoading] = useState(true)
  const [provider, setProvider] = useState('cloud')
  const [artifact, setArtifact] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [lastGeneration, setLastGeneration] = useState(null)
  const [mobileView, setMobileView] = useState('deck')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [globalError, setGlobalError] = useState(null)

  useEffect(() => {
    api
      .health()
      .then((res) => setHealth(res.data))
      .catch(() => setHealth(null))
      .finally(() => setHealthLoading(false))

    api
      .listSessions()
      .then((res) => {
        setSessions(res.data)
        if (res.data.length > 0) setActiveSessionId(res.data[0].id)
      })
      .catch((err) => setGlobalError(apiErrorMessage(err)))
  }, [])

  const handleCreateSession = useCallback(async () => {
    setCreating(true)
    try {
      const res = await api.createSession()
      setSessions((prev) => [res.data, ...prev])
      setActiveSessionId(res.data.id)
      setArtifact(null)
      setMobileView('deck')
      setSidebarOpen(false)
    } catch (err) {
      setGlobalError(apiErrorMessage(err))
    } finally {
      setCreating(false)
    }
  }, [])

  const handleSelectSession = useCallback((id) => {
    setActiveSessionId(id)
    setArtifact(null)
    setLastGeneration(null)
    setMobileView('deck')
    setSidebarOpen(false)
  }, [])

  const handleDeleteSession = useCallback(
    async (id) => {
      try {
        await api.deleteSession(id)
        setSessions((prev) => prev.filter((s) => s.id !== id))
        if (activeSessionId === id) {
          setActiveSessionId(null)
          setArtifact(null)
        }
      } catch (err) {
        setGlobalError(apiErrorMessage(err))
      }
    },
    [activeSessionId]
  )

  const runGenerateEssay = useCallback(
    async (selectedProvider) => {
      if (!activeSessionId) return
      setGenerating(true)
      setGlobalError(null)
      try {
        const res = await api.generateEssay(activeSessionId, selectedProvider)
        setArtifact({
          type: 'markdown',
          content: res.data.essay_text,
          provider: res.data.provider,
          validation: res.data.validation,
          kind: 'essay',
        })
        setLastGeneration({ kind: 'essay', type: 'markdown', provider: selectedProvider })
        setMobileView('insert')
      } finally {
        setGenerating(false)
      }
    },
    [activeSessionId]
  )

  const runGenerateArtifact = useCallback(
    async (type, selectedProvider) => {
      if (!activeSessionId) return
      setGenerating(true)
      setGlobalError(null)
      try {
        const res = await api.generateArtifact(activeSessionId, type, selectedProvider)
        setArtifact({
          type: res.data.type,
          content: res.data.content,
          provider: selectedProvider,
          kind: 'artifact',
        })
        setLastGeneration({ kind: 'artifact', type, provider: selectedProvider })
        setMobileView('insert')
      } finally {
        setGenerating(false)
      }
    },
    [activeSessionId]
  )

  const handleRegenerate = useCallback(async () => {
    if (!lastGeneration) return
    if (lastGeneration.kind === 'essay') {
      await runGenerateEssay(lastGeneration.provider)
    } else {
      await runGenerateArtifact(lastGeneration.type, lastGeneration.provider)
    }
  }, [lastGeneration, runGenerateEssay, runGenerateArtifact])

  return (
    <div className="shell">
      <header className="shell__header">
        <button
          type="button"
          className="shell__hamburger"
          aria-label={sidebarOpen ? 'Close sessions' : 'Open sessions'}
          aria-expanded={sidebarOpen}
          onClick={() => setSidebarOpen((v) => !v)}
        >
          <span />
          <span />
          <span />
        </button>
        <div className="shell__brand">
          <span className="shell__mark" aria-hidden="true" />
          <span className="shell__wordmark">Lenny Growth Assistant</span>
        </div>
        <div className="shell__mobile-tabs">
          <button
            type="button"
            data-active={mobileView === 'deck' || undefined}
            onClick={() => setMobileView('deck')}
          >
            Deck
          </button>
          <button
            type="button"
            data-active={mobileView === 'insert' || undefined}
            onClick={() => setMobileView('insert')}
          >
            Insert
          </button>
        </div>
        <HealthBadge health={health} loading={healthLoading} />
      </header>

      {globalError && (
        <div className="shell__banner" role="alert">
          {globalError}
          <button type="button" onClick={() => setGlobalError(null)}>
            Dismiss
          </button>
        </div>
      )}

      <div className="shell__body">
        {sidebarOpen && (
          <div
            className="shell__scrim"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
        )}
        <div className="shell__sidebar" data-open={sidebarOpen || undefined}>
          <Sidebar
            sessions={sessions}
            activeId={activeSessionId}
            onSelect={handleSelectSession}
            onCreate={handleCreateSession}
            onDelete={handleDeleteSession}
            creating={creating}
          />
        </div>

        <main className="shell__deck" data-mobile-hidden={mobileView !== 'deck' || undefined}>
          <ChatPane
            sessionId={activeSessionId}
            provider={provider}
            onProviderChange={setProvider}
            onGenerateEssay={runGenerateEssay}
            onGenerateArtifact={runGenerateArtifact}
            generating={generating}
          />
        </main>

        <section className="shell__insert" data-mobile-hidden={mobileView !== 'insert' || undefined}>
          <ArtifactViewer
            artifact={artifact}
            onRegenerate={lastGeneration ? handleRegenerate : undefined}
            regenerating={generating}
          />
        </section>
      </div>
    </div>
  )
}
