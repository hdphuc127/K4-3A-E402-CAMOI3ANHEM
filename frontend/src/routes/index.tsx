import { createFileRoute } from "@tanstack/react-router";
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
} from "@/lib/review-data";

type TopicId = string;

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Ôn tập thông minh — Tìm đúng lỗ hổng kiến thức" },
      {
        name: "description",
        content:
          "Làm bài kiểm tra nhanh cuối tuần, xem lỗ hổng kiến thức, tới đúng bài học liên quan và ôn cùng AI Tutor.",
      },
      { property: "og:title", content: "Ôn tập thông minh — Tìm đúng lỗ hổng kiến thức" },
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

const FLOW: Step[] = ["weeks", "week", "test", "result", "lesson", "check", "summary"];

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
  const [showAllMistakes, setShowAllMistakes] = useState(false);
  const [status, setStatus] = useState<Record<string, Status>>({});
  const [flagged, setFlagged] = useState<Record<string, boolean>>({});
  const [topic, setTopic] = useState<TopicId>("embedding");
  const [slide, setSlide] = useState(0);
  const [checkIdx, setCheckIdx] = useState(0);
  const [checkAnswer, setCheckAnswer] = useState<number | null>(null);
  const [checkSubmitted, setCheckSubmitted] = useState(false);
  const [diagnosisByQuestion, setDiagnosisByQuestion] = useState<Record<string, DiagnosisResult>>(
    {},
  );
  const [isSubmittingDiagnosis, setIsSubmittingDiagnosis] = useState(false);
  const [diagnosisError, setDiagnosisError] = useState<string | null>(null);
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
  const weekQuestions = useMemo(
    () => QUESTIONS.filter((q) => week.topics.includes(q.topic)),
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
        ? `${getLesson(topic).lesson} - ${getLesson(topic).slides[slide]!.title}`
        : step === "check"
          ? `Kiểm tra hiểu — ${getTopic(topic).name}`
          : step === "result"
            ? "Kết quả & lỗ hổng kiến thức"
            : STEP_LABEL[step],
    topic: (step === "weeks" || step === "week" ? undefined : topic) as ChatContext["topic"],
  };

  const send = (text: string) => {
    setMessages((prev) => [...prev, msg("user", text), msg("ai", tutorReply(text, chatContext))]);
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
    setTopic(t);
    setSlide(0);
    setStep("lesson");
    aiSay(
      `Mình đã mở ${getLesson(t).lesson} - ${getLesson(t).slides[0]!.title}. Đây đúng là phần liên quan tới lỗi sai của bạn. Bạn cứ đọc, có gì hỏi mình ngay tại đây nhé.`,
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

  const remaining = week.topics.filter((t) => topicStatus(t) === "needs");

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
              Ô
            </div>
            <div>
              <h1 className="text-sm font-semibold text-foreground">Ôn tập thông minh</h1>
              <p className="text-xs text-muted-foreground">
                Biết mình yếu chỗ nào — và ôn đúng chỗ đó trước
              </p>
            </div>
          </div>
          <nav className="hidden items-center gap-1 md:flex">
            {FLOW.map((s, i) => {
              const active = s === step;
              const done = FLOW.indexOf(step) > i;
              return (
                <span
                  key={s}
                  className={`rounded-full px-2.5 py-1 text-xs ${
                    active
                      ? "bg-primary text-primary-foreground"
                      : done
                        ? "text-primary"
                        : "text-muted-foreground"
                  }`}
                >
                  {i + 1}. {STEP_LABEL[s]}
                </span>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[1fr_380px]">
        <section className="min-w-0 space-y-4">
          {step === "weeks" && (
            <>
              <div>
                <h2 className="text-xl font-semibold text-foreground">Chọn tuần bạn muốn ôn</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Mỗi tuần gồm các bài đã học. Chọn một tuần để bắt đầu kiểm tra nhanh.
                </p>
              </div>
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
                {WEEKS.map((w) => (
                  <button
                    key={w.id}
                    disabled={!w.available}
                    onClick={() => {
                      setWeekId(w.id);
                      setStep("week");
                    }}
                    className={`rounded-xl border bg-card p-4 text-left transition-colors ${
                      w.available
                        ? "border-border hover:border-primary"
                        : "border-border opacity-55"
                    }`}
                  >
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
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
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
                </div>
                <div className="mt-5 flex flex-wrap gap-2">
                  <button
                    onClick={() => setStep("test")}
                    className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
                  >
                    Bắt đầu kiểm tra
                  </button>
                  <button
                    onClick={() => goLesson(week.topics[0]!)}
                    className="rounded-lg border border-border px-4 py-2 text-sm hover:border-primary"
                  >
                    Xem nội dung tuần
                  </button>
                </div>
                <p className="mt-3 text-xs text-muted-foreground">
                  Bài kiểm tra không nhằm chấm điểm — nó dùng để xác định bạn đang yếu ở đâu.
                </p>
              </div>
            </>
          )}

          {step === "test" && (
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
          )}

          {step === "result" && (
            <>
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
                    </div>
                  </div>
                ) : (
                  <p className="mt-4 rounded-lg bg-success/10 p-4 text-sm text-foreground">
                    Bạn trả lời đúng tất cả. Không có lỗ hổng nào cần ưu tiên tuần này.
                  </p>
                )}

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
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {showAllMistakes && (
                <div className="space-y-3">
                  {weekQuestions
                    .filter((q) => answers[q.id] !== q.correct)
                    .map((q) => (
                      <div key={q.id} className="rounded-xl border border-border bg-card p-4">
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
                  className="rounded-lg border border-border px-4 py-2 text-sm hover:border-primary"
                >
                  Để sau — xem tổng kết
                </button>
                <button
                  onClick={() => setStep("test")}
                  className="rounded-lg border border-border px-4 py-2 text-sm hover:border-primary"
                >
                  Xem lại bài làm
                </button>
              </div>
            </>
          )}

          {step === "lesson" && (
            <>
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
                  <button
                    onClick={startCheck}
                    className="ml-auto rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
                  >
                    Kiểm tra lại tôi
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => send("Giải thích dễ hiểu hơn")}
                  className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm hover:border-primary"
                >
                  Giải thích dễ hơn
                </button>
                <button
                  onClick={() => send("Cho tôi ví dụ khác")}
                  className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm hover:border-primary"
                >
                  Cho ví dụ khác
                </button>
                <button
                  onClick={() => send("So sánh 2 khái niệm")}
                  className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm hover:border-primary"
                >
                  So sánh 2 khái niệm
                </button>
                <button
                  onClick={() => send("Tóm tắt phần này")}
                  className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm hover:border-primary"
                >
                  Tóm tắt phần này
                </button>
                <button
                  onClick={() => send("Tôi vẫn chưa hiểu")}
                  className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm hover:border-primary"
                >
                  Tôi vẫn chưa hiểu
                </button>
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
              onNext={() => setStep("summary")}
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
              <div className="rounded-xl border border-border bg-card p-5">
                <h2 className="text-xl font-semibold text-foreground">
                  Tổng kết tuần — {week.title}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Bản đồ kiến thức của bạn sau phiên ôn này.
                </p>
                <div className="mt-4 grid gap-2">
                  {week.topics.map((t) => (
                    <div
                      key={t}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border p-3"
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
                      .map((t) => getTopic(t).name)
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
                    className="rounded-lg border border-border px-4 py-2 text-sm hover:border-primary"
                  >
                    Xem lại lỗi sai
                  </button>
                  <button
                    onClick={() => setStep("weeks")}
                    className="rounded-lg border border-border px-4 py-2 text-sm hover:border-primary"
                  >
                    Quay về danh sách tuần
                  </button>
                  <button
                    onClick={() =>
                      aiSay(
                        "Phiên ôn đã kết thúc. Tổng kết vẫn ở đây nếu bạn muốn xem lại, và mình vẫn sẵn sàng trả lời thêm.",
                      )
                    }
                    className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
                  >
                    Kết thúc phiên ôn
                  </button>
                </div>
              </div>
            </>
          )}
        </section>

        <div className="h-[calc(100vh-7rem)] lg:sticky lg:top-6">
          <TutorChat
            messages={messages}
            context={chatContext}
            onSend={send}
            onCheckMe={step === "lesson" || step === "result" ? startCheck : undefined}
          />
        </div>
      </main>
    </div>
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
      <div className="rounded-xl border border-border bg-card p-5">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          Kiểm tra hiểu — {props.getTopic(props.topic).name}
        </p>
        <h2 className="mt-2 text-lg font-semibold text-foreground">{q.prompt}</h2>
        <div className="mt-4 grid gap-2">
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
                className={`flex cursor-pointer items-center gap-2 rounded-lg border p-2.5 text-sm ${state}`}
              >
                <input
                  type="radio"
                  name="check"
                  disabled={props.submitted}
                  checked={props.answer === i}
                  onChange={() => props.onPick(i)}
                />
                {o}
              </label>
            );
          })}
        </div>

        {!props.submitted ? (
          <button
            disabled={props.answer === null}
            onClick={props.onSubmit}
            className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-40"
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
                    Xem tổng kết tuần
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
