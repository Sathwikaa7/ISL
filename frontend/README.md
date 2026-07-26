# ISL Live — Frontend

React + Vite + Tailwind frontend for the Real-Time Indian Sign Language
Recognition capstone project. Built to sit in front of a Flask backend that
handles MediaPipe hand tracking, the MobileNetV3 classifier, RapidFuzz word
suggestion, Deep Translator, and gTTS.

## Setup

```bash
cd isl-frontend
npm install
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies `/api/*` and
`/socket.io` to `http://localhost:5000` (your Flask app). Change the target
in `vite.config.js` if your backend runs elsewhere.

For production, `npm run build` outputs static files to `dist/` — serve
these from Flask (e.g. `static_folder='dist'`) or any static host, with
`/api` and `/socket.io` reverse-proxied to the Flask process.

## Backend contract this frontend expects

### WebSocket (Flask-SocketIO)

| Direction | Event        | Payload                                              |
|-----------|--------------|-------------------------------------------------------|
| client → server | `frame`  | `{ image: "data:image/jpeg;base64,...", session_id }` |
| server → client | `prediction` | `{ label: "A", confidence: 0.94, fps: 24 }`        |

Frames are sent roughly every 130ms (client-throttled); the server is free to
infer on its own cadence and only emit `prediction` when a result is ready.

### REST endpoints (`/api/...`)

- `GET /api/health` → `{ status: "ok" }`
- `GET /api/suggest?prefix=hel` → `{ suggestions: [{ word: "hello", score: 0.92 }, ...] }`
- `POST /api/translate` body `{ text: "hello there" }` → `{ english: "...", telugu: "..." }`
- `POST /api/speak` body `{ text: "...", lang: "en" | "te" }` →
  either `{ audio_url: "/static/audio/xyz.mp3" }` or `{ audio_base64: "..." }`
- `POST /api/feedback` body `{ session_id, rating, comments }` → `{ status: "ok" }`

If your route names or payload shapes differ, adjust
`src/services/api.js` and `src/services/socket.js` — every backend call in
the app funnels through those two files.

## UI overview

- **Webcam panel** — live camera feed, connection badge, big predicted-letter
  overlay with a confidence meter, freeze/resume control.
- **Mode toggle** — alphabet (fingerspelling) vs. word/phrase recognition,
  matching the two recognition strategies compared in the project research.
- **Letter buffer** — the raw letters accumulated from stable predictions
  (a letter only commits after ~700ms of steady prediction, to avoid noise).
- **Word suggestions** — RapidFuzz fuzzy matches for the current buffer,
  tap to commit a word into the sentence.
- **Sentence builder** — the word-by-word sentence under construction, with
  undo/clear/add-space, and a "Form sentence" action that calls translate.
- **Bilingual output** — English + Telugu side by side, each with its own
  gTTS "Speak" button.
- **Transcript history** — running log of completed, translated sentences,
  meant to be read by the secondary user (doctor, teacher, officer, etc.)
  the signer is communicating with.

## Design notes

Dark ink-navy background with a teal/amber/coral accent system, Space
Grotesk for display type and Inter for body text, JetBrains Mono for
technical readouts (confidence %, fps, session id). The signature moment is
the large animated letter reveal + confidence meter on the webcam panel —
everything else stays quiet and structural so the live prediction is always
the visual focus.
