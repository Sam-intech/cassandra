import { makeLinePath, yForThreshold } from "../lib/chart";
import { formatTimestamp, formatVpin } from "../lib/format";

const WIDTH = 760;
const HEIGHT = 260;

export default function LiveChart({
  data,
  currentVpin,
  connectionError,
  isConnected,
  streaming = false,
  streamButtonLabel = "start streaming",
  onStreamButtonClick,
  onResetSystem,
  streamActionLoading = false,
  streamActionError = "",
}) {
  const path = makeLinePath(data, WIDTH, HEIGHT);
  const markerX = WIDTH - 14;
  const markerY = yForThreshold(currentVpin ?? 0.5, WIDTH, HEIGHT);
  const streamOnline = streaming && isConnected;

  return (
    <section className="animate-rise rounded-3xl border border-slate-200 bg-white/90 p-5 shadow-[0_18px_42px_-30px_rgba(15,23,42,0.45)] backdrop-blur-sm">
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.25em] text-cyan-700">Live VPIN</p>
          <h2 className="font-display text-xl font-semibold text-slate-900">Real-time toxicity curve</h2>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span
            className={`rounded-full border px-3 py-1 font-mono text-[10px] uppercase tracking-wide ${
              streamOnline
                ? "border-cyan-300 bg-cyan-50 text-cyan-700"
                : "border-red-300 bg-red-50 text-red-700"
            }`}
          >
            {streamOnline ? "stream online" : "stream offline"}
          </span>
          <p className="font-mono text-xs text-slate-500">
            {data.length > 0
              ? `Updated ${formatTimestamp(data[data.length - 1].timestamp)}`
              : streaming
                ? "streaming..."
                : "Waiting for stream..."}
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-b from-white to-slate-100 p-2">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-64 w-full">
          <line x1="14" y1={yForThreshold(0.85, WIDTH, HEIGHT)} x2="746" y2={yForThreshold(0.85, WIDTH, HEIGHT)} stroke="#ff5a5f" strokeDasharray="4 6" strokeOpacity="0.7" />
          <line x1="14" y1={yForThreshold(0.75, WIDTH, HEIGHT)} x2="746" y2={yForThreshold(0.75, WIDTH, HEIGHT)} stroke="#ffbe0b" strokeDasharray="4 6" strokeOpacity="0.7" />
          <line x1="14" y1={yForThreshold(0.65, WIDTH, HEIGHT)} x2="746" y2={yForThreshold(0.65, WIDTH, HEIGHT)} stroke="#8ce99a" strokeDasharray="4 6" strokeOpacity="0.45" />
          {path ? (
            <>
              <polyline points={path} fill="none" stroke="#40e0d0" strokeWidth="2.8" strokeLinejoin="round" strokeLinecap="round" />
              <circle cx={markerX} cy={markerY} r="5" fill="#40e0d0" />
            </>
          ) : null}
        </svg>
      </div>

      <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 font-mono text-xs text-slate-600">
          <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1">points: {data.length}</span>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1">current: {formatVpin(currentVpin)}</span>
          {connectionError ? <span className="rounded-full border border-red-300 bg-red-50 px-2 py-1 text-red-700">{connectionError}</span> : null}
          {streamActionError ? <span className="rounded-full border border-red-300 bg-red-50 px-2 py-1 text-red-700">{streamActionError}</span> : null}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={onStreamButtonClick}
            disabled={streamActionLoading}
            className={`rounded-xl border px-4 py-2 font-mono text-xs uppercase tracking-[0.16em] transition ${
              streaming
                ? "border-red-600 bg-red-600 text-white shadow-[0_16px_30px_-20px_rgba(239,68,68,0.85)]"
                : "border-cyan-600 bg-cyan-600 text-white"
            } disabled:cursor-not-allowed disabled:opacity-60`}
          >
            {streamActionLoading ? "updating..." : streamButtonLabel}
          </button>
          <button
            type="button"
            onClick={() => onResetSystem?.()}
            disabled={streamActionLoading}
            title="Reset system and clear runtime data"
            className="grid h-9 w-9 place-items-center rounded-xl border border-slate-300 bg-white text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden="true">
              <path d="M3 10a7 7 0 1 0 2-4.9" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              <path d="M3 3v4h4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    </section>
  );
}
