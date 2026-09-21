"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AiChipIcon, Cancel01Icon, ChatBotIcon, SentIcon } from "hugeicons-react";
import { getAuthenticatedAiChatWebSocketUrl, type AiChatResponse } from "@/lib/ai-chat";
import { cn } from "@/lib/utils";

type ChatMessage = {
  id: number;
  role: "user" | "assistant" | "error";
  text: string;
};

type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";

const initialMessage: ChatMessage = {
  id: 0,
  role: "assistant",
  text: "Hi, I’m the Serenity Health AI assistant. Ask me about hospital information.",
};

function statusLabel(status: ConnectionStatus) {
  if (status === "connected") return "Connected";
  if (status === "connecting") return "Connecting…";
  if (status === "error") return "Connection unavailable";
  return "Disconnected";
}

export function AiChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage]);
  const [draft, setDraft] = useState("");
  const [isWaiting, setIsWaiting] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const isConnectingRef = useRef(false);
  const closeRequestedRef = useRef(false);
  const latestMessageRef = useRef<HTMLDivElement | null>(null);

  const addMessage = useCallback((role: ChatMessage["role"], text: string) => {
    setMessages((current) => [...current, { id: Date.now() + current.length, role, text }]);
  }, []);

  const disconnect = useCallback(() => {
    closeRequestedRef.current = true;
    socketRef.current?.close();
    socketRef.current = null;
    isConnectingRef.current = false;
    setStatus("disconnected");
    setIsWaiting(false);
  }, []);

  const connect = useCallback(async () => {
    if (
      isConnectingRef.current ||
      socketRef.current?.readyState === WebSocket.OPEN ||
      socketRef.current?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    closeRequestedRef.current = false;
    isConnectingRef.current = true;
    setStatus("connecting");
    let socket: WebSocket;
    try {
      const url = await getAuthenticatedAiChatWebSocketUrl();
      if (closeRequestedRef.current) return;
      socket = new WebSocket(url);
    } catch {
      isConnectingRef.current = false;
      setStatus("error");
      return;
    }

    isConnectingRef.current = false;
    socketRef.current = socket;

    socket.onopen = () => setStatus("connected");
    socket.onmessage = (event) => {
      let response: AiChatResponse;
      try {
        response = JSON.parse(event.data) as AiChatResponse;
      } catch {
        addMessage("error", "The assistant sent an unreadable response. Please try again.");
        setIsWaiting(false);
        return;
      }

      if (response.type === "connection") {
        setStatus("connected");
      } else if (response.type === "answer") {
        addMessage("assistant", response.message);
        setIsWaiting(false);
      } else if (response.type === "error") {
        addMessage("error", response.message || "The assistant could not process that request.");
        setIsWaiting(false);
      }
    };
    socket.onerror = () => {
      setStatus("error");
      setIsWaiting(false);
    };
    socket.onclose = () => {
      socketRef.current = null;
      isConnectingRef.current = false;
      setIsWaiting(false);
      if (!closeRequestedRef.current) {
        setStatus("error");
      }
    };
  }, [addMessage]);

  useEffect(() => {
    const timer = isOpen ? window.setTimeout(() => { void connect(); }, 0) : undefined;
    return () => {
      if (timer) window.clearTimeout(timer);
      if (!isOpen) return;
      disconnect();
    };
  }, [isOpen, connect, disconnect]);

  useEffect(() => {
    latestMessageRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isWaiting]);

  useEffect(() => () => disconnect(), [disconnect]);

  const sendMessage = () => {
    const text = draft.trim();
    if (!text || isWaiting || socketRef.current?.readyState !== WebSocket.OPEN) return;

    addMessage("user", text);
    setDraft("");
    setIsWaiting(true);
    socketRef.current.send(JSON.stringify({ message: text }));
  };

  const closePanel = () => {
    setIsOpen(false);
    disconnect();
  };

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="fixed bottom-5 right-5 z-[60] flex size-14 items-center justify-center rounded-full bg-action text-white transition-transform hover:scale-105 hover:bg-focus focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-action/30"
        aria-label="Open AI assistant"
      >
        <ChatBotIcon className="size-6" />
      </button>
    );
  }

  const canSend = Boolean(draft.trim()) && status === "connected" && !isWaiting;

  return (
    <section
      className="fixed bottom-4 right-4 z-[60] flex h-[min(38rem,calc(100dvh-2rem))] w-[calc(100vw-2rem)] max-w-sm flex-col overflow-hidden rounded-[18px] border border-hairline bg-canvas dark:border-stone-800 dark:bg-stone-900"
      aria-label="AI Assistant"
    >
      <header className="flex items-center justify-between bg-action px-4 py-3 text-white">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="flex size-8 shrink-0 items-center justify-center rounded-[11px] bg-white/15">
            <AiChipIcon className="size-4" />
          </div>
          <div className="min-w-0">
            <h2 className="text-sm font-semibold">AI Assistant</h2>
            <p className="text-xs text-white/75">{statusLabel(status)}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={closePanel}
          className="rounded-full p-1.5 text-white/75 transition-colors hover:bg-white/15 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          aria-label="Minimize AI assistant"
        >
          <Cancel01Icon className="size-5" />
        </button>
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto bg-stone-50 p-4 dark:bg-stone-950">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex",
              message.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <p
              className={cn(
                "max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
                message.role === "user" && "rounded-br-md bg-emerald-600 text-white",
                message.role === "assistant" && "rounded-bl-md border border-stone-200 bg-white text-stone-700 dark:border-stone-700 dark:bg-stone-900 dark:text-stone-200",
                message.role === "error" && "rounded-bl-md border border-red-200 bg-red-50 text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300"
              )}
            >
              {message.text}
            </p>
          </div>
        ))}
        {isWaiting && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-md border border-stone-200 bg-white px-3.5 py-2.5 text-sm text-stone-500 dark:border-stone-700 dark:bg-stone-900 dark:text-stone-400">
              <span className="inline-flex items-center gap-1.5"><span className="size-2 animate-pulse rounded-full bg-emerald-500" />AI Assistant is thinking…</span>
            </div>
          </div>
        )}
        {status === "error" && !isWaiting && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
            Connection unavailable. <button type="button" onClick={() => void connect()} className="font-semibold underline underline-offset-2">Try again</button>
          </div>
        )}
        <div ref={latestMessageRef} />
      </div>

      <form
        className="border-t border-stone-200 bg-white p-3 dark:border-stone-700 dark:bg-stone-900"
        onSubmit={(event) => {
          event.preventDefault();
          sendMessage();
        }}
      >
        <div className="flex items-center gap-2">
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={status === "connected" ? "Ask the AI assistant…" : "Waiting for connection…"}
            disabled={status !== "connected" || isWaiting}
            className="h-10 min-w-0 flex-1 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm text-stone-900 outline-none placeholder:text-stone-400 focus:border-emerald-500 focus:ring-3 focus:ring-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-60 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-100"
            aria-label="Message AI assistant"
          />
          <button
            type="submit"
            disabled={!canSend}
            className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-emerald-600 text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-emerald-500 dark:hover:bg-emerald-400"
            aria-label="Send message"
          >
            <SentIcon className="size-4" />
          </button>
        </div>
      </form>
    </section>
  );
}
