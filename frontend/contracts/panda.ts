export type PandaPhase =
  | "chat"
  | "diagnostic"
  | "explanation"
  | "practice"
  | "curricular"
  | "remediation"
  | "mastery_check"
  | "paused"
  | "check"
  | "report";

export interface PandaWeakTopic {
  grade: number;
  topic_id: string;
  topic: string;
  source_question_id: string;
}

export interface PandaCurrentPractice {
  id: string;
  topic_id?: string;
  lesson_id?: string;
  content_version?: string;
  part_index?: number;
  part_number?: number;
  part_count?: number;
  prompt?: string;
  source?: "curriculum" | string;
  requires_image?: boolean;
  title?: string;
  question: string;
  answer?: string;
  attempts: number;
  alternatives?: string[];
}

export interface PandaPracticeFeedback {
  is_correct?: boolean;
  confidence?: number;
  user_answer?: string;
  correct_answer?: string;
  topic_id?: string;
  attempts: number;
  status?: "correct" | "incorrect" | "invalid_input" | "needs_review";
  part_index?: number;
  part_complete?: boolean;
  lesson_complete?: boolean;
  mastery_awarded?: false;
}

export interface PandaCurricularState {
  lesson_id: string | null;
  content_version: string | null;
  part_index: number;
  part_count: number;
  part_complete: boolean;
  awaiting_advance: boolean;
  lesson_complete: boolean;
  mastery_awarded: false;
}

export interface PandaReport {
  summary: string;
  weak_topic: PandaWeakTopic | null;
  practice_result: "success" | "needs_review";
  recommendations: string[];
}

export interface PandaBackendState {
  phase: PandaPhase;
  actual_grade?: number | null;
  weak_topic: PandaWeakTopic | null;
  current_practice: PandaCurrentPractice | null;
  practice_feedback?: PandaPracticeFeedback | null;
  report: PandaReport | null;
  curricular?: PandaCurricularState;
}

export interface PandaVisual {
  type?: string;
  grade?: number;
  page?: string;
  fallback_image?: string;
  component?: unknown;
  data?: unknown;
}

export interface PandaChatResponse {
  text: string;
  visual: PandaVisual | null;
  state: PandaBackendState;
}

export interface PandaChatRequest {
  user_id: string;
  message: string;
  name: string | null;
  grade: number | null;
  mode?: 'kungfu' | 'homework' | 'curricular' | null;
  lesson_id?: string | null;
  content_version?: string | null;
  action?: 'start' | 'answer' | 'hint' | 'advance' | null;
}
