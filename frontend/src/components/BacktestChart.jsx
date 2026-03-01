import { makeLinePath, yForThreshold } from "../lib/chart";
import { formatTimestamp, formatVpin } from "../lib/format";

const WIDTH = 760;
const HEIGHT = 260;

export default function BacktestChart({ data, events, summary, loading, error }) {
  const sampled = data.length > 360 ? data.filter((_, idx) => idx % Math.ceil(data.length / 360) === 0) : data;
  const path = makeLinePath(sampled, WIDTH, HEIGHT);

  return (
    <section className="animate-rise rounded-3xl border border-white/10 bg-ink-900/85 p-5 backdrop-blur-sm">
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.25em] text-signal-amber">Backtest</p>
          <h2 className="font-display text-xl font-semibold text-white">FTX collapse replay</h2>
        </div>
        {summary ? <p className="font-mono text-xs text-white/60">peak vpin {formatVpin(Number(summary.peak_vpin))}</p> : null}
      </div>

      <div className="overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-ink-800/80 to-ink-950/95 p-2">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-64 w-full">
          <line x1="14" y1={yForThreshold(0.7, WIDTH, HEIGHT)} x2="746" y2={yForThreshold(0.7, WIDTH, HEIGHT)} stroke="#ffbe0b" strokeDasharray="4 6" strokeOpacity="0.8" />
          {path ? <polyline points={path} fill="none" stroke="#ffbe0b" strokeWidth="2.8" strokeLinejoin="round" strokeLinecap="round" /> : null}
        </svg>
      </div>

      {loading ? <p className="mt-3 font-mono text-xs text-white/60">Loading backtest...</p> : null}
      {error ? <p className="mt-3 font-mono text-xs text-signal-red">{error}</p> : null}

      {!loading && !error ? (
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          <div className="rounded-xl border border-white/10 bg-ink-950/50 p-3">
            <p className="font-mono text-xs uppercase tracking-wide text-white/55">Summary</p>
            <p className="mt-2 font-mono text-sm text-white/85">Buckets: {summary?.total_buckets ?? "-"}</p>
            <p className="font-mono text-sm text-white/85">Peak timestamp: {formatTimestamp(summary?.peak_timestamp)}</p>
            <p className="font-mono text-sm text-white/85">Lead time: {summary?.minutes_before_public ?? "-"}m before public signal</p>
          </div>

          <div className="rounded-xl border border-white/10 bg-ink-950/50 p-3">
            <p className="font-mono text-xs uppercase tracking-wide text-white/55">Event markers</p>
            <ul className="mt-2 space-y-1">
              {(events || []).slice(0, 3).map((event) => (
                <li key={event.timestamp} className="font-mono text-xs text-white/80">
                  {formatTimestamp(event.timestamp)} · {event.label}
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </section>
  );
}
