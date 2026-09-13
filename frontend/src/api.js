import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Every request that talks to an LLM carries provider as the literal string
 * "cloud" (Gemini) or "local" (Ollama) - this matches src/routers/*.py exactly.
 */
export const api = {
  health: () => client.get('/health'),

  createSession: () => client.post('/sessions'),
  listSessions: () => client.get('/sessions'),
  getSession: (sessionId) => client.get(`/sessions/${sessionId}`),
  deleteSession: (sessionId) => client.delete(`/sessions/${sessionId}`),

  chat: (sessionId, message, provider = 'cloud') =>
    client.post('/chat', { session_id: sessionId, message, provider }),

  generateEssay: (sessionId, provider = 'cloud') =>
    client.post('/essays', { session_id: sessionId, provider }),

  generateArtifact: (sessionId, type = 'markdown', provider = 'cloud') =>
    client.post('/artifacts', { session_id: sessionId, type, provider }),

  getArtifact: (artifactId) => client.get(`/artifacts/${artifactId}`),
}

/** Extracts a human-readable message from an Axios error / FastAPI error body. */
export function apiErrorMessage(err) {
  if (err?.response?.data?.detail) return err.response.data.detail
  if (err?.message) return err.message
  return 'An unexpected error occurred.'
}

export default api
