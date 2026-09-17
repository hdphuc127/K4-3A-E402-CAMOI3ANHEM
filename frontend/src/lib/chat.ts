import type { ChatContext } from "./tutor-replies";

const API_BASE_URL = (import.meta.env["VITE_API_BASE_URL"] ?? "http://127.0.0.1:8000/api/v1")
  .replace(/^VITE_API_BASE_URL=/, "")
  .replace(/\/$/, "");

// Frontend model; map the backend contract to these fields when it is available.
export type ChatSource = {
  source_id?: string | null;
  id?: string;
  title?: string | null;
  page?: number | string | null;
  slide?: number | string | null;
  timestamp?: string | null;
  excerpt?: string | null;
  // Full source text, if supplied separately from the cited excerpt.
  content?: string | null;
  // Keep the supplied value: the backend's confidence scale is not agreed yet.
  confidence?: number | string | null;
  url?: string;
  // Frontend demo marker; never inferred for backend sources.
  is_demo?: boolean;
};

export type ChatMessage = {
  id: string;
  role: "user" | "ai";
  text: string;
  kind?: "reply" | "notice";
  // Prefer citations; sources remains supported for existing callers.
  citations?: ChatSource[];
  sources?: ChatSource[];
};

export type ChatRequest = {
  text: string;
  context: ChatContext;
  messages: ChatMessage[];
};

export type ChatReply = {
  text: string;
  citations?: ChatSource[];
  sources?: ChatSource[];
};

export async function requestTutorReplyStream(
  request: ChatRequest,
  onText: (text: string) => void,
): Promise<ChatReply> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: {
      Accept: "application/x-ndjson",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text: request.text,
      context: request.context,
      messages: request.messages.map(({ role, text }) => ({ role, text })),
    }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat stream request failed: ${response.status} ${response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let fullText = "";
  let citations: ChatSource[] = [];
  let degraded = false;

  const consume = (line: string) => {
    if (!line.trim()) return;
    const event = JSON.parse(line) as {
      type: "delta" | "done";
      text?: string;
      citations?: ChatSource[];
      degraded?: boolean;
    };
    if (event.type === "delta" && event.text) {
      fullText += event.text;
      onText(event.text);
    } else if (event.type === "done") {
      citations = event.citations ?? [];
      degraded = event.degraded ?? false;
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    lines.forEach(consume);
    if (done) break;
  }
  if (buffer.trim()) consume(buffer);

  return { text: fullText, citations, sources: citations };
}

export async function requestTutorReply(request: ChatRequest): Promise<ChatReply> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text: request.text,
      context: request.context,
      messages: request.messages.map(({ role, text }) => ({ role, text })),
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat API request failed: ${response.status} ${response.statusText}`);
  }

  const payload = (await response.json()) as {
    success: boolean;
    data?: { text: string; citations?: ChatSource[] };
    error?: { message?: string } | null;
  };
  if (!payload.success || !payload.data) {
    throw new Error(payload.error?.message ?? "Chat API returned an unsuccessful response");
  }

  return {
    text: payload.data.text,
    citations: payload.data.citations ?? [],
  };
}
