export default function PredictionPanel({ letter, confidencePercent, modelReady, top3 = [], holding = false }) {
  const isSpace = letter === "space" || letter === " ";
  const noHand = letter === "nothing" && !(confidencePercent > 0);
  const pause = letter === "nothing" && confidencePercent > 0;
  const display = isSpace ? "␣" : letter && letter !== "nothing" ? letter : "—";
  const others =
    letter && letter !== "nothing"
      ? (top3 || []).filter((row) => row.label && row.label !== letter).slice(0, 2)
      : [];

  let hint = "Waiting for trained model";
  if (modelReady && noHand) hint = "No hand yet — hold the sign still in the box";
  else if (modelReady && pause) hint = "Hold still… locking when the bar fills";
  else if (modelReady && isSpace) hint = "Space added. Drop your hand, then the next letter.";
  else if (modelReady && holding) hint = "Locked. Drop your hand before the next letter.";
  else if (modelReady) hint = "Sign locked";

  const barLabel = pause ? "Hold still" : "Confidence";

  return (
    <div className="rounded-2xl border border-line bg-panel p-5">
      <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-400">Predicted sign</p>
      <p className={`mt-3 font-display font-medium text-white ${display.length > 2 ? "text-5xl" : "text-7xl"}`}>
        {display}
      </p>
      <p className="mt-2 text-sm text-slate-400">{hint}</p>
      <div className="mt-5">
        <div className="mb-1 flex justify-between font-mono text-xs text-slate-400">
          <span>{barLabel}</span>
          <span>{Number.isFinite(confidencePercent) ? `${confidencePercent}%` : "—"}</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-ink">
          <div
            className="h-full rounded-full bg-accent transition-all duration-200"
            style={{ width: `${Math.min(100, confidencePercent || 0)}%` }}
          />
        </div>
      </div>
      {others.length > 0 && (
        <p className="mt-3 font-mono text-xs text-slate-500">
          Also considering {others.map((row) => `${row.label} ${row.percent}%`).join(" · ")}
        </p>
      )}
    </div>
  );
}
