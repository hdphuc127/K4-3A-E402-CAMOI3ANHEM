// Frontend model; map /api/v1/quiz to this shape once its contract is agreed.
export type QuizQuestion = {
  id: string;
  prompt: string;
  options: readonly string[];
  correct: number;
  why: string;
  topic?: string;
  difficulty?: string | number;
  adaptive_metadata?: Readonly<Record<string, unknown>>;
};

export type QuizMetadata = {
  quiz_id?: string;
  difficulty?: string | number;
  adaptive_metadata?: Readonly<Record<string, unknown>>;
};

export type QuizAnswers = Record<string, number>;

// Validate supplied MCQs, without selecting/adapting questions on the frontend.
export function isValidQuiz(questions: readonly QuizQuestion[]): boolean {
  return (
    questions.length >= 3 &&
    questions.length <= 5 &&
    new Set(questions.map((q) => q.id)).size === questions.length &&
    questions.every(
      (q) =>
        q.id.trim().length > 0 &&
        q.prompt.trim().length > 0 &&
        q.options.length >= 2 &&
        q.options.every((option) => option.trim().length > 0) &&
        Number.isInteger(q.correct) &&
        q.correct >= 0 &&
        q.correct < q.options.length &&
        q.why.trim().length > 0,
    )
  );
}

export function hasQuizAnswer(question: QuizQuestion, answers: QuizAnswers): boolean {
  const answer = answers[question.id];
  return (
    answer !== undefined &&
    Number.isInteger(answer) &&
    answer >= 0 &&
    answer < question.options.length
  );
}
