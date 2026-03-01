import { makeLinePath, yForThreshold } from "../lib/chart";
import { formatTimestamp, formatVpin } from "../lib/format";

const WIDTH = 760;
const HEIGHT = 260;

export default function LiveChart({ data, currentVpin, connectionError }) {
  const path = makeLinePath(data, WIDTH, HEIGHT);
  const markerX = WIDTH - 14;
  const markerY = yForThreshold(currentVpin ?? 0.5, WIDTH, HEIGHT);

  return (
    <section className="animate-rise rounded-3xl border border-white/10 bg-ink-900/85 p-5 shadow-glow backdrop-blur-sm">
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.25em] text-signal-cyan">Live VPIN</p>
          <h2 className="font-display text-xl font-semibold text-white">Real-time toxicity curve</h2>
        </div>
        <p className="font-mono text-xs text-white/60">
          {data.length > 0 ? `Updated ${formatTimestamp(data[data.length - 1].timestamp)}` : "Waiting for stream..."}
        </p>
      </div>

      <div className="overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-ink-800/80 to-ink-950/95 p-2">
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

      <div className="mt-3 flex flex-wrap items-center gap-3 font-mono text-xs text-white/65">
        <span className="rounded-full border border-white/15 px-2 py-1">points: {data.length}</span>
        <span className="rounded-full border border-white/15 px-2 py-1">current: {formatVpin(currentVpin)}</span>
        {connectionError ? <span className="rounded-full border border-signal-red/35 px-2 py-1 text-signal-red">{connectionError}</span> : null}
      </div>
    </section>
  );
}
