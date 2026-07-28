import { useState } from 'react'
import Header from './components/Header'
import WebcamPanel from './components/WebcamPanel'
import ModeToggle from './components/ModeToggle'
import LetterBuffer from './components/LetterBuffer'
import WordSuggestions from './components/WordSuggestions'
import SentenceBuilder from './components/SentenceBuilder'
import BilingualOutput from './components/BilingualOutput'
import TranscriptHistory from './components/TranscriptHistory'
import { translateSentence } from './services/api'
import { createSessionId } from './services/utils'

export default function App() {
  const [sessionId] = useState(createSessionId)

  const [mode, setMode] = useState('alphabet')

  const [connectionStatus, setConnectionStatus] = useState('connecting')

  const [letterBuffer, setLetterBuffer] = useState('')
  const [isFrozen, setIsFrozen] = useState(false)

  const [sentenceWords, setSentenceWords] = useState([])
  const [englishOutput, setEnglishOutput] = useState('')
  const [teluguOutput, setTeluguOutput] = useState('')
  const [isTranslating, setIsTranslating] = useState(false)
  const [transcript, setTranscript] = useState([])

  function handlePrediction({ label, confidence }) {
    // One click creates one server prediction.  Do not wait for a second
    // frame: alphabet capture is intentionally a single-frame interaction.
    if (mode !== 'alphabet' || !label) return
    setLetterBuffer((previous) => previous + label.toUpperCase())
  }
  

  function handleBackspace() {
    setLetterBuffer((prev) => prev.slice(0, -1))
  }

  function handleClearBuffer() {
    setLetterBuffer('')
  }

  function handleSelectSuggestion(word) {
    setSentenceWords((prev) => [...prev, word])
    setLetterBuffer('')
  }

  function handleAddSpace() {
    if (letterBuffer) {
      setSentenceWords((prev) => [...prev, letterBuffer])
      setLetterBuffer('')
    }
  }

  function handleRemoveWord(index) {
    setSentenceWords((prev) =>
      prev.filter((_, i) => i !== index)
    )
  }

  function handleUndoWord() {
    setSentenceWords((prev) => prev.slice(0, -1))
  }

  function handleClearSentence() {
    setSentenceWords([])
    setEnglishOutput('')
    setTeluguOutput('')
  }

  async function handleTranslate(sentence) {

    if (!sentence) return

    setIsTranslating(true)

    try {

      const data = await translateSentence(sentence)

      setEnglishOutput(data.english ?? sentence)
      setTeluguOutput(data.telugu ?? '')

      setTranscript((prev) => [
        ...prev,
        {
          english: data.english ?? sentence,
          telugu: data.telugu ?? '',
          time: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })
        }
      ])

      setSentenceWords([])

    } catch {

      setEnglishOutput(sentence)

      setTeluguOutput(
        'Translation service unavailable — check the /api/translate endpoint.'
      )

    } finally {

      setIsTranslating(false)

    }
  }

  return (
    <div className="mx-auto min-h-screen max-w-6xl px-4 py-8 sm:px-6 lg:px-8">

      <Header sessionId={sessionId} />

      <main className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-5">

        <div className="flex flex-col gap-5 lg:col-span-3">

          <WebcamPanel
            sessionId={sessionId}
            mode={mode}
            onPrediction={handlePrediction}
            isFrozen={isFrozen}
            connectionStatus={connectionStatus}
            setConnectionStatus={setConnectionStatus}
          />

          <ModeToggle
            mode={mode}
            setMode={setMode}
          />

          <BilingualOutput
            english={englishOutput}
            telugu={teluguOutput}
          />

        </div>

        <div className="flex flex-col gap-5 lg:col-span-2">

          {console.log("Current Buffer:", letterBuffer)}

          <LetterBuffer
            buffer={letterBuffer}
            onBackspace={handleBackspace}
            onClear={handleClearBuffer}
            onFreeze={() => setIsFrozen((f) => !f)}
            isFrozen={isFrozen}
          />

          <WordSuggestions
            letterBuffer={letterBuffer}
            onSelect={handleSelectSuggestion}
          />

          <SentenceBuilder
            words={sentenceWords}
            onRemoveWord={handleRemoveWord}
            onAddSpace={handleAddSpace}
            onUndo={handleUndoWord}
            onClear={handleClearSentence}
            onTranslate={handleTranslate}
            isTranslating={isTranslating}
          />

          <TranscriptHistory
            entries={transcript}
          />

        </div>

      </main>

      <footer className="mt-10 border-t border-white/5 pt-4 text-center font-mono text-[11px] text-slate-500">
        MediaPipe · MobileNetV3 · RapidFuzz · Deep Translator · gTTS — Flask + React
      </footer>

    </div>
  )
}
