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
    <section className="animate-rise rounded-3xl border border-slate-200 bg-white/95 p-5 shadow-[0_18px_42px_-30px_rgba(15,23,42,0.45)] backdrop-blur-sm">
      <div className="mb-4">
        <p className="font-mono text-xs uppercase tracking-[0.25em] text-cyan-700">Need to chat?</p>
        <h2 className="font-display text-xl font-semibold text-slate-900">Ask Cassandra</h2>
      </div>

      <div className="max-h-72 space-y-2 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50 p-3">
        {messages.map((message) => (
          <article
            key={message.id}
            className={`rounded-xl px-3 py-2 text-sm leading-6 ${
              message.role === "user"
                ? "ml-6 bg-cyan-100 text-cyan-900"
                : "mr-6 bg-white text-slate-700"
            }`}
          >
            <p className="mb-1 font-mono text-[10px] uppercase tracking-widest text-slate-400">{message.role}</p>
            <p>{message.content}</p>
          </article>
        ))}
      </div>

      {error ? <p className="mt-2 font-mono text-xs text-red-700">{error}</p> : null}

      <form onSubmit={submit} className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="What does this VPIN regime imply?"
          className="flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none ring-0 placeholder:text-slate-400 focus:border-cyan-500"
        />
        <button
          type="submit"
          disabled={isSending}
          className="rounded-xl bg-cyan-600 px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wider text-white transition hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSending ? "Sending" : "Send"}
        </button>
      </form>
    </section>
  );
}
