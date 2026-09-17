import { useId, useState } from "react";
import {
  hasQuizAnswer,
  isValidQuiz,
  type QuizAnswers,
  type QuizMetadata,
  type QuizQuestion,
} from "@/lib/quiz";

type Props = {
  title: string;
  questions: readonly QuizQuestion[];
  answers: QuizAnswers;
  submitted: boolean;
  metadata?: QuizMetadata;
  topicLabels?: Readonly<Record<string, string>>;
  onPick: (questionId: string, answer: number) => void;
  onSubmit: () => void;
  onContinue: () => void;
  onBack: () => void;
  continueLabel?: string;
};

export function AdaptiveQuiz({
  title,
  questions,
  answers,
  submitted,
  metadata,
  topicLabels,
  onPick,
  onSubmit,
  onContinue,
  onBack,
  continueLabel = "Xem kết quả & ôn tập",
}: Props) {
  const instanceId = useId();
  const [page, setPage] = useState(0);
  const currentIndex = Math.min(page, Math.max(0, questions.length - 1));
  const valid = isValidQuiz(questions);
  const answeredCount = questions.filter((q) => hasQuizAnswer(q, answers)).length;
  const complete = valid && answeredCount === questions.length;
  const correctCount = questions.filter((q) => answers[q.id] === q.correct).length;

  return (
    <div className="coach-quiz space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-foreground">{title}</h2>
        <span className="text-sm text-muted-foreground">
          Đã trả lời {answeredCount}/{questions.length}
        </span>
      </div>
      {!submitted && valid && (
        <div className="space-y-3">
          <p aria-live="polite" className="text-sm text-muted-foreground">
            Câu {currentIndex + 1} / {questions.length}
          </p>
          <div
            role="progressbar"
            aria-label="Tiến trình câu hỏi"
            aria-valuemin={0}
            aria-valuemax={questions.length}
            aria-valuenow={currentIndex + 1}
            className="h-1.5 overflow-hidden rounded-full bg-muted"
          >
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
            />
          </div>
        </div>
      )}
      {metadata?.difficulty !== undefined && (
        <p className="text-xs text-muted-foreground">Độ khó: {metadata.difficulty}</p>
      )}
      {!valid ? (
        <p
          role="alert"
          className="rounded-2xl border border-border bg-card p-5 shadow-sm sm:p-6 text-sm"
        >
          Bài quiz chưa sẵn sàng. Cần 3–5 câu hỏi có đáp án và giải thích đầy đủ.
        </p>
      ) : (
        questions.map((q, index) => {
          const correct = answers[q.id] === q.correct;
          const topicLabel = q.topic ? (topicLabels?.[q.topic] ?? q.topic) : undefined;

          return (
            <fieldset
              key={q.id}
              hidden={!submitted && index !== currentIndex}
              className="min-w-0 rounded-2xl border border-border bg-card p-4 sm:p-5"
            >
              <legend className="sr-only">
                Câu {index + 1}: {q.prompt}
              </legend>
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="text-xs text-muted-foreground">Câu {index + 1}</span>
                {topicLabel && (
                  <span className="rounded-md bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
                    {topicLabel}
                  </span>
                )}
                {q.difficulty !== undefined && (
                  <span className="text-xs text-muted-foreground">Độ khó: {q.difficulty}</span>
                )}
              </div>
              <p className="text-2xl font-semibold leading-snug text-foreground">{q.prompt}</p>
              <div className="mt-4 grid gap-2">
                {q.options.map((option, answerIndex) => {
                  const selected = answers[q.id] === answerIndex;
                  const state = submitted
                    ? answerIndex === q.correct
                      ? "border-success bg-success/10"
                      : selected
                        ? "border-warning bg-warning/15"
                        : "border-border"
                    : selected
                      ? "border-primary bg-primary/5"
                      : "border-border";

                  return (
                    <label
                      key={answerIndex}
                      className={`flex items-start gap-3 rounded-xl border px-3 py-3 text-sm leading-relaxed transition-colors focus-within:ring-2 focus-within:ring-ring ${submitted ? "" : "cursor-pointer hover:bg-surface"} ${state}`}
                    >
                      <input
                        type="radio"
                        className="sr-only"
                        name={`${instanceId}-${q.id}`}
                        disabled={submitted}
                        checked={selected}
                        onChange={() => {
                          if (!submitted) onPick(q.id, answerIndex);
                        }}
                      />
                      <span
                        aria-hidden="true"
                        className={`grid h-6 w-6 shrink-0 place-items-center rounded-full border text-xs font-medium ${selected ? "border-primary bg-primary text-primary-foreground" : "border-border text-muted-foreground"}`}
                      >
                        {String.fromCharCode(65 + answerIndex)}
                      </span>
                      <span className="pt-0.5">{option}</span>
                    </label>
                  );
                })}
              </div>
              {submitted && (
                <div
                  className={`mt-3 rounded-lg p-3 text-sm ${correct ? "bg-success/10" : "bg-warning/15"}`}
                >
                  <p className="font-medium">{correct ? "Chính xác" : "Chưa đúng"}</p>
                  {!correct && <p className="mt-1">Đáp án đúng: {q.options[q.correct]}</p>}
                  <p className="mt-1 whitespace-pre-line">{q.why}</p>
                </div>
              )}
            </fieldset>
          );
        })
      )}
      {valid && submitted && (
        <p role="status" className="text-sm text-foreground">
          Đúng {correctCount}/{questions.length} câu.
        </p>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {!submitted && valid && (
          <button
            type="button"
            disabled={currentIndex === 0}
            onClick={() => setPage(currentIndex - 1)}
            className="rounded-xl px-4 py-2.5 text-sm text-muted-foreground disabled:opacity-40"
          >
            Câu trước
          </button>
        )}
        {!submitted && valid && currentIndex < questions.length - 1 ? (
          <button
            type="button"
            disabled={!hasQuizAnswer(questions[currentIndex]!, answers)}
            onClick={() => setPage(currentIndex + 1)}
            className="rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground disabled:opacity-40"
          >
            Câu tiếp theo
          </button>
        ) : (
          <button
            type="button"
            disabled={!complete}
            onClick={() => {
              if (!complete) return;
              if (submitted) onContinue();
              else onSubmit();
            }}
            className="rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-40"
          >
            {submitted ? continueLabel : "Nộp bài"}
          </button>
        )}
        <button
          type="button"
          onClick={onBack}
          className="rounded-xl border border-border bg-card px-5 py-2.5 text-sm hover:border-primary"
        >
          Quay lại
        </button>
      </div>
    </div>
  );
}
