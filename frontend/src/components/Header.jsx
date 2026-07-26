export default function Header({ sessionId }) {
  return (
    <header className="flex flex-col gap-1 border-b border-white/5 pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="eyebrow mb-2">Capstone · Real-Time ISL Recognition</p>
        <h1 className="font-display text-3xl font-bold text-paper sm:text-4xl">
          ISL <span className="text-teal-400">Live</span>
        </h1>
        <p className="mt-2 max-w-md text-sm text-slate-400">
          Sign naturally — get instant word suggestions, formed sentences, and
          bilingual English–Telugu speech, no interpreter required.
        </p>
      </div>
      <div className="font-mono text-[11px] text-slate-500">
        session <span className="text-slate-400">{sessionId}</span>
      </div>
    </header>
  )
}
