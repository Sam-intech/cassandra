import { formatTimestamp } from "../lib/format";
import { Fragment } from "react";

function renderInline(text) {
  const chunks = String(text).split(/(\*\*.*?\*\*)/g);
  return chunks.map((chunk, index) => {
    if (chunk.startsWith("**") && chunk.endsWith("**")) {
      return (
        <strong key={`${chunk}-${index}`} className="font-bold text-slate-900">
          {chunk.slice(2, -2)}
        </strong>
      );
    }
    return <Fragment key={`${chunk}-${index}`}>{chunk}</Fragment>;
  });
}

function renderBriefLine(line, index) {
  const text = line.trim();
  if (!text) {
    return <div key={`spacer-${index}`} className="h-2" />;
  }

  if (text.startsWith("### ") || text.startsWith("## ") || text.startsWith("# ")) {
    return (
      <h3 key={`heading-${index}`} className="font-display text-sm font-bold uppercase tracking-wide text-slate-900">
        {renderInline(text.replace(/^#+\s*/, ""))}
      </h3>
    );
  }

  if (text.startsWith("- ") || text.startsWith("* ")) {
    return (
      <p key={`bullet-${index}`} className="pl-3 text-sm leading-6 text-slate-700">
        <span className="mr-2 text-cyan-700">•</span>
        {renderInline(text.slice(2))}
      </p>
    );
  }

  return (
    <p key={`line-${index}`} className="text-sm leading-6 text-slate-700">
      {renderInline(text)}
    </p>
  );
}

function Placeholder() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="font-display text-lg font-semibold text-slate-900">No brief yet</p>
      <p className="mt-2 text-sm text-slate-600">
        The brief appears here after the stream raises a meaningful VPIN alert and the intelligence agent responds.
      </p>
    </div>
  );
}

export default function IntelligenceBrief({ brief, error }) {
  return (
    <section className="animate-rise rounded-3xl border border-slate-200 bg-white/95 p-5 shadow-[0_18px_42px_-30px_rgba(15,23,42,0.45)] backdrop-blur-sm">
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">Cassandra</p>
          <h2 className="font-display text-xl font-semibold text-slate-900">Brief</h2>
        </div>
        {brief?.timestamp ? (
          <p className="font-mono text-xs text-slate-500">Generated {formatTimestamp(brief.timestamp)}</p>
        ) : null}
      </div>

      {!brief ? (
        <Placeholder />
      ) : (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2 font-mono text-xs">
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-slate-700">VPIN {brief.vpin_score?.toFixed?.(4) ?? "-"}</span>
            <span className="rounded-full border border-red-300 bg-red-50 px-3 py-1 text-red-700">{brief.alert_level || "-"}</span>
            {/* <span className="rounded-full border border-white/15 bg-ink-950/50 px-3 py-1 text-white/80">tools {brief.tools_called?.length ?? 0}</span> */}
          </div>

          <article className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="space-y-1 font-display">
              {(brief.intelligence_brief || "No generated brief text found.")
                .split("\n")
                .map((line, index) => renderBriefLine(line, index))}
            </div>
          </article>
        </div>
      )}
      {error ? <p className="mt-3 font-mono text-xs text-red-700">{error}</p> : null}
    </section>
  );
}
