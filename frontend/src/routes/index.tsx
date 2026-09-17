import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useRef, useState } from "react";
import { TutorChat, type ChatMessage } from "@/components/TutorChat";
import { AdaptiveQuiz } from "@/components/AdaptiveQuiz";
import { ReviewLayout } from "@/components/ReviewLayout";
import { SourceViewer } from "@/components/SourceViewer";
import { CoachLanding } from "@/components/CoachLanding";
import { type ChatContext } from "@/lib/tutor-replies";
import { requestTutorReply, type ChatRequest, type ChatSource } from "@/lib/chat";
import {
  CHECK_QUESTIONS,
  DEMO_QUIZ_QUESTION_IDS,
  LESSONS,
  QUESTIONS,
  TOPICS,
  WEEKS,
  type TopicId,
} from "@/lib/review-data";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Coach4U — Your AI Learning Coach" },
      {
        name: "description",
        content:
          "Làm bài kiểm tra nhanh cuối tuần, xem lỗ hổng kiến thức, tới đúng bài học liên quan và ôn cùng AI Tutor.",
      },
      { property: "og:title", content: "Coach4U — Your AI Learning Coach" },
      {
        property: "og:description",
        content:
          "Phát hiện điểm yếu, hiểu vì sao sai, tới đúng nội dung học và kiểm tra lại hiểu biết.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ReviewApp,
});

type Step = "weeks" | "week" | "test" | "result" | "lesson" | "check" | "summary";
type Status = "strong" | "needs" | "reviewed" | "unverified";

const STEP_LABEL: Record<Step, string> = {
  weeks: "Chọn tuần",
  week: "Tổng quan tuần",
  test: "Bài kiểm tra nhanh",
  result: "Lỗ hổng kiến thức",
  lesson: "Ôn nội dung",
  check: "Kiểm tra hiểu",
  summary: "Tổng kết tuần",
};

// Presentation grouping only: all existing application states remain intact.
const DISPLAY_STEPS = ["Khởi động", "Đánh giá", "Ôn tập", "Kiểm tra"];
const DISPLAY_INDEX: Record<Step, number> = {
  weeks: 0,
  week: 0,
  test: 1,
  result: 1,
  lesson: 2,
  check: 3,
  summary: 3,
};

let mid = 0;
const msg = (role: "user" | "ai", text: string): ChatMessage => ({
  id: `m${++mid}`,
  role,
  text,
});

function StatusPill({ status }: { status: Status }) {
  const map: Record<Status, { t: string; c: string }> = {
    strong: { t: "Vững", c: "bg-success/15 text-success" },
    needs: { t: "Cần ôn", c: "bg-warning/25 text-warning-foreground" },
    reviewed: { t: "Đã ôn & xác nhận", c: "bg-primary/10 text-primary" },
    unverified: { t: "Chưa xác nhận", c: "bg-secondary text-muted-foreground" },
  };
  const s = map[status];
  return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${s.c}`}>{s.t}</span>;
}

function ReviewApp() {
  const [step, setStep] = useState<Step>("weeks");
  const [weekId, setWeekId] = useState<string>("w2");
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [showAllMistakes, setShowAllMistakes] = useState(false);
  const [status, setStatus] = useState<Record<string, Status>>({});
  const [flagged, setFlagged] = useState<Record<string, boolean>>({});
  const [topic, setTopic] = useState<TopicId>("embedding");
  const [selectedSource, setSelectedSource] = useState<ChatSource | null>(null);
  const [checkIdx, setCheckIdx] = useState(0);
  const [checkAnswer, setCheckAnswer] = useState<number | null>(null);
  const [checkSubmitted, setCheckSubmitted] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [failedRequest, setFailedRequest] = useState<ChatRequest | null>(null);
  const chatPending = useRef(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    msg(
      "ai",
      "Chào bạn! Mình là AI Tutor. Mình sẽ đi cùng bạn suốt phiên ôn: từ bài kiểm tra, phân tích lỗ hổng, tới nội dung bài học và kiểm tra lại hiểu biết.",
    ),
  ]);

  const week = WEEKS.find((w) => w.id === weekId)!;
  const [isReviewQuiz, setIsReviewQuiz] = useState(false);
  const [reviewAnswers, setReviewAnswers] = useState<Record<string, number>>({});
  const [reviewSubmitted, setReviewSubmitted] = useState(false);
  const [showLanding, setShowLanding] = useState(true);
  const [showRemainingTopics, setShowRemainingTopics] = useState(false);
  const weekQuestions = useMemo(
    () =>
      QUESTIONS.filter(
        (q) => week.topics.includes(q.topic) && DEMO_QUIZ_QUESTION_IDS.includes(q.id),
      ),
    [week],
  );

  const wrongByTopic = useMemo(() => {
    const m: Record<string, number> = {};
    for (const q of weekQuestions) {
      if (answers[q.id] !== undefined && answers[q.id] !== q.correct) {
        m[q.topic] = (m[q.topic] ?? 0) + 1;
      }
    }
    return m;
  }, [answers, weekQuestions]);

  const correctCount = weekQuestions.filter((q) => answers[q.id] === q.correct).length;
  const priority = useMemo(() => {
    const entries = Object.entries(wrongByTopic).sort((a, b) => b[1] - a[1]);
    return (entries[0]?.[0] as TopicId | undefined) ?? undefined;
  }, [wrongByTopic]);

  const topicStatus = (t: TopicId): Status =>
    (status[t] as Status) ?? (wrongByTopic[t] ? "needs" : "strong");

  const chatContext: ChatContext = {
    label:
      step === "lesson"
        ? selectedSource?.title?.trim() || LESSONS[topic].lesson
        : step === "check"
          ? `Kiểm tra hiểu — ${TOPICS[topic].name}`
          : step === "result"
            ? "Kết quả & lỗ hổng kiến thức"
            : STEP_LABEL[step],
    topic: step === "weeks" || step === "week" ? undefined : topic,
  };

  const receiveReply = async (request: ChatRequest) => {
    // A ref also blocks repeated sends before React renders the loading state.
    if (chatPending.current) return;
    chatPending.current = true;
    setChatLoading(true);
    setChatError(null);
    setFailedRequest(null);
    try {
      const reply = await requestTutorReply(request);
      if (!reply.text.trim()) throw new Error("Empty tutor reply");
      const response: ChatMessage = { ...msg("ai", reply.text), ...reply, kind: "reply" };
      setMessages((prev) => [...prev, response]);
    } catch {
      setFailedRequest(request);
      setChatError(
        "Chưa nhận được câu trả lời. Câu hỏi của bạn vẫn được giữ lại; hãy thử lại nhé.",
      );
    } finally {
      chatPending.current = false;
      setChatLoading(false);
    }
  };

  const send = (text: string) => {
    const question = text.trim();
    if (chatPending.current || !question) return;
    const userMessage = msg("user", question);
    const request: ChatRequest = {
      text: question,
      context: { ...chatContext },
      messages: [...messages, userMessage],
    };
    setMessages((prev) => [...prev, userMessage]);
    void receiveReply(request);
  };
  const aiSay = (text: string) => setMessages((prev) => [...prev, msg("ai", text)]);

  const goLesson = (t: TopicId) => {
    setShowRemainingTopics(false);
    setTopic(t);
    setSelectedSource(null);
    setStep("lesson");
    aiSay(
      `Mình sẽ cùng bạn ôn ${LESSONS[t].lesson}. Bạn có thể hỏi mình ngay tại đây và mở nguồn từ citation khi câu trả lời có cung cấp.`,
    );
  };

  const startCheck = () => {
    setCheckAnswer(null);
    setCheckSubmitted(false);
    setStep("check");
    aiSay(
      `Được, mình ra một câu mới về ${TOPICS[topic].name} — khác câu bạn đã làm sai, nhưng cùng khái niệm.`,
    );
  };

  const startReviewQuiz = () => {
    if (chatPending.current) return;
    setIsReviewQuiz(true);
    setReviewAnswers({});
    setReviewSubmitted(false);
    setStep("test");
  };

  const remaining = week.topics.filter((t) => topicStatus(t) === "needs");

  return (
    <>
      {showLanding && (
        <CoachLanding
          onStart={() => {
            setStep("weeks");
            setShowLanding(false);
          }}
        />
      )}
      <ReviewLayout
        hidden={showLanding}
        step={step}
        label={STEP_LABEL[step]}
        steps={DISPLAY_STEPS}
        activeIndex={step === "test" && isReviewQuiz ? 3 : DISPLAY_INDEX[step]}
        onHome={() => setShowLanding(true)}
        messageCount={messages.length}
        sourcePanel={
          selectedSource ? (
            <SourceViewer source={selectedSource} onClose={() => setSelectedSource(null)} />
          ) : null
        }
        tutor={
          <TutorChat
            messages={messages}
            context={chatContext}
            onSend={send}
            onOpenSource={(source) => {
              setSelectedSource(source);
              setStep("lesson");
            }}
            isLoading={chatLoading}
            error={chatError}
            onRetry={() => {
              if (failedRequest) void receiveReply(failedRequest);
            }}
            onCheckMe={step === "result" ? startCheck : undefined}
            onRetest={step === "lesson" ? startReviewQuiz : undefined}
          />
        }
      >
        <section
          className={`coach-content min-w-0 space-y-4 ${step === "lesson" ? "col-span-full border-b border-border px-4 py-3" : step === "test" || step === "check" ? "mx-auto max-w-full" : step === "result" || step === "summary" ? "mx-auto max-w-full" : ""}`}
        >
          {step === "weeks" && (
            <>
              <div className="mx-auto max-w-4xl">
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Ôn tập theo tuần
                </p>
                <h2 className="text-xl font-bold text-foreground">Chọn tuần bạn muốn ôn</h2>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                  Mỗi tuần gồm các bài đã học. Chọn một tuần để bắt đầu kiểm tra nhanh.
                </p>
              </div>
              <div className="mx-auto grid max-w-4xl gap-3 pt-2">
                {WEEKS.map((w) => (
                  <button
                    key={w.id}
                    disabled={!w.available}
                    aria-pressed={weekId === w.id}
                    onClick={() => {
                      setWeekId(w.id);
                    }}
                    className={`coach-week-card flex items-center gap-3 rounded-xl border bg-card p-3 text-left transition-colors ${
                      w.available && weekId === w.id
                        ? "border-primary shadow-sm ring-1 ring-primary/15"
                        : w.available ? "border-border" : "border-border opacity-55"
                    }`}
                  >
                    <span
                      aria-hidden="true"
                      className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-secondary text-xl text-primary"
                    >
                      &#9636;
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-semibold text-foreground">{w.title}</span>
                      <span className="mt-1 block text-xs text-muted-foreground">{w.period}</span>
                      {!w.available && (
                        <span className="mt-1 block text-[11px] text-muted-foreground">
                          Chưa mở
                        </span>
                      )}
                      <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">
                        {w.subtitle}
                      </span>
                    </span>
                    <span aria-hidden="true" className="text-lg text-primary">
                      &#8250;
                    </span>
                  </button>
                ))}
              </div>
              <button
                type="button"
                disabled={!week.available}
                onClick={() => {
                  setAnswers({});
                  setQuizSubmitted(false);
                  setStatus({});
                  setFlagged({});
                  setShowAllMistakes(false);
                  setStep("week");
                }}
                className="w-full rounded-xl bg-primary py-3 text-sm font-semibold text-primary-foreground disabled:opacity-40"
              >
                Tiếp tục →
              </button>
            </>
          )}

          {step === "week" && (
            <>
              <button
                onClick={() => setStep("weeks")}
                className="text-sm text-muted-foreground hover:text-primary"
              >
                ← Quay lại danh sách tuần
              </button>
              <div className="grid gap-4">
                <div className="rounded-2xl border border-border bg-card p-4 sm:p-5">
                  <h2 className="text-xl font-semibold text-foreground">{week.title}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Kiểm tra nhanh để biết phần nào bạn cần ôn lại. Khoảng 3 phút,{" "}
                    {weekQuestions.length} câu.
                  </p>
                  <div className="mt-4 grid gap-2">
                    {week.topics.map((t) => (
                      <div key={t} className="rounded-xl border border-border bg-surface px-5 py-4">
                        <p className="text-sm font-medium text-foreground">{TOPICS[t].name}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">{TOPICS[t].summary}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="rounded-2xl border border-primary bg-card p-6 ring-1 ring-primary/15 sm:p-8">
                  <h3 className="text-xl font-semibold">Kiểm tra cuối tuần</h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {weekQuestions.length} câu · khoảng 3 phút
                  </p>
                  <div className="mt-4 flex flex-col gap-2">
                    <button
                      onClick={() => {
                        setIsReviewQuiz(false);
                        setStep("test");
                      }}
                      className="rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90"
                    >
                      Bắt đầu kiểm tra nhanh →
                    </button>
                    <button
                      onClick={() => goLesson(week.topics[0]!)}
                      className="rounded-xl border border-border bg-card px-5 py-2.5 text-sm hover:border-primary"
                    >
                      Xem nội dung tuần
                    </button>
                  </div>
                  <p className="mt-3 text-xs text-muted-foreground">
                    Bài kiểm tra không nhằm chấm điểm — nó dùng để xác định bạn đang yếu ở đâu.
                  </p>
                </div>
              </div>
            </>
          )}

          {step === "test" && (
            <AdaptiveQuiz
              key={isReviewQuiz ? "review" : "diagnostic"}
              title={`${isReviewQuiz ? "Kiểm tra lại" : "Bài kiểm tra nhanh"} — ${week.title}`}
              questions={weekQuestions}
              answers={isReviewQuiz ? reviewAnswers : answers}
              submitted={isReviewQuiz ? reviewSubmitted : quizSubmitted}
              continueLabel={isReviewQuiz ? "Tiếp tục nội dung khác" : "Xem kết quả & ôn tập"}
              topicLabels={Object.fromEntries(Object.values(TOPICS).map((t) => [t.id, t.name]))}
              onPick={(questionId, answer) => {
                if (isReviewQuiz) {
                  if (!reviewSubmitted)
                    setReviewAnswers((prev) => ({ ...prev, [questionId]: answer }));
                } else if (!quizSubmitted)
                  setAnswers((prev) => ({ ...prev, [questionId]: answer }));
              }}
              onSubmit={() => {
                if (isReviewQuiz) setReviewSubmitted(true);
                else setQuizSubmitted(true);
              }}
              onContinue={() => {
                if (isReviewQuiz) {
                  setShowRemainingTopics(true);
                  setStep("lesson");
                  return;
                }
                setStep("result");
                aiSay(
                  "Mình đã xem bài làm của bạn. Kết quả và phân tích lỗ hổng đang ở bên trái. Bạn có thể hỏi mình “Tại sao tôi sai câu này?” bất cứ lúc nào.",
                );
              }}
              onBack={() => setStep(isReviewQuiz ? "lesson" : "week")}
            />
          )}

          {step === "result" && (
            <>
              <div className="grid gap-4">
                <div className="rounded-2xl border border-border bg-card p-4 text-center">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Kết quả kiểm tra
                  </p>
                  <p className="mt-4 text-3xl font-semibold text-foreground">
                    {correctCount} / {weekQuestions.length}
                  </p>
                  <p className="mt-4 text-sm leading-relaxed text-muted-foreground">{week.title}</p>
                </div>
                <div className="rounded-2xl border border-border bg-card p-4 shadow-sm sm:p-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-xl font-semibold text-foreground">
                        Kết quả & lỗ hổng kiến thức
                      </h2>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Đúng {correctCount}/{weekQuestions.length} câu. Quan trọng hơn điểm số: bạn
                        nên ôn gì trước.
                      </p>
                    </div>
                  </div>

                  {priority ? (
                    <div className="mt-4 rounded-lg border border-primary/30 bg-primary/5 p-4">
                      <p className="text-sm font-semibold text-primary">
                        Ưu tiên ôn: {TOPICS[priority].name}
                      </p>
                      <p className="mt-1 text-sm text-foreground">
                        {wrongByTopic[priority]! >= 2
                          ? `Các câu trả lời của bạn cho thấy bạn có thể đang nhầm ${
                              priority === "embedding"
                                ? "Token ID với Embedding Vector"
                                : `bản chất của ${TOPICS[priority].name}`
                            }.`
                          : "Chưa đủ thông tin để kết luận chắc chắn bạn hiểu nhầm ở đâu. Hãy làm thêm một câu kiểm tra."}
                      </p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button
                          onClick={() => goLesson(priority)}
                          className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90"
                        >
                          Ôn phần này
                        </button>
                        <button
                          onClick={() => send("Tại sao tôi sai câu này?")}
                          className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm hover:border-primary"
                        >
                          Tại sao tôi sai?
                        </button>
                        <button
                          onClick={() => setShowAllMistakes((v) => !v)}
                          className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm hover:border-primary"
                        >
                          {showAllMistakes ? "Ẩn lỗi sai" : "Xem tất cả lỗi sai"}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="mt-4 rounded-lg bg-success/10 p-4 text-sm text-foreground">
                      Bạn trả lời đúng tất cả. Không có lỗ hổng nào cần ưu tiên tuần này.
                    </p>
                  )}

                  <div className="mt-5">
                    {week.topics.map((t) => (
                      <div
                        key={t}
                        className="flex flex-wrap items-center justify-between gap-3 border-b border-border py-4 last:border-0"
                      >
                        <div>
                          <p className="text-sm font-medium text-foreground">
                            {TOPICS[t].name}
                            {wrongByTopic[t]
                              ? ` — sai ${wrongByTopic[t]} câu`
                              : " — không sai câu nào"}
                          </p>
                          <p className="text-xs text-muted-foreground">{TOPICS[t].summary}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <StatusPill status={topicStatus(t)} />
                          {topicStatus(t) === "needs" && (
                            <>
                              <button
                                onClick={() => goLesson(t)}
                                className="rounded-md bg-primary px-2.5 py-1 text-xs text-primary-foreground hover:opacity-90"
                              >
                                Ôn phần này
                              </button>
                              <button
                                onClick={() => setFlagged((f) => ({ ...f, [t]: !f[t] }))}
                                className="rounded-md border border-border px-2.5 py-1 text-xs hover:border-primary"
                              >
                                {flagged[t] ? "✓ Đã đánh dấu" : "Đánh dấu cần ôn lại"}
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {showAllMistakes && (
                <div className="space-y-3">
                  {weekQuestions
                    .filter((q) => answers[q.id] !== q.correct)
                    .map((q) => (
                      <div
                        key={q.id}
                        className="rounded-2xl border border-border bg-card p-5 shadow-sm sm:p-6"
                      >
                        <div className="mb-1 flex items-center gap-2">
                          <span className="rounded-md bg-warning/25 px-2 py-0.5 text-xs text-warning-foreground">
                            Sai
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {LESSONS[q.topic].lesson}
                          </span>
                        </div>
                        <p className="text-sm font-medium text-foreground">{q.prompt}</p>
                        <p className="mt-2 text-sm text-muted-foreground">
                          Bạn chọn: {q.options[answers[q.id]!]}
                        </p>
                        <p className="text-sm text-success">Đáp án đúng: {q.options[q.correct]}</p>
                        <p className="mt-2 text-sm text-foreground">{q.why}</p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <button
                            onClick={() => goLesson(q.topic)}
                            className="rounded-md border border-border px-2.5 py-1 text-xs hover:border-primary"
                          >
                            Đi tới slide liên quan
                          </button>
                          <button
                            onClick={() => send("Tại sao tôi sai câu này?")}
                            className="rounded-md border border-border px-2.5 py-1 text-xs hover:border-primary"
                          >
                            Hỏi AI về câu này
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setStep("summary")}
                  className="rounded-xl border border-border bg-card px-5 py-2.5 text-sm hover:border-primary"
                >
                  Để sau — xem tổng kết
                </button>
                <button
                  onClick={() => setStep("test")}
                  className="rounded-xl border border-border bg-card px-5 py-2.5 text-sm hover:border-primary"
                >
                  Xem lại bài làm
                </button>
              </div>
            </>
          )}

          {step === "lesson" && (
            <>
              {showRemainingTopics && (
                <div className="rounded-xl border border-border bg-surface p-4">
                  <h2 className="text-sm font-semibold">Chọn nội dung cần ôn tiếp</h2>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {remaining
                      .filter((t) => t !== topic)
                      .map((t) => (
                        <button
                          type="button"
                          key={t}
                          onClick={() => goLesson(t)}
                          className="rounded-xl border border-primary/20 bg-card px-3 py-2 text-sm text-primary"
                        >
                          {TOPICS[t].name}
                        </button>
                      ))}
                    {!remaining.some((t) => t !== topic) && (
                      <p className="text-xs text-muted-foreground">
                        Không có topic yếu khác trong kết quả kiểm tra hiện tại.
                      </p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowRemainingTopics(false)}
                    className="mt-3 text-xs text-primary"
                  >
                    Tiếp tục chat
                  </button>
                </div>
              )}
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <button
                  onClick={() => setStep("result")}
                  className="text-muted-foreground hover:text-primary"
                >
                  ← Quay lại câu sai
                </button>
                <span className="text-muted-foreground">/</span>
                <span className="text-foreground">{LESSONS[topic].lesson}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {week.topics.map((t) => (
                  <button
                    type="button"
                    key={t}
                    aria-pressed={t === topic}
                    onClick={() => {
                      if (t !== topic) goLesson(t);
                    }}
                    className={`rounded-xl border px-3 py-2 text-xs ${t === topic ? "border-primary bg-secondary text-primary" : "border-border bg-card text-muted-foreground"}`}
                  >
                    {TOPICS[t].name}
                    {topicStatus(t) === "needs" ? " · Cần ôn" : ""}
                  </button>
                ))}
              </div>
            </>
          )}

          {step === "check" && (
            <CheckPanel
              topic={topic}
              index={checkIdx}
              answer={checkAnswer}
              submitted={checkSubmitted}
              onPick={setCheckAnswer}
              onSubmit={() => {
                setCheckSubmitted(true);
                const q = CHECK_QUESTIONS[topic][checkIdx % CHECK_QUESTIONS[topic].length]!;
                const ok = checkAnswer === q.correct;
                setStatus((s) => ({ ...s, [topic]: ok ? "reviewed" : "needs" }));
                aiSay(ok ? q.whyCorrect : q.whyWrong);
              }}
              onRetryOther={() => {
                setCheckIdx((i) => i + 1);
                setCheckAnswer(null);
                setCheckSubmitted(false);
              }}
              onBackToLesson={() => setStep("lesson")}
              onExplainDifferently={() => send("Giải thích dễ hiểu hơn")}
              onAnotherExample={() => send("Cho tôi ví dụ khác")}
              onNext={() => {
                setShowRemainingTopics(true);
                setStep("lesson");
              }}
              onLater={() => {
                setStatus((s) => ({ ...s, [topic]: "needs" }));
                setStep("summary");
              }}
              remaining={remaining.filter((t) => t !== topic)}
              onPickNext={goLesson}
            />
          )}

          {step === "summary" && (
            <>
              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
                <h2 className="text-xl font-semibold text-foreground">
                  Tổng kết tuần — {week.title}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Bản đồ kiến thức của bạn sau phiên ôn này.
                </p>
                <div className="mt-6">
                  {week.topics.map((t) => (
                    <div
                      key={t}
                      className="flex flex-wrap items-center justify-between gap-3 border-b border-border py-4 last:border-0"
                    >
                      <div>
                        <p className="text-sm font-medium text-foreground">{TOPICS[t].name}</p>
                        <p className="text-xs text-muted-foreground">
                          {topicStatus(t) === "reviewed"
                            ? "Đã ôn và trả lời đúng câu kiểm tra mới."
                            : topicStatus(t) === "needs"
                              ? "Còn lỗi sai chưa được xác nhận hiểu."
                              : "Không có lỗi sai trong bài kiểm tra."}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <StatusPill status={topicStatus(t)} />
                        {topicStatus(t) === "needs" && (
                          <button
                            onClick={() => goLesson(t)}
                            className="rounded-md bg-primary px-2.5 py-1 text-xs text-primary-foreground hover:opacity-90"
                          >
                            Ôn tiếp {TOPICS[t].name}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 rounded-lg bg-secondary p-4 text-sm text-foreground">
                  <p>
                    <strong>Đã ôn:</strong>{" "}
                    {week.topics
                      .filter((t) => topicStatus(t) === "reviewed")
                      .map((t) => TOPICS[t].name)
                      .join(", ") || "chưa có"}
                  </p>
                  <p className="mt-1">
                    <strong>Còn cần ôn:</strong>{" "}
                    {remaining.map((t) => TOPICS[t].name).join(", ") || "không còn phần nào"}
                  </p>
                  <p className="mt-1">
                    <strong>Nên ưu tiên tiếp theo:</strong>{" "}
                    {remaining[0] ? TOPICS[remaining[0]].name : "Có thể học sang tuần mới"}
                  </p>
                </div>
                <div className="mt-5 flex flex-wrap gap-2">
                  <button
                    onClick={() => setStep("result")}
                    className="rounded-xl border border-border bg-card px-5 py-2.5 text-sm hover:border-primary"
                  >
                    Xem lại lỗi sai
                  </button>
                  <button
                    onClick={() => setStep("weeks")}
                    className="rounded-xl border border-border bg-card px-5 py-2.5 text-sm hover:border-primary"
                  >
                    Quay về danh sách tuần
                  </button>
                  <button
                    onClick={() =>
                      aiSay(
                        "Phiên ôn đã kết thúc. Tổng kết vẫn ở đây nếu bạn muốn xem lại, và mình vẫn sẵn sàng trả lời thêm.",
                      )
                    }
                    className="rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90"
                  >
                    Kết thúc phiên ôn
                  </button>
                </div>
              </div>
            </>
          )}
        </section>
      </ReviewLayout>
    </>
  );
}

function CheckPanel(props: {
  topic: TopicId;
  index: number;
  answer: number | null;
  submitted: boolean;
  onPick: (i: number) => void;
  onSubmit: () => void;
  onRetryOther: () => void;
  onBackToLesson: () => void;
  onExplainDifferently: () => void;
  onAnotherExample: () => void;
  onNext: () => void;
  onLater: () => void;
  remaining: TopicId[];
  onPickNext: (t: TopicId) => void;
}) {
  const list = CHECK_QUESTIONS[props.topic];
  const q = list[props.index % list.length]!;
  const ok = props.answer === q.correct;

  return (
    <>
      <button
        onClick={props.onBackToLesson}
        className="text-sm text-muted-foreground hover:text-primary"
      >
        ← Quay lại nội dung bài học
      </button>
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          Kiểm tra hiểu — {TOPICS[props.topic].name}
        </p>
        <h2 className="mt-3 text-xl font-semibold leading-snug text-foreground">{q.prompt}</h2>
        <div className="mt-7 grid gap-3">
          {q.options.map((o, i) => {
            const state = props.submitted
              ? i === q.correct
                ? "border-success bg-success/10"
                : i === props.answer
                  ? "border-warning bg-warning/15"
                  : "border-border"
              : props.answer === i
                ? "border-primary bg-primary/5"
                : "border-border";
            return (
              <label
                key={i}
                className={`flex cursor-pointer items-start gap-4 rounded-xl border px-5 py-4 text-sm leading-relaxed focus-within:ring-2 focus-within:ring-ring ${state}`}
              >
                <input
                  type="radio"
                  className="sr-only"
                  name="check"
                  disabled={props.submitted}
                  checked={props.answer === i}
                  onChange={() => props.onPick(i)}
                />
                <span
                  aria-hidden="true"
                  className={`grid h-6 w-6 shrink-0 place-items-center rounded-full border text-xs ${props.answer === i ? "border-primary bg-primary text-primary-foreground" : "border-border text-muted-foreground"}`}
                >
                  {String.fromCharCode(65 + i)}
                </span>
                <span className="pt-0.5">{o}</span>
              </label>
            );
          })}
        </div>

        {!props.submitted ? (
          <button
            disabled={props.answer === null}
            onClick={props.onSubmit}
            className="mt-4 rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-40"
          >
            Trả lời
          </button>
        ) : (
          <div className="mt-4 space-y-3">
            <div
              className={`rounded-lg p-4 text-sm ${
                ok ? "bg-success/10 text-foreground" : "bg-warning/15 text-foreground"
              }`}
            >
              <p className="font-semibold">
                {ok
                  ? "Chính xác — khái niệm này đã được xác nhận hiểu."
                  : "Chưa đúng — mình chưa đánh dấu là đã hiểu."}
              </p>
              <p className="mt-1">{ok ? q.whyCorrect : q.whyWrong}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {!ok && (
                <>
                  <button
                    onClick={props.onBackToLesson}
                    className="rounded-lg border border-border px-3 py-1.5 text-sm hover:border-primary"
                  >
                    Xem lại phần này
                  </button>
                  <button
                    onClick={props.onExplainDifferently}
                    className="rounded-lg border border-border px-3 py-1.5 text-sm hover:border-primary"
                  >
                    Giải thích theo cách khác
                  </button>
                  <button
                    onClick={props.onAnotherExample}
                    className="rounded-lg border border-border px-3 py-1.5 text-sm hover:border-primary"
                  >
                    Cho ví dụ khác
                  </button>
                  <button
                    onClick={props.onRetryOther}
                    className="rounded-lg border border-border px-3 py-1.5 text-sm hover:border-primary"
                  >
                    Thử lại với câu khác
                  </button>
                  <button
                    onClick={props.onLater}
                    className="rounded-lg border border-border px-3 py-1.5 text-sm hover:border-primary"
                  >
                    Để ôn sau
                  </button>
                </>
              )}
              {ok && (
                <>
                  {props.remaining.map((t) => (
                    <button
                      key={t}
                      onClick={() => props.onPickNext(t)}
                      className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90"
                    >
                      Ôn tiếp {TOPICS[t].name}
                    </button>
                  ))}
                  <button
                    onClick={props.onNext}
                    className="rounded-lg border border-border px-3 py-1.5 text-sm hover:border-primary"
                  >
                    Tiếp tục nội dung khác
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
