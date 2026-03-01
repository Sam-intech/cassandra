import { useMemo, useState } from "react";
import BacktestChart from "./components/BacktestChart";
import ChatInterface from "./components/ChatInterface";
import Header from "./components/Header";
import IntelligenceBrief from "./components/IntelligenceBrief";
import LiveChart from "./components/LiveChart";
import MetricsBar from "./components/MetricsBar";
import { useAgentChat } from "./hooks/useAgentChat";
import { useBacktestData } from "./hooks/useBacktestData";
import { useIntelligenceBrief } from "./hooks/useIntelligenceBrief";
import { useStreamStatus } from "./hooks/useStreamStatus";
import { useVpinStream } from "./hooks/useVpinStream";

export default function App() {
  const { status, setStreaming, resetSystem, actionLoading, actionError } = useStreamStatus();
  const { data: backtestData, events, summary, loading: backtestLoading, error: backtestError } = useBacktestData();
  const { brief, error: briefError, setBrief } = useIntelligenceBrief();
  const { livePoints, latestUpdate, latestBrief, currentVpin, isConnected, connectionError, clearStreamData } = useVpinStream();
  const { messages, isSending, error: chatError, sendMessage, resetConversation } = useAgentChat();
  const [streamControlMode, setStreamControlMode] = useState("start");
  const [showLanding, setShowLanding] = useState(true);

  const activeBrief = latestBrief || brief;
  const streaming = Boolean(status?.streaming);

  const streamButtonLabel = useMemo(() => {
    if (streaming) return "stop streaming";
    if (streamControlMode === "resume") return "resume streaming";
    return "start streaming";
  }, [streaming, streamControlMode]);

  const handleStreamButtonClick = async () => {
    if (streaming) {
      const ok = await setStreaming(false);
      if (ok) setStreamControlMode("resume");
      return;
    }

    const ok = await setStreaming(true);
    if (ok && streamControlMode === "start") {
      setStreamControlMode("resume");
    }
  };

  const handleResetSystem = async () => {
    const ok = await resetSystem(false);
    if (!ok) return;

    clearStreamData();
    setBrief(null);
    resetConversation();
    setStreamControlMode("start");
    setShowLanding(true);
  };

  const handleLandingStart = async () => {
    const ok = await setStreaming(true);
    if (!ok) return;
    setStreamControlMode("resume");
    setShowLanding(false);
  };

  // ============================
  // App main layout start here
  if (showLanding) {
    return (
      <main className="relative min-h-screen overflow-x-hidden bg-slate-50 px-4 py-8 text-slate-900 sm:px-8 lg:px-12">
        <div className="pointer-events-none absolute -top-32 -left-20 h-80 w-80 rounded-full bg-cyan-300/30 blur-3xl" />
        <div className="pointer-events-none absolute right-0 bottom-0 h-96 w-96 rounded-full bg-rose-300/30 blur-3xl" />

        <section className="mx-auto flex flex-col justify-center items-center mt-12 max-w-6xl p-8">
          <h1 className="font-display text-6xl font-bold leading-[0.9] tracking-tight text-slate-900 drop-shadow-[0_12px_22px_rgba(14,116,144,0.3)] sm:text-8xl lg:text-[10rem]">
            CASSANDRA
          </h1>
          <p className="mt-3 font-mono text-xs uppercase tracking-[0.28em] text-cyan-700">
            Real-Time Order Flow Intelligence
          </p>
          <p className="mt-5 max-w-2xl text-base text-center leading-7 text-slate-600">
            Monitor VPIN toxicity, stream live Binance order flow, and get autonomous intelligence briefs with market context in one dashboard.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleLandingStart}
              disabled={actionLoading}
              className="rounded-xl bg-cyan-600 px-5 py-3 font-mono text-xs font-semibold uppercase tracking-[0.18em] text-white transition hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {actionLoading ? "starting..." : "start streaming"}
            </button>
          </div>

          {actionError ? (
            <p className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 font-mono text-xs text-red-700">
              {actionError}
            </p>
          ) : null}
        </section>
      </main>
    );
  }

  return (
    <>
      {/* <Header /> */}
      <main className="relative w-full overflow-x-hidden bg-slate-50 px-4 py-6 text-slate-900 sm:px-6 lg:px-10">
        <div className="pointer-events-none absolute -left-24 top-10 h-80 w-80 rounded-full bg-cyan-300/20 blur-3xl" />
        <div className="pointer-events-none absolute right-0 top-1/3 h-72 w-72 rounded-full bg-rose-300/20 blur-3xl" />

        <div className="w-full flex flex-col items-center justify-center mb-20 mt-10">
          <p className="font-display text-6xl font-bold tracking-tight text-slate-900 drop-shadow-[0_10px_20px_rgba(14,116,144,0.26)] sm:text-7xl lg:text-8xl">
            CASSANDRA
          </p>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">Real-Time Order Flow Intelligence for Crypto Markets</p>
        </div>

        <div className="relative w-full space-y-8 animate-rise">
        
          <MetricsBar
            status={status}
            latestUpdate={latestUpdate}
          />

          <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
            <div className="space-y-4">
              <LiveChart
                data={livePoints}
                currentVpin={currentVpin}
                connectionError={connectionError}
                isConnected={isConnected}
                streaming={streaming}
                streamButtonLabel={streamButtonLabel}
                onStreamButtonClick={handleStreamButtonClick}
                onResetSystem={handleResetSystem}
                streamActionLoading={actionLoading}
                streamActionError={actionError}
              />
              <ChatInterface
                messages={messages}
                isSending={isSending}
                error={chatError}
                onSend={sendMessage}
              />
              {/* <BacktestChart
                data={backtestData}
                events={events}
                summary={summary}
                loading={backtestLoading}
                error={backtestError}
              /> */}
            </div>

            <aside className="space-y-4">
              <IntelligenceBrief brief={activeBrief} error={briefError} />
            </aside>
          </div>
        </div>
      </main>
    </>
  );
}
