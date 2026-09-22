import { Link } from "react-router-dom";
import StatusBadge from "./StatusBadge.jsx";

export default function Header({ health, error }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-6 py-4">
      <Link to="/" className="font-display text-xl text-white">
        Sign Language Converter
      </Link>
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge health={health} error={error} />
      </div>
    </header>
  );
}
