import type { ChatSource } from "../chat";
import { LESSONS } from "../review-data";

// Interaction fixture only. Remove this from the mock adapter when connecting the API.
const slide = LESSONS.embedding.slides[0]!;

export const DEMO_EMBEDDING_SLIDE: ChatSource = {
  source_id: "demo-embedding-slide-4",
  title: "Bài 2 — Embedding",
  slide: 4,
  content: slide.body.join("\n\n"),
  excerpt: slide.body[0]!,
  is_demo: true,
};
