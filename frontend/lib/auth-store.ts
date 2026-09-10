import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type UserRole = 'student' | 'parent';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar?: string;
  createdAt: Date;
}

export interface StudentProfile {
  userId: string;
  currentGrade: number;
  unlockedGrades: number[];
  qiEnergy: number;
  beltLevel: 'white' | 'yellow' | 'green' | 'black';
  correctAnswers: number;
  totalAnswers: number;
  lessonsCompleted: number;
  weeklyProgress: number[];
  weakTopics: string[];
  lastSessionGrade?: number;
}

export interface Subscription {
  plan: 'free' | 'basic' | 'premium';
  status: 'active' | 'cancelled' | 'expired';
  expiresAt?: Date;
}

interface AuthStore {
  user: User | null;
  studentProfile: StudentProfile | null;
  subscription: Subscription;
  isAuthenticated: boolean;
  isParentView: boolean;
  hasHydrated: boolean;
  
  login: (email: string, password: string) => Promise<boolean>;
  signup: (email: string, password: string, name: string, role: UserRole) => Promise<boolean>;
  logout: () => void;
  setParentView: (isParent: boolean) => void;
  updateStudentProfile: (update: Partial<StudentProfile>) => void;
  addQiEnergy: (amount: number) => void;
  unlockGrade: (grade: number) => void;
  completeLesson: () => void;
  setHasHydrated: (hydrated: boolean) => void;
}

const getBeltLevel = (correctAnswers: number): 'white' | 'yellow' | 'green' | 'black' => {
  if (correctAnswers >= 50) return 'black';
  if (correctAnswers >= 25) return 'green';
  if (correctAnswers >= 10) return 'yellow';
  return 'white';
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      studentProfile: null,
      subscription: { plan: 'free', status: 'active' },
      isAuthenticated: false,
      isParentView: false,
      hasHydrated: false,

      login: async (email: string, _password: string) => {
        // Simulated login - in production, call your auth API
        await new Promise(resolve => setTimeout(resolve, 800));
        
        const user: User = {
          id: crypto.randomUUID(),
          email,
          name: email.split('@')[0],
          role: 'student',
          createdAt: new Date(),
        };

        const studentProfile: StudentProfile = {
          userId: user.id,
          currentGrade: 3,
          unlockedGrades: [1, 2, 3],
          qiEnergy: 45,
          beltLevel: 'yellow',
          correctAnswers: 15,
          totalAnswers: 22,
          lessonsCompleted: 8,
          weeklyProgress: [3, 5, 2, 4, 6, 3, 2],
          weakTopics: ['Деление на 2 цифры', 'Дроби'],
          lastSessionGrade: 3,
        };

        set({ 
          user, 
          studentProfile,
          isAuthenticated: true 
        });
        return true;
      },

      signup: async (email: string, _password: string, name: string, role: UserRole) => {
        await new Promise(resolve => setTimeout(resolve, 800));
        
        const user: User = {
          id: crypto.randomUUID(),
          email,
          name,
          role,
          createdAt: new Date(),
        };

        const studentProfile: StudentProfile = {
          userId: user.id,
          currentGrade: 1,
          unlockedGrades: [1],
          qiEnergy: 0,
          beltLevel: 'white',
          correctAnswers: 0,
          totalAnswers: 0,
          lessonsCompleted: 0,
          weeklyProgress: [0, 0, 0, 0, 0, 0, 0],
          weakTopics: [],
        };

        set({ 
          user, 
          studentProfile,
          isAuthenticated: true 
        });
        return true;
      },

      logout: () => {
        set({ 
          user: null, 
          studentProfile: null,
          isAuthenticated: false,
          isParentView: false 
        });
      },

      setParentView: (isParent) => set({ isParentView: isParent }),

      updateStudentProfile: (update) => set((state) => ({
        studentProfile: state.studentProfile 
          ? { ...state.studentProfile, ...update }
          : null
      })),

      addQiEnergy: (amount) => set((state) => {
        if (!state.studentProfile) return state;
        const newQi = Math.min(100, state.studentProfile.qiEnergy + amount);
        const newCorrect = amount > 0 
          ? state.studentProfile.correctAnswers + 1 
          : state.studentProfile.correctAnswers;
        return {
          studentProfile: {
            ...state.studentProfile,
            qiEnergy: newQi,
            correctAnswers: newCorrect,
            totalAnswers: state.studentProfile.totalAnswers + 1,
            beltLevel: getBeltLevel(newCorrect),
          }
        };
      }),

      unlockGrade: (grade) => set((state) => {
        if (!state.studentProfile) return state;
        if (state.studentProfile.unlockedGrades.includes(grade)) return state;
        return {
          studentProfile: {
            ...state.studentProfile,
            unlockedGrades: [...state.studentProfile.unlockedGrades, grade].sort((a, b) => a - b),
          }
        };
      }),

      completeLesson: () => set((state) => {
        if (!state.studentProfile) return state;
        const today = new Date().getDay();
        const newWeekly = [...state.studentProfile.weeklyProgress];
        newWeekly[today] = (newWeekly[today] || 0) + 1;
        return {
          studentProfile: {
            ...state.studentProfile,
            lessonsCompleted: state.studentProfile.lessonsCompleted + 1,
            weeklyProgress: newWeekly,
          }
        };
      }),

      setHasHydrated: (hydrated) => set({ hasHydrated: hydrated }),
    }),
    {
      name: 'master-kwatt-auth',
      partialize: (state) => ({
        user: state.user,
        studentProfile: state.studentProfile,
        subscription: state.subscription,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => () => {
        useAuthStore.setState({ hasHydrated: true });
      },
    }
  )
);
