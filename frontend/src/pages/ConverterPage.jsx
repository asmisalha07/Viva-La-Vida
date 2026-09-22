import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import Header from "../components/Header.jsx";
import PredictionPanel from "../components/PredictionPanel.jsx";
import WebcamFeed, { captureFrame } from "../components/WebcamFeed.jsx";
import WordBuilder from "../components/WordBuilder.jsx";
import SignGuideGrid from "../components/SignGuideGrid.jsx";
import { getGuide, getHealth, predictFrame } from "../services/api.js";
import { speakLetter, speakText } from "../services/speech.js";

/** Need a clear winner held still before locking a letter. */
const STABLE_LETTERS = 4;
const STABLE_WORDS = 2;
const CONFIDENCE_MIN_LETTERS = 0.4;
const CONFIDENCE_MIN_WORDS = 0.5;
const MARGIN_MIN_LETTERS = 0.08;
const MARGIN_MIN_WORDS = 0.08;
const POLL_LETTERS_MS = 420;
const POLL_WORDS_MS = 260;
const WORD_RELEASE_NEEDED = 3;

function isPause(label) {
  const x = (label || "").toLowerCase();
  return !label || x === "nothing";
}

function isSpaceSign(label) {
  const x = (label || "").toLowerCase();
  return x === "space";
}

export default function ConverterPage() {
  const videoRef = useRef(null);
  const lockedLetter = useRef(null);
  const releaseCount = useRef(0);
  const stable = useRef({ letter: null, count: 0 });
  const demoSpoken = useRef(false);

  const [mode, setMode] = useState("letters"); // "words" | "letters"
  const [cameraOn, setCameraOn] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [health, setHealth] = useState(null);
  const [guide, setGuide] = useState({ letters: [], words: [] });
  const [error, setError] = useState("");
  const [letter, setLetter] = useState("");
  const [confidence, setConfidence] = useState(0);
  const [top3, setTop3] = useState([]);
  const [roiPreview, setRoiPreview] = useState("");
  const [word, setWord] = useState("");
  const [sentence, setSentence] = useState("");
  const busyRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    const checkHealth = () => {
      getHealth()
        .then((data) => {
          if (cancelled) return;
          setHealth(data);
          setError((prev) =>
            prev.startsWith("Cannot reach FastAPI") || prev === "Model is not ready yet."
              ? ""
              : prev
          );
        })
        .catch(() => {
          if (cancelled) return;
          setHealth(null);
          setError("Cannot reach FastAPI. Start: uvicorn main:app --port 8000");
        });
      getGuide()
        .then((data) => {
          if (!cancelled) setGuide(data);
        })
        .catch(() => {});
    };

    checkHealth();
    const id = setInterval(checkHealth, 4000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const handleCameraError = useCallback((message) => {
    setError(message);
  }, []);

  const resetPredictionHold = useCallback(() => {
    lockedLetter.current = null;
    releaseCount.current = 0;
    stable.current = { letter: null, count: 0 };
    demoSpoken.current = false;
  }, []);

  const markReleased = useCallback(() => {
    lockedLetter.current = null;
    releaseCount.current = 0;
    demoSpoken.current = false;
  }, []);

  const stopPrediction = useCallback(() => {
    setPredicting(false);
    resetPredictionHold();
    setLetter("");
    setConfidence(0);
    setTop3([]);
  }, [resetPredictionHold]);

  const startPrediction = useCallback(() => {
    const lettersOk = Boolean(health?.letters_ready);
    const wordsOk = Boolean(health?.words_ready);
    if (mode === "letters" && !lettersOk) {
      setError("Letters model not trained. In backend: python model/train.py --source letters");
      return;
    }
    if (mode === "words" && !wordsOk) {
      setError("Words model not trained. Collect word signs, then: python model/train.py --source words");
      return;
    }
    setError("");
    setCameraOn(true);
    resetPredictionHold();
    setPredicting(true);
  }, [health, mode, resetPredictionHold]);

  const toggleCamera = useCallback(() => {
    setCameraOn((on) => {
      if (on) {
        setPredicting(false);
        resetPredictionHold();
        setLetter("");
        setConfidence(0);
        setTop3([]);
        return false;
      }
      return true;
    });
  }, [resetPredictionHold]);

  const switchMode = useCallback(
    (next) => {
      setMode(next);
      setPredicting(false);
      setWord("");
      setSentence("");
      resetPredictionHold();
      setLetter("");
      setConfidence(0);
      setTop3([]);
      setError("");
    },
    [resetPredictionHold]
  );

  const commitSpace = useCallback(() => {
    if (word) {
      setSentence((s) => (s ? `${s} ${word}` : word));
    }
    setWord("");
    markReleased();
    stable.current = { letter: null, count: 0 };
  }, [word, markReleased]);

  /** One trained sign → that word, then speak it. */
  const ingestWord = useCallback(
    (nextLetter, nextConfidence, nextMargin = 1) => {
      const weak = nextConfidence < CONFIDENCE_MIN_WORDS || nextMargin < MARGIN_MIN_WORDS;

      if (weak || isPause(nextLetter) || nextLetter.length === 1) {
        stable.current = { letter: null, count: 0 };
        if (lockedLetter.current) {
          releaseCount.current += 1;
          if (releaseCount.current >= WORD_RELEASE_NEEDED) markReleased();
        }
        return false;
      }

      const spokenWord = nextLetter;

      if (lockedLetter.current === spokenWord) {
        releaseCount.current = 0;
        return false;
      }

      if (stable.current.letter === spokenWord) {
        stable.current.count += 1;
      } else {
        stable.current = { letter: spokenWord, count: 1 };
      }
      if (stable.current.count < STABLE_WORDS) return false;

      setWord(spokenWord);
      setSentence((s) => (s ? `${s} ${spokenWord}` : spokenWord));
      lockedLetter.current = spokenWord;
      releaseCount.current = 0;
      speakText(spokenWord);
      stable.current = { letter: null, count: 0 };
      return true;
    },
    [markReleased]
  );

  const ingestSpell = useCallback(
    (nextLetter, nextConfidence, nextMargin = 1, handDetected = true) => {
      if (!handDetected) {
        stable.current = { letter: null, count: 0 };
        if (lockedLetter.current) markReleased();
        return false;
      }

      const weak = nextConfidence < CONFIDENCE_MIN_LETTERS || nextMargin < MARGIN_MIN_LETTERS;
      const space = isSpaceSign(nextLetter);

      if (!space && (weak || isPause(nextLetter) || nextLetter.length > 1)) {
        stable.current = { letter: null, count: 0 };
        if (lockedLetter.current) markReleased();
        return false;
      }

      const token = space ? " " : nextLetter;

      if (lockedLetter.current === token) {
        releaseCount.current = 0;
        stable.current = { letter: null, count: 0 };
        return false;
      }

      if (stable.current.letter === token) {
        stable.current.count += 1;
      } else {
        stable.current = { letter: token, count: 1 };
      }
      if (stable.current.count < STABLE_LETTERS) return false;

      if (space) {
        setWord((w) => {
          if (!w || w.endsWith(" ")) return w;
          return `${w} `;
        });
      } else {
        setWord((w) => w + token);
        speakLetter(token);
      }
      lockedLetter.current = token;
      releaseCount.current = 0;
      stable.current = { letter: null, count: 0 };
      return true;
    },
    [markReleased]
  );

  const ingest = useCallback(
    (nextLetter, nextConfidence, nextMargin = 1, handDetected = true) => {
      if (mode === "words") {
        return ingestWord(nextLetter, nextConfidence, nextMargin);
      }
      return ingestSpell(nextLetter, nextConfidence, nextMargin, handDetected);
    },
    [mode, ingestWord, ingestSpell]
  );

  useEffect(() => {
    if (!cameraOn || !predicting) return undefined;
    const apiMode = mode === "words" ? "words" : "letters";
    const pollMs = apiMode === "words" ? POLL_WORDS_MS : POLL_LETTERS_MS;
    const id = setInterval(async () => {
      if (busyRef.current) return;
      const image = captureFrame(videoRef.current);
      if (!image) return;
      busyRef.current = true;
      try {
        const result = await predictFrame(image, apiMode);
        const shown = result.letter || "";
        const locked = ingest(
          shown,
          result.confidence,
          result.margin,
          Boolean(result.hand_detected)
        );
        if (apiMode === "words") {
          setLetter(shown);
          setConfidence(
            Number.isFinite(result.confidence_percent) ? result.confidence_percent : 0
          );
          setTop3(Array.isArray(result.top3) ? result.top3 : []);
        } else if (locked) {
          setLetter(shown);
          setConfidence(
            Number.isFinite(result.confidence_percent) ? result.confidence_percent : 0
          );
          setTop3([]);
        } else if (lockedLetter.current) {
          setTop3([]);
        } else if (isPause(shown) || !shown) {
          setLetter("nothing");
          setConfidence(0);
          setTop3([]);
        } else {
          setLetter("nothing");
          const held = stable.current.letter === shown ? stable.current.count : 0;
          setConfidence(Math.round((held / STABLE_LETTERS) * 100));
          setTop3([]);
        }
        if (result.roi_preview) {
          setRoiPreview(`data:image/jpeg;base64,${result.roi_preview}`);
        }
        setError("");
      } catch (err) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Prediction failed.");
      } finally {
        busyRef.current = false;
      }
    }, pollMs);
    return () => clearInterval(id);
  }, [cameraOn, predicting, mode, ingest]);

  const isWords = mode === "words";
  const spoken = isWords ? sentence : [sentence, word].filter(Boolean).join(" ");
  const tabReady = isWords ? health?.words_ready : health?.letters_ready;

  return (
    <div className="min-h-screen">
      <Header health={health} error={error} />
      <main className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[1.15fr_0.85fr]">
        <section>
          <WebcamFeed
            running={cameraOn}
            videoRef={videoRef}
            onError={handleCameraError}
          />
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => switchMode("words")}
              className={`rounded-lg px-4 py-2 text-sm font-semibold ${
                isWords ? "bg-accent text-ink" : "border border-line text-slate-300"
              }`}
            >
              Words
            </button>
            <button
              type="button"
              onClick={() => switchMode("letters")}
              className={`rounded-lg px-4 py-2 text-sm font-semibold ${
                !isWords ? "bg-accent text-ink" : "border border-line text-slate-300"
              }`}
            >
              Letters
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={toggleCamera}
              className="rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-ink"
            >
              {cameraOn ? "Stop camera" : "Start camera"}
            </button>
            <button
              type="button"
              onClick={() => (predicting ? stopPrediction() : startPrediction())}
              disabled={!tabReady}
              className={`rounded-lg px-5 py-2.5 text-sm font-semibold disabled:opacity-40 ${
                predicting
                  ? "border border-red-400/70 bg-red-500/20 text-red-100"
                  : "bg-accent text-ink"
              }`}
            >
              {predicting ? "Stop prediction" : "Start prediction"}
            </button>
            <Link to="/" className="rounded-lg border border-line px-5 py-2.5 text-sm text-slate-300">
              Back
            </Link>
          </div>
          <p className="mt-3 font-mono text-xs tracking-wide text-slate-400">
            {isWords
              ? tabReady
                ? `Words: ${(health?.word_classes || []).join(" · ") || "HELLO · PLEASE"}. Drop the hand between signs. Try: WHAT IS YOUR NAME · HOW ARE YOU · MY NAME IS`
                : "Words: python model/collect_samples.py --sentences   then   python model/train.py --source words"
              : tabReady
                ? "Letters: hold a pose still until it locks. Rest pose (nothing) adds a space. Drop the hand before the next letter."
                : "Letters: train with python model/train.py --source letters"}
          </p>
          {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
          <div className="mt-8 rounded-2xl border border-line bg-panel p-4">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-400">
              {isWords ? "Word signs (your training photos)" : "Letter signs (your training photos)"}
            </p>
            <p className="mt-1 mb-4 text-sm text-slate-500">
              Scroll and copy the pose for this tab.
            </p>
            <SignGuideGrid items={isWords ? guide.words : guide.letters} compact />
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <PredictionPanel
            letter={letter}
            confidencePercent={confidence}
            modelReady={Boolean(tabReady)}
            top3={top3}
            holding={!isWords && predicting && letter !== "nothing"}
          />
          <WordBuilder
            word={word}
            sentence={sentence}
            demoMode={isWords}
            onSpeak={() => speakText(spoken)}
            onSpace={commitSpace}
            onClear={() => {
              setWord("");
              setSentence("");
              resetPredictionHold();
            }}
          />
          {roiPreview && (
            <div className="rounded-2xl border border-line bg-panel p-4">
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-400">
                Hand crop (preview)
              </p>
              <img src={roiPreview} alt="Preprocessed hand crop" className="mt-3 w-28 rounded-lg" />
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
