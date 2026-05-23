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
  prompt?: string;
  title?: string;
  operation?: 'add' | 'subtract';
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

export interface QuestionVisualSection {
  label: string;
  kind: 'concrete' | 'pictorial' | 'abstract';
  bullets: string[];
}

export interface QuestionVisualData {
  type: 'question';
  title: string;
  prompt: string;
  cpaVisual: 'counting' | 'position' | 'carry' | 'number_line' | 'addition' | 'shapes' | 'clock' | 'division' | 'mixed_ops' | 'unknown';
  objects?: string;
  parts?: number[];
  colors?: string[];
  answer?: string;
  topic?: string;
  templateType?: string;
  templateFamily?: string;
  templateLabel?: string;
  templateStage?: 'concrete' | 'pictorial' | 'abstract' | 'concrete_pictorial_abstract';
  templateGlyph?: string;
  templateSections?: QuestionVisualSection[];
  templateHide?: string;
  templateWhy?: string;
  templateNotes?: string;
  templatePreview?: {
    type: string;
    [key: string]: unknown;
  };
  templateReason?: string;
  templateSkills?: string[];
}

export type VisualData = NumberBondData | BarModelData | TenFrameData | QuestionVisualData;

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
