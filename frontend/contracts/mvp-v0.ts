export interface BackendSessionStateV0 {
  current_level: string;
  strong_topics: string[];
  weak_spots: string[];
  session_goal: "diagnostic" | "learning";
  recommendation: string;
}

export interface VisualV0 {
  type?: string;
  grade: number;
  page: string;
  fallback_image?: string;
  component?: unknown;
}

declare const assistantTextV0Brand: unique symbol;
export type AssistantTextV0 = string & { readonly [assistantTextV0Brand]: true };

export interface ChatResponseV0 {
  text: AssistantTextV0;
  visual: VisualV0 | null;
  backend_state: BackendSessionStateV0;
}
