export default function StatusBadge({ health, error }) {
  const ready = health?.model_loaded;
  const label = error
    ? "Camera / API error"
    : !health
      ? "Connecting to API…"
      : ready
        ? "Model ready"
        : "API up · model not trained";

  const color = error
    ? "bg-red-500/20 text-red-200"
    : ready
      ? "bg-accent/15 text-accent"
      : "bg-amber-400/15 text-amber-200";

  return (
    <span className={`rounded-full px-3 py-1 font-mono text-xs ${color}`}>{label}</span>
  );
}
