// Mirrors src/routers/chat.py's CITATION_PATTERN so client-rendered history
// (which only stores raw message content, not structured citations) can still
// surface cue-point chips consistently with freshly-received responses.
const CITATION_PATTERN = /\[(.*?),\s*(.*?),\s*(\d{2}:\d{2}:\d{2})\]/g

export function extractCitationsFromText(text) {
  if (!text) return []
  const citations = []
  const seen = new Set()
  let match
  CITATION_PATTERN.lastIndex = 0
  while ((match = CITATION_PATTERN.exec(text)) !== null) {
    const [, speaker, episode, timestamp] = match
    const key = `${speaker.trim()}|${episode.trim()}|${timestamp.trim()}`
    if (seen.has(key)) continue
    seen.add(key)
    citations.push({
      speaker: speaker.trim(),
      episode: episode.trim(),
      timestamp: timestamp.trim(),
      video_url: null,
    })
  }
  return citations
}

const NO_SUPPORT_PHRASES = ["don't have information", 'not in the knowledge base']

export function hasNoSupportStatement(text) {
  const lower = (text || '').toLowerCase()
  return NO_SUPPORT_PHRASES.some((phrase) => lower.includes(phrase))
}
