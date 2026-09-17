import { useEffect, useRef, useState } from "react";
import { QUICK_ACTIONS, type ChatContext } from "@/lib/tutor-replies";

export type ChatMessage = { id: string; role: "user" | "ai"; text: string };

type Props = {
  messages: ChatMessage[];
  context: ChatContext;
  onSend: (text: string) => void;
  onCheckMe?: (() => void) | undefined;
};

export function TutorChat({ messages, context, onSend, onCheckMe }: Props) {
  const [value, setValue] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length]);

  return (
    <aside className="flex h-full min-h-0 flex-col rounded-xl border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-foreground">AI Tutor</h2>
          <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] text-muted-foreground">
            Cùng một cuộc trò chuyện
          </span>
        </div>
        <p className="mt-1 truncate text-xs text-muted-foreground">Đang xem: {context.label}</p>
      </div>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.map((m) => (
          <div key={m.id} className={m.role === "user" ? "flex justify-end" : ""}>
            <div
              className={
                m.role === "user"
                  ? "max-w-[85%] whitespace-pre-line rounded-2xl rounded-br-sm bg-primary px-3 py-2 text-sm text-primary-foreground"
                  : "max-w-[92%] whitespace-pre-line text-sm leading-relaxed text-foreground"
              }
            >
              {m.role === "ai" && (
                <span className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  AI Tutor
                </span>
              )}
              {m.text}
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div className="border-t border-border px-4 py-3">
        <div className="mb-2 flex flex-wrap gap-1.5">
          {QUICK_ACTIONS.map((q) => (
            <button
              key={q}
              onClick={() => onSend(q)}
              className="rounded-full border border-border bg-background px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary"
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
            if (!value.trim()) return;
            onSend(value);
            setValue("");
          }}
          className="flex gap-2"
        >
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Hỏi AI về phần đang xem…"
            className="min-w-0 flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary"
          />
          <button
            type="submit"
            className="rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
          >
            Gửi
          </button>
        </form>
      </div>
    </aside>
  );
}
