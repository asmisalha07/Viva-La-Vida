import { Link } from "react-router-dom";

const PARTICLES = [
  { left: "12%", top: "18%", size: 3, delay: "0s", duration: "11s" },
  { left: "22%", top: "72%", size: 2, delay: "1.2s", duration: "13s" },
  { left: "38%", top: "28%", size: 4, delay: "0.4s", duration: "9s" },
  { left: "48%", top: "58%", size: 2, delay: "2.1s", duration: "12s" },
  { left: "58%", top: "16%", size: 3, delay: "0.8s", duration: "14s" },
  { left: "68%", top: "44%", size: 2, delay: "1.6s", duration: "10s" },
  { left: "74%", top: "78%", size: 3, delay: "2.8s", duration: "15s" },
  { left: "82%", top: "24%", size: 5, delay: "0.2s", duration: "11s" },
  { left: "88%", top: "62%", size: 2, delay: "1.9s", duration: "13s" },
  { left: "18%", top: "48%", size: 2, delay: "3.1s", duration: "12s" },
  { left: "92%", top: "38%", size: 3, delay: "0.6s", duration: "10s" },
  { left: "64%", top: "68%", size: 4, delay: "2.4s", duration: "14s" },
  { left: "8%", top: "82%", size: 2, delay: "1.1s", duration: "9s" },
  { left: "42%", top: "88%", size: 3, delay: "3.4s", duration: "16s" },
  { left: "78%", top: "12%", size: 2, delay: "1.5s", duration: "11s" },
  { left: "52%", top: "36%", size: 2, delay: "2.6s", duration: "12s" },
  { left: "30%", top: "14%", size: 3, delay: "0.9s", duration: "13s" },
  { left: "85%", top: "88%", size: 3, delay: "2s", duration: "10s" },
];

export default function HomePage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden
        style={{
          background:
            "radial-gradient(ellipse 90% 70% at 15% 20%, rgba(62,224,192,0.18), transparent 55%)," +
            "radial-gradient(ellipse 70% 60% at 90% 75%, rgba(122,162,255,0.14), transparent 50%)," +
            "linear-gradient(165deg, #070c16 0%, #0b1220 45%, #0e1829 100%)",
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.28]"
        aria-hidden
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px)," +
            "linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse at center, black 30%, transparent 75%)",
        }}
      />
      <div
        className="pointer-events-none absolute -left-24 top-1/4 h-72 w-72 rounded-full bg-accent/20 blur-3xl home-drift"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -right-16 bottom-1/4 h-80 w-80 rounded-full bg-accent2/15 blur-3xl home-drift-slow"
        aria-hidden
      />

      {/* Floating particles */}
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        {PARTICLES.map((p, i) => (
          <span
            key={i}
            className="home-particle absolute rounded-full"
            style={{
              left: p.left,
              top: p.top,
              width: p.size,
              height: p.size,
              animationDelay: p.delay,
              animationDuration: p.duration,
              background:
                i % 3 === 0
                  ? "rgba(62,224,192,0.85)"
                  : i % 3 === 1
                    ? "rgba(122,162,255,0.75)"
                    : "rgba(255,255,255,0.55)",
              boxShadow:
                i % 3 === 0
                  ? "0 0 10px rgba(62,224,192,0.45)"
                  : i % 3 === 1
                    ? "0 0 10px rgba(122,162,255,0.4)"
                    : "0 0 6px rgba(255,255,255,0.25)",
            }}
          />
        ))}
      </div>

      <main className="relative mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16 md:px-10">
        <div className="home-rise">
          <h1 className="font-display text-5xl font-medium leading-[1.05] tracking-tight text-white md:text-6xl lg:text-7xl">
            Sign Language
            <span className="block text-accent">Converter</span>
          </h1>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-slate-300">
            One hand sign in the camera becomes a word on screen — then spoken aloud.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Link
              to="/convert"
              className="rounded-lg bg-accent px-7 py-3.5 text-base font-semibold text-ink transition hover:brightness-110"
            >
              Open live converter
            </Link>
            <span className="font-mono text-xs tracking-wide text-slate-500">
              Webcam · landmarks · speech
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}
