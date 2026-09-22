export default function WordBuilder({ word, sentence, onClear, onSpeak, onSpace, demoMode }) {
  const spoken = demoMode ? sentence : [sentence, word].filter(Boolean).join(" ");

  return (
    <div className="rounded-2xl border border-line bg-panel p-5">
      <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-400">
        {demoMode ? "Sentence" : "Formed text"}
      </p>
      <p className="mt-3 min-h-[2.5rem] font-display text-3xl tracking-[0.12em] text-accent">
        {demoMode ? sentence || word || "…" : word || "…"}
      </p>
      {!demoMode && (
        <p className="mt-2 min-h-[1.5rem] text-slate-300">
          {sentence || "Letters lock into the word. Rest pose (nothing) inserts a space."}
        </p>
      )}
      {demoMode && (
        <p className="mt-2 min-h-[1.5rem] text-sm text-slate-400">
          {sentence
            ? "Drop your hand (nothing), then sign again to add the next word."
            : "Sign one word at a time. Try WHAT IS YOUR NAME or HOW ARE YOU after those signs are trained."}
        </p>
      )}
      <div className="mt-5 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onSpeak}
          disabled={!spoken}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-ink disabled:opacity-40"
        >
          Speak
        </button>
        {!demoMode && (
          <button
            type="button"
            onClick={onSpace}
            className="rounded-lg border border-line px-4 py-2 text-sm text-slate-200"
          >
            End word
          </button>
        )}
        <button
          type="button"
          onClick={onClear}
          className="rounded-lg border border-line px-4 py-2 text-sm text-slate-200"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
