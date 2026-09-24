export default function SignGuideGrid({ items = [], compact = false }) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">No guide photos in guide-photos/ yet.</p>;
  }
  return (
    <div className={`grid gap-3 ${compact ? "grid-cols-4 sm:grid-cols-6" : "grid-cols-3 sm:grid-cols-4 md:grid-cols-6"}`}>
      {items.map((item) => (
        <figure key={item.label} className="overflow-hidden rounded-xl border border-line bg-ink">
          <img src={item.image} alt={item.label} className="aspect-square w-full object-cover" />
          <figcaption className="px-2 py-1.5 text-center font-mono text-xs tracking-wide text-accent">
            {item.label}
          </figcaption>
        </figure>
      ))}
    </div>
  );
}
