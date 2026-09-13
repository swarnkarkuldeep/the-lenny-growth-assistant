import React, { useState } from 'react'
import DOMPurify from 'dompurify'
import SafeMarkdown from './SafeMarkdown'
import { CheckIcon, CopyIcon, DownloadIcon, RegenIcon } from './Icons'
import './ArtifactViewer.css'

const HTML_ALLOWED_TAGS = [
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'p', 'ul', 'ol', 'li', 'strong', 'em', 'a', 'blockquote', 'code', 'pre',
]
const HTML_ALLOWED_ATTR = ['href']

const VALIDATION_LABELS = {
  word_count_ok: 'Word count in range',
  has_headings: 'Has headings',
  has_takeaway: 'Has a clear takeaway',
  has_citations: 'Has citations',
  all_claims_traceable: 'Claims traceable to sources',
}

export default function ArtifactViewer({ artifact, onRegenerate, regenerating }) {
  const [copied, setCopied] = useState(false)

  if (!artifact) {
    return (
      <aside className="insert insert--empty" aria-label="Artifact viewer">
        <div className="insert__stamp">SLEEVE INSERT</div>
        <p className="insert__placeholder">
          No artifact yet. Ask a question, then cut an essay or generate an
          artifact to see it rendered here.
        </p>
      </aside>
    )
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard API unavailable - silently no-op, copy button just won't confirm */
    }
  }

  const handleDownload = () => {
    const ext = artifact.type === 'html' ? 'html' : 'md'
    const mime = artifact.type === 'html' ? 'text/html' : 'text/markdown'
    const blob = new Blob([artifact.content], { type: mime })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `lenny-${artifact.kind ?? 'artifact'}-${new Date().toISOString().slice(0, 10)}.${ext}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const validationEntries = artifact.validation
    ? Object.entries(VALIDATION_LABELS).map(([key, label]) => ({
        key,
        label,
        passed: Boolean(artifact.validation[key]),
      }))
    : null

  return (
    <aside className="insert" aria-label="Artifact viewer">
      <div className="insert__head">
        <div>
          <div className="insert__stamp">SLEEVE INSERT</div>
          <div className="insert__type">{artifact.type === 'html' ? 'HTML' : 'Markdown'}</div>
        </div>
        <div className="insert__controls">
          <button type="button" onClick={handleCopy} aria-label="Copy artifact to clipboard">
            {copied ? <CheckIcon /> : <CopyIcon />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button type="button" onClick={handleDownload} aria-label="Download artifact">
            <DownloadIcon />
            Download
          </button>
          {onRegenerate && (
            <button
              type="button"
              onClick={onRegenerate}
              disabled={regenerating}
              aria-label="Regenerate artifact"
            >
              <RegenIcon />
              {regenerating ? 'Regenerating…' : 'Regenerate'}
            </button>
          )}
        </div>
      </div>

      {validationEntries && (
        <div className="insert__validation" aria-label="Compliance checks">
          <span
            className="insert__validation-overall"
            data-passed={artifact.validation.compliance_passed}
          >
            {artifact.validation.compliance_passed ? 'Fully compliant' : 'Needs review'} ·{' '}
            {artifact.validation.word_count} words
          </span>
          <ul className="insert__validation-list">
            {validationEntries.map((entry) => (
              <li key={entry.key} data-passed={entry.passed}>
                <span className="insert__validation-mark" aria-hidden="true">
                  {entry.passed ? '✓' : '×'}
                </span>
                {entry.label}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="insert__content">
        {artifact.type === 'markdown' ? (
          <SafeMarkdown className="insert__prose">{artifact.content}</SafeMarkdown>
        ) : (
          <div
            className="insert__prose"
            // Sanitized twice: bleach on the backend (src/routers/artifacts.py),
            // DOMPurify here as a second, independent gate before this ever
            // reaches dangerouslySetInnerHTML - see docs/architecture.md.
            dangerouslySetInnerHTML={{
              __html: DOMPurify.sanitize(artifact.content, {
                ALLOWED_TAGS: HTML_ALLOWED_TAGS,
                ALLOWED_ATTR: HTML_ALLOWED_ATTR,
              }),
            }}
          />
        )}
      </div>
    </aside>
  )
}
