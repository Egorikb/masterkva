export type LearningMode = 'kungfu' | 'homework' | null;

export type BeltLevel = 'white' | 'yellow' | 'green' | 'black';

export interface UserProgress {
  qiEnergy: number;
  beltLevel: BeltLevel;
  correctAnswers: number;
  totalAnswers: number;
}

export interface NumberBondData {
  type: 'number_bond';
  total: number;
  parts: number[];
}

export interface BarModelData {
  type: 'bar_model';
  total: number;
  segments: { value: number; label: string; color?: string }[];
}

export interface TenFrameData {
  type: 'ten_frame';
  filled: number;
  total?: number;
}

export type VisualData = NumberBondData | BarModelData | TenFrameData;

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  audioUrl?: string;
  visualData?: VisualData;
  timestamp: Date;
}

export interface ApiResponse {
  text: string;
  audio_url?: string;
  visual_data?: VisualData;
  is_correct?: boolean;
  qi_bonus?: number;
}
