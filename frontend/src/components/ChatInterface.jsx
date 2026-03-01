import { useState } from "react";

export default function ChatInterface({ messages, isSending, error, onSend }) {
  const [input, setInput] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    const value = input.trim();
    if (!value || isSending) return;
    setInput("");
    await onSend(value);
  };

  return (
    <section className="animate-rise rounded-3xl border border-white/10 bg-ink-900/85 p-5 backdrop-blur-sm">
      <div className="mb-4">
        <p className="font-mono text-xs uppercase tracking-[0.25em] text-signal-cyan">Chat</p>
        <h2 className="font-display text-xl font-semibold text-white">Ask the agent</h2>
      </div>

      <div className="max-h-72 space-y-2 overflow-y-auto rounded-2xl border border-white/10 bg-ink-950/55 p-3">
        {messages.map((message) => (
          <article
            key={message.id}
            className={`rounded-xl px-3 py-2 text-sm leading-6 ${
              message.role === "user"
                ? "ml-6 bg-signal-cyan/15 text-signal-cyan"
                : "mr-6 bg-white/5 text-white/85"
            }`}
          >
            <p className="mb-1 font-mono text-[10px] uppercase tracking-widest text-white/50">{message.role}</p>
            <p>{message.content}</p>
          </article>
        ))}
      </div>

      {error ? <p className="mt-2 font-mono text-xs text-signal-red">{error}</p> : null}

      <form onSubmit={submit} className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="What does this VPIN regime imply?"
          className="flex-1 rounded-xl border border-white/20 bg-ink-950/70 px-3 py-2 text-sm text-white outline-none ring-0 placeholder:text-white/40 focus:border-signal-cyan/60"
        />
        <button
          type="submit"
          disabled={isSending}
          className="rounded-xl bg-signal-cyan px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wider text-ink-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSending ? "Sending" : "Send"}
        </button>
      </form>
    </section>
  );
}
