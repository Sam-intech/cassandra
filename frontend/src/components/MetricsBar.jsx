import { classifyAlert, formatPrice, formatTimestamp, formatVpin } from "../lib/format";

const ALERT_STYLES = {
  NORMAL: "text-signal-mint border-signal-mint/40 bg-signal-mint/10",
  MODERATE: "text-signal-amber border-signal-amber/40 bg-signal-amber/10",
  ELEVATED: "text-signal-amber border-signal-amber/40 bg-signal-amber/10",
  HIGH: "text-signal-red border-signal-red/40 bg-signal-red/10",
  CRITICAL: "text-signal-red border-signal-red/40 bg-signal-red/10",
};

function MetricCard({ label, value, hint }) {
  return (
    <article className="rounded-2xl border border-white/10 bg-ink-900/80 px-4 py-3 backdrop-blur-sm">
      <p className="font-mono text-xs uppercase tracking-widest text-white/55">{label}</p>
      <p className="mt-2 text-xl font-semibold text-white">{value}</p>
      {hint ? <p className="mt-1 font-mono text-xs text-white/45">{hint}</p> : null}
    </article>
  );
}

export default function MetricsBar({ status, latestUpdate, isConnected }) {
  const currentVpin = status?.current_vpin ?? latestUpdate?.vpin ?? null;
  const alertLevel = classifyAlert(currentVpin);
  const alertStyle = ALERT_STYLES[alertLevel] || ALERT_STYLES.NORMAL;

  return (
    <section className="animate-rise space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold tracking-tight text-white">CASSANDRA Intelligence Terminal</h1>
        <span
          className={`rounded-full border px-3 py-1 font-mono text-xs uppercase tracking-wide ${
            isConnected
              ? "border-signal-cyan/45 bg-signal-cyan/15 text-signal-cyan"
              : "border-signal-red/45 bg-signal-red/15 text-signal-red"
          }`}
        >
          {isConnected ? "stream online" : "stream offline"}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard
          label="VPIN"
          value={formatVpin(currentVpin)}
          hint={`Last tick ${formatTimestamp(latestUpdate?.timestamp)}`}
        />
        <MetricCard
          label="Alert"
          value={<span className={`rounded-md border px-2 py-1 text-base ${alertStyle}`}>{alertLevel}</span>}
          hint="Order flow toxicity"
        />
        <MetricCard
          label="Latest Price"
          value={formatPrice(status?.latest_price ?? latestUpdate?.latest_price)}
          hint="BTCUSDT"
        />
        <MetricCard
          label="Trades"
          value={(status?.trade_count ?? latestUpdate?.trade_count ?? 0).toLocaleString()}
          hint="Processed in stream"
        />
        <MetricCard
          label="Clients"
          value={String(status?.connected_clients ?? 0)}
          hint={status?.streaming ? "Backend streaming" : "Backend idle"}
        />
      </div>
    </section>
  );
}
