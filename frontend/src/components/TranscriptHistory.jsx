export default function TranscriptHistory({ entries }) {
  return (
    <div className="panel flex flex-col gap-3 p-4">
      <div className="flex items-center justify-between">
        <p className="eyebrow">Conversation transcript</p>
        <span className="font-mono text-[10px] text-slate-500">for the person you're speaking with</span>
      </div>

      <div className="flex max-h-64 flex-col gap-2 overflow-y-auto pr-1">
        {entries.length === 0 && (
          <span className="font-mono text-xs text-slate-500">
            Completed sentences will appear here as a running log.
          </span>
        )}
        {entries
          .slice()
          .reverse()
          .map((e, i) => (
            <div
              key={i}
              className="animate-rise rounded-lg border border-white/5 bg-ink-950/50 px-3 py-2"
            >
              <div className="flex items-center justify-between">
                <span className="font-body text-sm text-paper">{e.english}</span>
                <span className="font-mono text-[10px] text-slate-500">{e.time}</span>
              </div>
              {e.telugu && <span className="mt-0.5 block text-xs text-amber-400/80">{e.telugu}</span>}
            </div>
          ))}
      </div>
    </div>
  )
}
