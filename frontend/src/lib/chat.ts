import { tutorReply, type ChatContext } from "./tutor-replies";
import { DEMO_EMBEDDING_SLIDE } from "./demo/chat-demo";

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

// Keep the existing mock until the chat API contract is available.
// Replace only this adapter with the backend request and response mapping.
export async function requestTutorReply(request: ChatRequest): Promise<ChatReply> {
  return {
    text: tutorReply(request.text, request.context),
    ...(request.context.topic === "embedding" ? { citations: [DEMO_EMBEDDING_SLIDE] } : {}),
  };
}
