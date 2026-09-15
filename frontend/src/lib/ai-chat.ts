export type AiChatResponse = {
  type: "connection" | "answer" | "error";
  message: string;
};

/**
 * This is intentionally a public environment variable: browsers establish the
 * WebSocket connection directly, so unlike the REST API base URL it cannot be
 * kept server-only.
 */
export function getAiChatWebSocketUrl() {
  if (process.env.NEXT_PUBLIC_AI_WEBSOCKET_URL) {
    return process.env.NEXT_PUBLIC_AI_WEBSOCKET_URL;
  }

  // A reverse-proxied production deployment can use the page host by default.
  // Set NEXT_PUBLIC_AI_WEBSOCKET_URL when Channels is hosted elsewhere.
  if (process.env.NODE_ENV === "production" && typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/ws/chat/`;
  }

  return "ws://127.0.0.1:8000/ws/chat/";
}

/** Obtain the existing session's access token only when opening the socket. */
export async function getAuthenticatedAiChatWebSocketUrl() {
  const url = new URL(getAiChatWebSocketUrl());
  const response = await fetch("/api/chat-token", {
    cache: "no-store",
    credentials: "same-origin",
  });

  if (response.ok) {
    const { token } = (await response.json()) as { token?: string | null };
    if (token) url.searchParams.set("token", token);
  }

  return url.toString();
}
