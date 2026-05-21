import { create } from 'zustand';
import type { LearningMode, UserProgress, ChatMessage, BeltLevel } from './types';

interface ChatStore {
  mode: LearningMode;
  setMode: (mode: LearningMode) => void;
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  progress: UserProgress;
  updateProgress: (update: Partial<UserProgress>) => void;
  addQiEnergy: (amount: number) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  currentVisualData: ChatMessage['visualData'] | null;
  setCurrentVisualData: (data: ChatMessage['visualData'] | null) => void;
}

const getBeltLevel = (correctAnswers: number): BeltLevel => {
  if (correctAnswers >= 50) return 'black';
  if (correctAnswers >= 25) return 'green';
  if (correctAnswers >= 10) return 'yellow';
  return 'white';
};

export const useChatStore = create<ChatStore>((set) => ({
  mode: null,
  setMode: (mode) => set({ mode }),
  messages: [],
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message],
    currentVisualData: message.visualData || state.currentVisualData
  })),
  clearMessages: () => set({ messages: [], currentVisualData: null }),
  progress: {
    qiEnergy: 0,
    beltLevel: 'white',
    correctAnswers: 0,
    totalAnswers: 0,
  },
  updateProgress: (update) => set((state) => ({
    progress: { ...state.progress, ...update }
  })),
  addQiEnergy: (amount) => set((state) => {
    const newQi = Math.min(100, state.progress.qiEnergy + amount);
    const newCorrectAnswers = amount > 0 ? state.progress.correctAnswers + 1 : state.progress.correctAnswers;
    return {
      progress: {
        ...state.progress,
        qiEnergy: newQi,
        correctAnswers: newCorrectAnswers,
        totalAnswers: state.progress.totalAnswers + 1,
        beltLevel: getBeltLevel(newCorrectAnswers),
      }
    };
  }),
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
  currentVisualData: null,
  setCurrentVisualData: (data) => set({ currentVisualData: data }),
}));
