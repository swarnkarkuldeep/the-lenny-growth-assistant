import React from 'react'
import './CitationChip.css'

/**
 * Citations render as stamped catalog-reference cue points, never bare
 * hyperlinks - the Saville-catalog raise: grounding needs a rigorous,
 * legible reference code, not a decoded-on-hover mystery.
 */
export default function CitationChip({ citation }) {
  const label = `${citation.speaker} · ${citation.episode} · ${citation.timestamp}`

  const content = (
    <>
      <span className="citation-chip__mark" aria-hidden="true">
        ▸
      </span>
      <span className="citation-chip__speaker">{citation.speaker}</span>
      <span className="citation-chip__time">{citation.timestamp}</span>
    </>
  )

  if (citation.video_url) {
    return (
      <a
        className="citation-chip"
        href={citation.video_url}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Open source: ${label}`}
        title={label}
      >
        {content}
      </a>
    )
  }

  return (
    <span className="citation-chip" role="note" aria-label={label} title={label}>
      {content}
    </span>
  )
}
