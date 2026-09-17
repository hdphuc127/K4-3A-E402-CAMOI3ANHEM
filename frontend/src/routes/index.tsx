import { createFileRoute } from "@tanstack/react-router";
feat/core-apis
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { TutorChat, type ChatMessage } from "@/components/TutorChat";
import {
  getModuleConcepts,
  getModules,
  getReviewData,
  postDiagnosis,
  type DiagnosisResult,
  type ReviewCheckQuestion,
  type ReviewLesson,
  type ReviewQuestion,
  type ReviewTopic,
  type ReviewWeek,
} from "@/lib/api";
import { tutorReply, type ChatContext } from "@/lib/tutor-replies";
import {
  CHECK_QUESTIONS as FALLBACK_CHECK_QUESTIONS,
  LESSONS as FALLBACK_LESSONS,
  QUESTIONS as FALLBACK_QUESTIONS,
  TOPICS as FALLBACK_TOPICS,
  WEEKS as FALLBACK_WEEKS,
=======
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
main
} from "@/lib/review-data";

type TopicId = string;

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
  const [selectedModuleId, setSelectedModuleId] = useState<number | null>(null);
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
feat/core-apis
  const [diagnosisByQuestion, setDiagnosisByQuestion] = useState<Record<string, DiagnosisResult>>(
    {},
  );
  const [isSubmittingDiagnosis, setIsSubmittingDiagnosis] = useState(false);
  const [diagnosisError, setDiagnosisError] = useState<string | null>(null);
=======
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [failedRequest, setFailedRequest] = useState<ChatRequest | null>(null);
  const chatPending = useRef(false);
main
  const [messages, setMessages] = useState<ChatMessage[]>([
    msg(
      "ai",
      "Chào bạn! Mình là AI Tutor. Mình sẽ đi cùng bạn suốt phiên ôn: từ bài kiểm tra, phân tích lỗ hổng, tới nội dung bài học và kiểm tra lại hiểu biết.",
    ),
  ]);

  const modulesQuery = useQuery({
    queryKey: ["learning-modules"],
    queryFn: getModules,
    staleTime: 60_000,
  });

  const conceptsQuery = useQuery({
    queryKey: ["module-concepts", selectedModuleId],
    queryFn: () => getModuleConcepts(selectedModuleId!),
    enabled: selectedModuleId !== null,
    staleTime: 60_000,
  });

  const reviewDataQuery = useQuery({
    queryKey: ["review-data"],
    queryFn: getReviewData,
    staleTime: 60_000,
  });

  const TOPICS = (reviewDataQuery.data?.topics ?? FALLBACK_TOPICS) as Record<
    string,
    ReviewTopic
  >;
  const WEEKS = (reviewDataQuery.data?.weeks ?? FALLBACK_WEEKS) as ReviewWeek[];
  const QUESTIONS = (reviewDataQuery.data?.questions ?? FALLBACK_QUESTIONS) as ReviewQuestion[];
  const LESSONS = (reviewDataQuery.data?.lessons ?? FALLBACK_LESSONS) as Record<
    string,
    ReviewLesson
  >;
  const CHECK_QUESTIONS = (
    reviewDataQuery.data?.check_questions ?? FALLBACK_CHECK_QUESTIONS
  ) as Record<string, ReviewCheckQuestion[]>;
  const getTopic = (id: string): ReviewTopic =>
    TOPICS[id] ?? { id, name: id, summary: "Chưa có mô tả từ backend." };
  const getLesson = (id: string): ReviewLesson =>
    LESSONS[id] ?? {
      lesson: getTopic(id).name,
      slides: [{ title: getTopic(id).name, body: [getTopic(id).summary] }],
    };
  const getCheckQuestions = (id: string): ReviewCheckQuestion[] =>
    CHECK_QUESTIONS[id] ?? [];

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
feat/core-apis
        ? `${getLesson(topic).lesson} - ${getLesson(topic).slides[slide]!.title}`
=======
        ? selectedSource?.title?.trim() || LESSONS[topic].lesson
main
        : step === "check"
          ? `Kiểm tra hiểu — ${getTopic(topic).name}`
          : step === "result"
            ? "Kết quả & lỗ hổng kiến thức"
            : STEP_LABEL[step],
    topic: (step === "weeks" || step === "week" ? undefined : topic) as ChatContext["topic"],
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

  const submitTest = async () => {
    setIsSubmittingDiagnosis(true);
    setDiagnosisError(null);
    try {
      const results = await Promise.all(
        weekQuestions.map(async (question) => {
          const result = await postDiagnosis({
            lesson_id: question.topic,
            question_id: question.id,
            question_text: question.prompt,
            correct_answer: question.options[question.correct]!,
            student_answer: question.options[answers[question.id]!]!,
          });
          return [question.id, result] as const;
        }),
      );
      setDiagnosisByQuestion(Object.fromEntries(results));
      setStep("result");
      aiSay(
        "Mình đã gửi bài làm tới backend để phân tích. Bạn có thể xem hint chẩn đoán ở từng câu sai.",
      );
    } catch (error) {
      setDiagnosisError(error instanceof Error ? error.message : "Không thể phân tích bài làm");
      setStep("result");
    } finally {
      setIsSubmittingDiagnosis(false);
    }
  };
  const aiSay = (text: string) => setMessages((prev) => [...prev, msg("ai", text)]);

  const goLesson = (t: TopicId) => {
    setShowRemainingTopics(false);
    setTopic(t);
    setSelectedSource(null);
    setStep("lesson");
    aiSay(
feat/core-apis
      `Mình đã mở ${getLesson(t).lesson} - ${getLesson(t).slides[0]!.title}. Đây đúng là phần liên quan tới lỗi sai của bạn. Bạn cứ đọc, có gì hỏi mình ngay tại đây nhé.`,
=======
      `Mình sẽ cùng bạn ôn ${LESSONS[t].lesson}. Bạn có thể hỏi mình ngay tại đây và mở nguồn từ citation khi câu trả lời có cung cấp.`,
main
    );
  };

  const startCheck = () => {
    setCheckAnswer(null);
    setCheckSubmitted(false);
    setStep("check");
    aiSay(
      `Được, mình ra một câu mới về ${getTopic(topic).name} — khác câu bạn đã làm sai, nhưng cùng khái niệm.`,
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
feat/core-apis
              <div className="rounded-xl border border-border bg-card p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">Module từ backend</h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Lấy dữ liệu từ GET /api/v1/modules và GET /api/v1/modules/:id/concepts.
                    </p>
                  </div>
                  <span className="rounded-full bg-secondary px-2.5 py-1 text-xs text-muted-foreground">
                    {modulesQuery.isFetching ? "Đang tải" : "API"}
                  </span>
                </div>

                {modulesQuery.isLoading && (
                  <p className="mt-3 text-sm text-muted-foreground">
                    Đang tải danh sách module...
                  </p>
                )}

                {modulesQuery.isError && (
                  <div className="mt-3 rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm text-foreground">
                    <p className="font-medium">Chưa kết nối được backend.</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Hãy chạy backend ở http://127.0.0.1:8000 rồi reload frontend.
                    </p>
                  </div>
                )}

                {modulesQuery.data && modulesQuery.data.length > 0 && (
                  <div className="mt-3 grid gap-2">
                    {modulesQuery.data.map((module) => (
                      <button
                        key={module.id}
                        onClick={() => {
                          setSelectedModuleId(module.id);
                          aiSay(
                            `Mình đã lấy module "${module.title}" từ backend. Bạn có thể xem các khái niệm bên dưới.`,
                          );
                        }}
                        className={`rounded-lg border p-3 text-left transition-colors ${
                          selectedModuleId === module.id
                            ? "border-primary bg-primary/5"
                            : "border-border hover:border-primary"
                        }`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="text-sm font-medium text-foreground">{module.title}</p>
                          <span className="rounded-md bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
                            Track {module.track}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">{module.description}</p>
                      </button>
                    ))}
                  </div>
                )}

                {selectedModuleId !== null && (
                  <div className="mt-4 rounded-lg border border-border p-3">
                    <p className="text-xs font-medium uppercase text-muted-foreground">Concepts</p>
                    {conceptsQuery.isLoading && (
                      <p className="mt-2 text-sm text-muted-foreground">Đang tải concepts...</p>
                    )}
                    {conceptsQuery.isError && (
                      <p className="mt-2 text-sm text-warning-foreground">
                        Không tải được concepts cho module này.
                      </p>
                    )}
                    {conceptsQuery.data && conceptsQuery.data.concepts.length > 0 && (
                      <div className="mt-2 grid gap-2">
                        {conceptsQuery.data.concepts.map((concept) => (
                          <div key={concept.id} className="rounded-md bg-secondary px-3 py-2">
                            <p className="text-sm font-medium text-secondary-foreground">
                              {concept.title}
                            </p>
                            <p className="mt-0.5 text-xs text-muted-foreground">
                              {concept.expected_summary}
                            </p>
                            {concept.common_gap && (
                              <p className="mt-1 text-xs text-primary">
                                Lỗ hổng thường gặp: {concept.common_gap}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    {conceptsQuery.data && conceptsQuery.data.concepts.length === 0 && (
                      <p className="mt-2 text-sm text-muted-foreground">
                        Module này chưa có concept.
                      </p>
                    )}
                  </div>
                )}
              </div>
              <div className="grid gap-3">
=======
              <div className="mx-auto grid max-w-4xl gap-3 pt-2">
main
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
feat/core-apis
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium text-foreground">{w.title}</h3>
                      <span className="text-xs text-muted-foreground">{w.period}</span>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{w.subtitle}</p>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {w.topics.map((t) => (
                        <span
                          key={t}
                          className="rounded-md bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
                        >
                          {getTopic(t).name}
                        </span>
                      ))}
                      {!w.available && (
                        <span className="text-xs text-muted-foreground">
                          · Bản demo: chọn Tuần 2
=======
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
main
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
feat/core-apis
              <div className="rounded-xl border border-border bg-card p-5">
                <h2 className="text-xl font-semibold text-foreground">{week.title}</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Kiểm tra nhanh để biết phần nào bạn cần ôn lại. Khoảng 3 phút,{" "}
                  {weekQuestions.length} câu.
                </p>
                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  {week.topics.map((t) => (
                    <div key={t} className="rounded-lg border border-border p-3">
                      <p className="text-sm font-medium text-foreground">{getTopic(t).name}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">{getTopic(t).summary}</p>
                    </div>
                  ))}
=======
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
main
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
feat/core-apis
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-foreground">
                  Bài kiểm tra nhanh — {week.title}
                </h2>
                <span className="text-sm text-muted-foreground">
                  Đã trả lời {Object.keys(answers).length}/{weekQuestions.length}
                </span>
              </div>
              {weekQuestions.map((q, i) => (
                <div key={q.id} className="rounded-xl border border-border bg-card p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Câu {i + 1}</span>
                    <span className="rounded-md bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
                      {getTopic(q.topic).name}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-foreground">{q.prompt}</p>
                  <div className="mt-3 grid gap-2">
                    {q.options.map((o, oi) => (
                      <label
                        key={oi}
                        className={`flex cursor-pointer items-center gap-2 rounded-lg border p-2.5 text-sm ${
                          answers[q.id] === oi ? "border-primary bg-primary/5" : "border-border"
                        }`}
                      >
                        <input
                          type="radio"
                          name={q.id}
                          checked={answers[q.id] === oi}
                          onChange={() => setAnswers((a) => ({ ...a, [q.id]: oi }))}
                        />
                        {o}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={submitTest}
                  disabled={
                    isSubmittingDiagnosis || Object.keys(answers).length < weekQuestions.length
                  }
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-40"
                >
                  {isSubmittingDiagnosis ? "Đang phân tích..." : "Nộp bài"}
                </button>
                <button
                  onClick={() => setStep("week")}
                  className="rounded-lg border border-border px-4 py-2 text-sm hover:border-primary"
                >
                  Quay lại
                </button>
              </div>
            </>
=======
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
main
          )}

          {step === "result" && (
            <>
feat/core-apis
              <div className="rounded-xl border border-border bg-card p-5">
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
                  <div className="text-3xl font-semibold text-primary">
                    {correctCount}/{weekQuestions.length}
                  </div>
                </div>

                {priority ? (
                  <div className="mt-4 rounded-lg border border-primary/30 bg-primary/5 p-4">
                    <p className="text-sm font-semibold text-primary">
                      Ưu tiên ôn: {getTopic(priority).name}
                    </p>
                    <p className="mt-1 text-sm text-foreground">
                      {wrongByTopic[priority]! >= 2
                        ? `Các câu trả lời của bạn cho thấy bạn có thể đang nhầm ${
                            priority === "embedding"
                              ? "Token ID với Embedding Vector"
                              : `bản chất của ${getTopic(priority).name}`
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
=======
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
main
                    </div>
                  </div>

feat/core-apis
                <div className="mt-5 grid gap-2">
                  {week.topics.map((t) => (
                    <div
                      key={t}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border p-3"
                    >
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {getTopic(t).name}
                          {wrongByTopic[t]
                            ? ` — sai ${wrongByTopic[t]} câu`
                            : " — không sai câu nào"}
                        </p>
                        <p className="text-xs text-muted-foreground">{getTopic(t).summary}</p>
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
=======
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
main
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
                            {getLesson(q.topic).lesson}
                          </span>
                        </div>
                        <p className="text-sm font-medium text-foreground">{q.prompt}</p>
                        <p className="mt-2 text-sm text-muted-foreground">
                          Bạn chọn: {q.options[answers[q.id]!]}
                        </p>
                        <p className="text-sm text-success">Đáp án đúng: {q.options[q.correct]}</p>
                        <p className="mt-2 text-sm text-foreground">{q.why}</p>
                        {diagnosisByQuestion[q.id] && (
                          <div className="mt-3 rounded-lg bg-accent/40 p-3 text-sm text-accent-foreground">
                            <p className="font-medium">Hint từ backend</p>
                            <p className="mt-1">{diagnosisByQuestion[q.id]!.hint}</p>
                            {diagnosisByQuestion[q.id]!.citations[0] && (
                              <p className="mt-2 text-xs opacity-80">
                                Nguồn: {diagnosisByQuestion[q.id]!.citations[0]!.title}
                              </p>
                            )}
                          </div>
                        )}
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
                <span className="text-foreground">{getLesson(topic).lesson}</span>
              </div>
feat/core-apis
              <div className="rounded-xl border border-border bg-card p-5">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  Khái niệm liên quan tới lỗi sai của bạn
                </p>
                <h2 className="mt-1 text-xl font-semibold text-foreground">
                  {getLesson(topic).slides[slide]!.title}
                </h2>
                {getLesson(topic).slides[slide]!.note && (
                  <p className="mt-2 rounded-lg bg-accent/40 px-3 py-2 text-sm text-accent-foreground">
                    {getLesson(topic).slides[slide]!.note}
                  </p>
                )}
                <div className="mt-4 space-y-3">
                  {getLesson(topic).slides[slide]!.body.map((p, i) => (
                    <p key={i} className="text-sm leading-relaxed text-foreground">
                      {p}
                    </p>
                  ))}
                </div>
                <div className="mt-5 flex flex-wrap items-center gap-2">
                  <button
                    disabled={slide === 0}
                    onClick={() => setSlide((s) => s - 1)}
                    className="rounded-lg border border-border px-3 py-1.5 text-sm disabled:opacity-40"
                  >
                    Xem phần trước
                  </button>
                  <button
                    disabled={slide >= getLesson(topic).slides.length - 1}
                    onClick={() => setSlide((s) => s + 1)}
                    className="rounded-lg border border-border px-3 py-1.5 text-sm disabled:opacity-40"
                  >
                    Xem phần tiếp theo
                  </button>
                  <span className="text-xs text-muted-foreground">
                    Slide {slide + 1}/{getLesson(topic).slides.length}
                  </span>
=======
              <div className="flex flex-wrap gap-2">
                {week.topics.map((t) => (
main
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
              checkQuestions={getCheckQuestions(topic)}
              getTopic={getTopic}
              onPick={setCheckAnswer}
              onSubmit={() => {
                setCheckSubmitted(true);
                const q = getCheckQuestions(topic)[checkIdx % getCheckQuestions(topic).length]!;
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
feat/core-apis
              <div className="rounded-xl border border-border bg-card p-5">
=======
              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
main
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
                        {diagnosisError && (
                          <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm text-foreground">
                            Không lấy được chẩn đoán từ backend: {diagnosisError}
                          </div>
                        )}
                        <p className="text-sm font-medium text-foreground">{getTopic(t).name}</p>
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
                            Ôn tiếp {getTopic(t).name}
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
feat/core-apis
                      .map((t) => getTopic(t).name)
=======
                      .map((t) => TOPICS[t].name)
main
                      .join(", ") || "chưa có"}
                  </p>
                  <p className="mt-1">
                    <strong>Còn cần ôn:</strong>{" "}
                    {remaining.map((t) => getTopic(t).name).join(", ") || "không còn phần nào"}
                  </p>
                  <p className="mt-1">
                    <strong>Nên ưu tiên tiếp theo:</strong>{" "}
                    {remaining[0] ? getTopic(remaining[0]).name : "Có thể học sang tuần mới"}
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
  checkQuestions: ReviewCheckQuestion[];
  getTopic: (id: string) => ReviewTopic;
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
  const list = props.checkQuestions;
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
          Kiểm tra hiểu — {props.getTopic(props.topic).name}
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
feat/core-apis
                className={`flex cursor-pointer items-center gap-2 rounded-lg border p-2.5 text-sm ${state}`}
=======
                className={`flex cursor-pointer items-start gap-4 rounded-xl border px-5 py-4 text-sm leading-relaxed focus-within:ring-2 focus-within:ring-ring ${state}`}
main
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
                      Ôn tiếp {props.getTopic(t).name}
                    </button>
                  ))}
                  <button
                    onClick={props.onNext}
                    className="rounded-lg border border-border px-3 py-1.5 text-sm hover:border-primary"
                  >
feat/core-apis
                    Xem tổng kết tuần
=======
                    Tiếp tục nội dung khác
main
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
