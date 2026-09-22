import { useEffect, useRef } from "react";

/**
 * Live camera with a center guide that matches the backend ROI crop.
 */
export default function WebcamFeed({ running, videoRef, onError }) {
  const streamRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function start() {
      try {
        // Keep constraints loose — strict width/height often times out on some laptops.
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
          video.muted = true;
          video.playsInline = true;
          try {
            await video.play();
          } catch {
            // autoPlay + muted usually still shows frames even if play() rejects.
          }
        }
        onError?.("");
      } catch (err) {
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        onError?.(err.message || "Camera permission was denied.");
      }
    }

    if (running) start();

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;
    };
    // onError intentionally omitted — unstable parent callbacks remounted the stream and blinked the camera.
  }, [running, videoRef]);

  return (
    <div className="relative overflow-hidden rounded-2xl border border-line bg-black">
      <video
        ref={videoRef}
        className="aspect-[4/3] w-full -scale-x-100 object-cover"
        playsInline
        muted
        autoPlay
      />
      {!running && (
        <div className="absolute inset-0 flex items-center justify-center bg-ink/70 text-sm text-slate-300">
          Camera is off
        </div>
      )}
      {running && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="guide-box h-[55%] max-h-[280px] w-[55%] max-w-[280px] rounded-xl border-2 border-accent/90" />
        </div>
      )}
      <p className="absolute bottom-3 left-3 rounded-md bg-ink/70 px-2 py-1 font-mono text-[11px] tracking-wide text-accent">
        Place hand inside the box
      </p>
    </div>
  );
}

/** Grab a JPEG data URL from the visible video frame (un-mirrored, matching OpenCV). */
export function captureFrame(videoEl) {
  if (!videoEl || videoEl.readyState < 2) return null;
  const canvas = document.createElement("canvas");
  canvas.width = videoEl.videoWidth || 640;
  canvas.height = videoEl.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  // Mirror to match the on-screen preview and collect_samples.py.
  ctx.translate(canvas.width, 0);
  ctx.scale(-1, 1);
  ctx.drawImage(videoEl, 0, 0);
  return canvas.toDataURL("image/jpeg", 0.92);
}
