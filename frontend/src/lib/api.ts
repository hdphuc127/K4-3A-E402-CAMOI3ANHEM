const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function resolveApiBaseUrl() {
  const rawValue = String(import.meta.env["VITE_API_BASE_URL"] ?? DEFAULT_API_BASE_URL).trim();
  const [, valueAfterEquals] = rawValue.match(/^VITE_API_BASE_URL=(.+)$/) ?? [];
  const value = (valueAfterEquals ?? rawValue).trim();

  if (!/^https?:\/\//.test(value)) {
    return DEFAULT_API_BASE_URL;
  }

  return value.replace(/\/$/, "");
}

const API_BASE_URL = resolveApiBaseUrl();

type ApiEnvelope<T> = {
  success: boolean;
  data: T;
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  } | null;
};

export type LearningModule = {
  id: number;
  slug: string;
  title: string;
  description: string;
  track: string;
  created_at: string;
};

export type Concept = {
  id: number;
  module_id: number;
  slug: string;
  title: string;
  expected_summary: string;
  common_gap: string;
  created_at: string;
};

export type ModuleConcepts = {
  module?: LearningModule | null;
  concepts: Concept[];
};

export type ReviewTopic = {
  id: string;
  name: string;
  summary: string;
};

export type ReviewWeek = {
  id: string;
  title: string;
  subtitle: string;
  period: string;
  topics: string[];
  available: boolean;
};

export type ReviewQuestion = {
  id: string;
  topic: string;
  prompt: string;
  options: string[];
  correct: number;
  why: string;
  misconception: string;
};

export type ReviewLesson = {
  lesson: string;
  slides: Array<{
    title: string;
    body: string[];
    note?: string | null;
  }>;
};

export type ReviewCheckQuestion = {
  prompt: string;
  options: string[];
  correct: number;
  whyCorrect: string;
  whyWrong: string;
};

export type ReviewData = {
  topics: Record<string, ReviewTopic>;
  weeks: ReviewWeek[];
  questions: ReviewQuestion[];
  lessons: Record<string, ReviewLesson>;
  check_questions: Record<string, ReviewCheckQuestion[]>;
};

export type DiagnosisResult = {
  question_id: string;
  is_correct: boolean;
  misconception: "answer_is_correct" | "counting_characters_or_spaces" | "ambiguous_or_unknown";
  hint: string;
  next_action: "retry_answer" | "ask_for_reasoning" | "explain_reasoning";
  citations: Array<{
    source_id: string;
    title: string;
    excerpt: string;
    confidence: number;
  }>;
  debug_prompt_name: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json" },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  const payload = (await response.json()) as ApiEnvelope<T>;

  if (!payload.success) {
    throw new Error(payload.error?.message ?? "API returned an unsuccessful response");
  }

  return payload.data;
}

export function getModules() {
  return request<LearningModule[]>("/modules");
}

export function getModuleConcepts(moduleId: number) {
  return request<ModuleConcepts>(`/modules/${moduleId}/concepts`);
}

export function getReviewData() {
  return request<ReviewData>("/review-data");
}

export type QuizItem = {
  id: string;
  prompt: string;
  options: string[];
  correct: number;
  why: string;
  topic: string;
  source_id: string;
};

export type QuizResult = {
  quiz_id: string;
  difficulty: string;
  items: QuizItem[];
};

export function postQuiz(input: {
  topic: string;
  weak_points?: string[];
  difficulty?: string;
  num_items?: number;
}) {
  return request<QuizResult>("/quiz", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}

export type TestResult = {
  test_id: string;
  items: ReviewQuestion[];
};

export function postDiagnosticTest(weekId: string) {
  return request<TestResult>("/test", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ week_id: weekId }),
  });
}

export function postDiagnosis(input: {
  lesson_id: string;
  question_id: string;
  question_text: string;
  correct_answer: string;
  student_answer: string;
}) {
  return request<DiagnosisResult>("/diagnosis", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}
