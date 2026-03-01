import { useState } from "react";
import { fetchJson } from "../lib/api";

function makeId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function useAgentChat() {
  const initialMessage = {
    id: makeId(),
    role: "assistant",
    content: "Ask about current VPIN behavior, liquidity risk, or tactical positioning.",
  };
  const [messages, setMessages] = useState([
    initialMessage,
  ]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  const sendMessage = async (question) => {
    const value = question.trim();
    if (!value || isSending) return;

    const userMessage = { id: makeId(), role: "user", content: value };
    setMessages((prev) => [...prev, userMessage]);
    setIsSending(true);
    setError("");

    try {
      const payload = await fetchJson("/agent/chat", {
        method: "POST",
        body: JSON.stringify({ question: value }),
      });

      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: "assistant",
          content: payload.response || "No response returned.",
        },
      ]);
    } catch (err) {
      const message = err.message || "Failed to send chat request.";
      setError(message);
      setMessages((prev) => [
        ...prev,
        { id: makeId(), role: "assistant", content: `Error: ${message}` },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const resetConversation = () => {
    setMessages([
      {
        id: makeId(),
        role: "assistant",
        content: initialMessage.content,
      },
    ]);
    setError("");
    setIsSending(false);
  };

  return { messages, isSending, error, sendMessage, resetConversation };
}
