import { useEffect, useRef, useState } from "react";
import { QUICK_ACTIONS, type ChatContext } from "@/lib/tutor-replies";
import type { ChatMessage, ChatSource } from "@/lib/chat";
import { SourceCitation } from "@/components/SourceCitation";
import { CoachMascot } from "@/components/CoachMascot";
import { ChatMarkdown } from "@/components/ChatMarkdown";

export type { ChatMessage } from "@/lib/chat";

type Props = {
  messages: ChatMessage[];
  context: ChatContext;
  onSend: (text: string) => void;
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  onOpenSource?: ((source: ChatSource) => void) | undefined;
  onCheckMe?: (() => void) | undefined;
  onRetest?: (() => void) | undefined;
};

export function TutorChat({
  messages,
  context,
  onSend,
  isLoading,
  error,
  onRetry,
  onOpenSource,
  onCheckMe,
  onRetest,
}: Props) {
  const [value, setValue] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, isLoading, error]);

  return (
    <aside className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
      <div className="border-b border-border px-5 py-4 lg:px-7">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <CoachMascot className="h-9 w-9 rounded-xl" />
            <h2 className="text-lg font-semibold text-foreground">AI Tutor</h2>
          </div>
          <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] text-muted-foreground">
            Cùng một cuộc trò chuyện
          </span>
        </div>
        <p className="mt-1 truncate text-xs text-muted-foreground">Đang xem: {context.label}</p>
      </div>

      <div
        aria-busy={isLoading}
        className="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-6 lg:px-7"
      >
        {messages.map((m) => (
          <div key={m.id} className={m.role === "user" ? "flex justify-end" : ""}>
            <div
              className={
                m.role === "user"
                  ? "max-w-[88%] whitespace-pre-line rounded-2xl rounded-br-sm bg-primary px-5 py-4 text-sm leading-relaxed text-primary-foreground"
                  : "max-w-[88%] whitespace-pre-line rounded-2xl rounded-bl-sm bg-surface px-5 py-4 text-sm leading-relaxed text-foreground"
              }
            >
              {m.role === "ai" && (
                <span className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  AI Tutor
                </span>
              )}
              {m.role === "ai" ? <ChatMarkdown text={m.text} /> : m.text}
              {m.role === "ai" && (
                <SourceCitation
                  citations={m.citations ?? m.sources ?? []}
                  onOpenSource={onOpenSource}
                />
              )}
              {m.role === "ai" && m.kind === "reply" && onRetest && (
                <div className="mt-4 flex flex-wrap gap-2 whitespace-normal">
                  <button
                    type="button"
                    disabled={isLoading}
                    onClick={() => inputRef.current?.focus()}
                    className="rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium disabled:opacity-40"
                  >
                    Luyện thêm
                  </button>
                  <button
                    type="button"
                    disabled={isLoading}
                    onClick={onRetest}
                    className="rounded-lg bg-primary px-3 py-2 text-xs font-medium text-primary-foreground disabled:opacity-40"
                  >
                    Kiểm tra lại
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <p role="status" className="animate-pulse text-sm text-muted-foreground">
            Đang chờ AI trả lời…
          </p>
        )}
        {error && (
          <div
            role="alert"
            className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm"
          >
            <p>{error}</p>
            <button
              type="button"
              onClick={onRetry}
              disabled={isLoading}
              className="mt-2 text-primary underline disabled:opacity-40"
            >
              Thử lại
            </button>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="border-t border-border px-5 py-5 lg:px-7">
        <div className="mb-3 flex flex-wrap gap-2">
          {QUICK_ACTIONS.map((q) => (
            <button
              key={q}
              disabled={isLoading}
              onClick={() => onSend(q)}
              className="whitespace-nowrap rounded-lg border border-border bg-card px-3 py-2 text-xs text-foreground transition-colors hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-40"
            >
              {q}
            </button>
          ))}
          {onCheckMe && (
            <button
              onClick={onCheckMe}
              className="rounded-full bg-accent px-2.5 py-1 text-xs font-medium text-accent-foreground transition-opacity hover:opacity-90"
            >
              Kiểm tra lại tôi
            </button>
          )}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (isLoading || !value.trim()) return;
            onSend(value.trim());
            setValue("");
          }}
          className="flex gap-2"
        >
          <input
            ref={inputRef}
            aria-label="Câu hỏi cho AI Tutor"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Hỏi AI về phần đang xem…"
            className="min-w-0 flex-1 rounded-xl border border-input bg-card px-3 py-2.5 text-sm outline-none focus:border-primary"
          />
          <button
            type="submit"
            disabled={isLoading || !value.trim()}
            className="rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Gửi
          </button>
        </form>
      </div>
    </aside>
  );
}
