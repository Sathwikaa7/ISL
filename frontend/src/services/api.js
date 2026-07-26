// Thin wrapper around the Flask REST API.
// All calls are relative ("/api/...") so the Vite dev proxy (see vite.config.js)
// or your production reverse proxy can route them to the Flask backend.
// Adjust paths/payloads here if your backend's routes differ.

const BASE = '/api'

async function handle(res) {
  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json()
      detail = body.error || body.message || ''
    } catch {
      /* ignore parse errors */
    }
    throw new Error(detail || `Request failed with status ${res.status}`)
  }
  return res.json()
}

/**
 * Get fuzzy word suggestions for a raw letter sequence (RapidFuzz on the backend).
 * Expected response: { suggestions: [{ word: "hello", score: 0.92 }, ...] }
 */
export async function fetchWordSuggestions(letterSequence) {
  const res = await fetch(`${BASE}/suggest?prefix=${encodeURIComponent(letterSequence)}`)
  return handle(res)
}

/**
 * Translate an English sentence to Telugu.
 * Expected response: { english: "...", telugu: "..." }
 */
export async function translateSentence(englishText) {
  const res = await fetch(`${BASE}/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: englishText })
  })
  return handle(res)
}

/**
 * Request bilingual speech synthesis (gTTS) for a sentence.
 * Expected response: { audio_url: "/static/audio/xyz.mp3" } OR { audio_base64: "..." }
 */
export async function synthesizeSpeech(text, lang = 'en') {
  const res = await fetch(`${BASE}/speak`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, lang })
  })
  return handle(res)
}

/**
 * Submit accuracy/UX feedback for a session (optional, maps to FEEDBACK table
 * in the ER diagram).
 */
export async function submitFeedback(sessionId, rating, comments) {
  const res = await fetch(`${BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, rating, comments })
  })
  return handle(res)
}

/** Basic backend health check, used for the connection badge. */
export async function pingServer() {
  const res = await fetch(`${BASE}/health`)
  return handle(res)
}
