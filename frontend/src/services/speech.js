/** Browser Text-to-Speech (SpeechSynthesis). No backend required. */

/** ALL-CAPS strings get spelled letter-by-letter by many voices — normalize to words. */
function asSpokenWords(text) {
  return (text || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word.toLowerCase())
    .join(" ");
}

/** Speak formed text as words (e.g. HELLO → "hello"). */
export function speakText(text) {
  const phrase = asSpokenWords(text);
  if (!phrase || !window.speechSynthesis) return;

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(phrase);
  utterance.rate = 0.95;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}

/** Speak a single ASL letter as soon as it is committed (e.g. H → "H"). */
export function speakLetter(letter) {
  const ch = (letter || "").trim().toUpperCase();
  if (!ch || ch === "NOTHING" || !window.speechSynthesis) return;

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(ch);
  utterance.rate = 1.05;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}
