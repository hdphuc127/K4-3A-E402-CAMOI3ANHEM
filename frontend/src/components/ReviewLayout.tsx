import { useEffect, useState, type ReactNode } from "react";
import { CoachMascot } from "./CoachMascot";

type Props = {
  step: string;
  label: string;
  steps: readonly string[];
  activeIndex: number;
  onHome: () => void;
  tutor: ReactNode;
  messageCount: number;
  children: ReactNode;
  sourcePanel?: ReactNode;
  hidden?: boolean;
};

export function ReviewLayout({
  step,
  label,
  steps,
  activeIndex,
  onHome,
  tutor,
  messageCount,
  children,
  sourcePanel,
  hidden = false,
}: Props) {
  const workspace = step === "lesson";
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    if (messageCount > 1) setChatOpen(true);
  }, [messageCount]);

  return (
    <div className={`review-app coach-app min-h-screen ${hidden ? "hidden" : ""}`}>
      <div className={`coach-shell ${workspace && sourcePanel ? "coach-shell-split" : ""}`}>
        <header className="border-b border-border bg-card">
          <div className="mx-auto flex min-h-14 max-w-full items-center justify-between gap-4 px-4 sm:px-5">
            <button type="button" onClick={onHome} className="flex items-center gap-3 text-left">
              <CoachMascot className="h-8 w-8 shrink-0 rounded-xl" />
              <h1 className="text-base font-bold">
                Coach<span className="text-primary">4U</span>
              </h1>
            </button>
            <span className="text-right text-[11px] font-medium text-muted-foreground">
              {label}
            </span>
          </div>
          {step !== "weeks" && (
            <nav
              aria-label="Tiến trình ôn tập"
              className="mx-auto flex max-w-md px-4 pb-4 pt-3 text-[10px] sm:text-xs"
            >
              {steps.map((name, index) => (
                <div
                  key={name}
                  aria-current={index === activeIndex ? "step" : undefined}
                  className={`relative flex flex-1 flex-col items-center gap-2 ${index === activeIndex ? "font-semibold text-primary" : "text-muted-foreground"}`}
                >
                  {index < steps.length - 1 && (
                    <span
                      aria-hidden="true"
                      className={`absolute left-1/2 top-2 h-0.5 w-full ${index < activeIndex ? "bg-primary" : "bg-border"}`}
                    />
                  )}
                  <span
                    aria-hidden="true"
                    className={`relative z-10 h-4 w-4 rounded-full border-2 ${index <= activeIndex ? "border-primary bg-primary" : "border-border bg-card"} ${index === activeIndex ? "ring-4 ring-primary/10" : ""}`}
                  />
                  <span className="text-center">{name}</span>
                </div>
              ))}
            </nav>
          )}
        </header>
        <main
          className={
            workspace
              ? `review-workspace grid overflow-hidden bg-card ${sourcePanel ? "lg:grid-cols-2" : "grid-cols-1"}`
              : "px-4 py-5 sm:px-5"
          }
        >
          {children}
          {workspace && sourcePanel && (
            <div className="min-w-0 border-b border-border lg:border-r lg:border-b-0">
              {sourcePanel}
            </div>
          )}
          <aside
            className={
              workspace
                ? "min-w-0 bg-card"
                : "fixed right-4 bottom-4 z-30 w-[min(420px,calc(100vw-2rem))]"
            }
          >
            {!workspace && (
              <button
                type="button"
                aria-expanded={chatOpen}
                aria-controls="review-tutor-panel"
                onClick={() => setChatOpen((open) => !open)}
                className="ml-auto mb-3 flex items-center gap-3 rounded-full border border-primary/20 bg-primary px-5 py-3 text-sm font-medium text-primary-foreground shadow-lg"
              >
                AI Tutor <span aria-hidden="true">{chatOpen ? "−" : "+"}</span>
              </button>
            )}
            <div
              id="review-tutor-panel"
              className={`${workspace || chatOpen ? "" : "hidden"} ${workspace ? "h-[min(640px,calc(100dvh-12rem))] min-h-[420px]" : "h-[min(620px,calc(100dvh-11rem))] min-h-0 shadow-xl"}`}
            >
              {tutor}
            </div>
          </aside>
        </main>
      </div>
    </div>
  );
}
