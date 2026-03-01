import BacktestChart from "./components/BacktestChart";
import ChatInterface from "./components/ChatInterface";
import IntelligenceBrief from "./components/IntelligenceBrief";
import LiveChart from "./components/LiveChart";
import MetricsBar from "./components/MetricsBar";
import { useAgentChat } from "./hooks/useAgentChat";
import { useBacktestData } from "./hooks/useBacktestData";
import { useIntelligenceBrief } from "./hooks/useIntelligenceBrief";
import { useStreamStatus } from "./hooks/useStreamStatus";
import { useVpinStream } from "./hooks/useVpinStream";

export default function App() {
  const { status } = useStreamStatus();
  const { data: backtestData, events, summary, loading: backtestLoading, error: backtestError } = useBacktestData();
  const { brief, error: briefError } = useIntelligenceBrief();
  const { livePoints, latestUpdate, latestBrief, currentVpin, isConnected, connectionError } = useVpinStream();
  const { messages, isSending, error: chatError, sendMessage } = useAgentChat();

  const activeBrief = latestBrief || brief;

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-ink-950 px-4 py-6 text-white sm:px-6 lg:px-10">
      <div className="pointer-events-none absolute -left-24 top-10 h-80 w-80 rounded-full bg-signal-cyan/10 blur-3xl" />
      <div className="pointer-events-none absolute right-0 top-1/3 h-72 w-72 rounded-full bg-signal-red/10 blur-3xl" />

      <div className="relative mx-auto max-w-7xl space-y-4">
        <MetricsBar status={status} latestUpdate={latestUpdate} isConnected={isConnected} />

        <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
          <div className="space-y-4">
            <LiveChart data={livePoints} currentVpin={currentVpin} connectionError={connectionError} />
            <BacktestChart
              data={backtestData}
              events={events}
              summary={summary}
              loading={backtestLoading}
              error={backtestError}
            />
          </div>

          <aside className="space-y-4">
            <IntelligenceBrief brief={activeBrief} error={briefError} />
            <ChatInterface
              messages={messages}
              isSending={isSending}
              error={chatError}
              onSend={sendMessage}
            />
          </aside>
        </div>
      </div>
    </main>
  );
}
