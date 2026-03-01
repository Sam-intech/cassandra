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
  };





  // ============================
  // App main layout start here
  return (
    <>
      {/* <Header /> */}
      <main className="relative w-full overflow-x-hidden bg-ink-950 px-4 py-6 text-white sm:px-6 lg:px-10">
        <div className="pointer-events-none absolute -left-24 top-10 h-80 w-80 rounded-full bg-signal-cyan/10 blur-3xl" />
        <div className="pointer-events-none absolute right-0 top-1/3 h-72 w-72 rounded-full bg-signal-red/10 blur-3xl" />

        <div className="w-full flex flex-col items-center justify-center mb-20 mt-10">
          <p className="font-display text-3xl font-bold tracking-tight text-white">CASSANDRA</p>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-white/55">Real-Time Order Flow Intelligence for Crypto Markets</p>
        </div>

        <div className="relative w-full space-y-8">
        
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
