"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ChatInterface } from "@/components/chat-interface";
import { InteractiveBlackboard } from "@/components/interactive-blackboard";
import { useAuthStore } from "@/lib/auth-store";
import { useChatStore } from "@/lib/chat-store";
import { 
  ArrowLeft, 
  Zap, 
  Award, 
  BookOpen, 
  Scroll,
  Home
} from "lucide-react";

const beltColors = {
  white: "bg-gray-100 text-gray-800 border-gray-300",
  yellow: "bg-yellow-100 text-yellow-800 border-yellow-400",
  green: "bg-emerald-100 text-emerald-800 border-emerald-500",
  black: "bg-gray-900 text-white border-gray-700",
};

const beltNames = {
  white: "Белый пояс",
  yellow: "Жёлтый пояс",
  green: "Зелёный пояс",
  black: "Чёрный пояс",
};

function SessionContent() {
  const searchParams = useSearchParams();
  const grade = searchParams.get("grade");
  const modeParam = searchParams.get("mode");
  
  const { studentProfile, updateStudentProfile } = useAuthStore();
  const { mode, setMode, clearMessages } = useChatStore();
  const [selectedMode, setSelectedMode] = useState<"kungfu" | "homework" | null>(null);

  // Set the mode from URL param or show selector
  useEffect(() => {
    if (modeParam === "kungfu" || modeParam === "homework") {
      setMode(modeParam);
      setSelectedMode(modeParam);
    }
  }, [modeParam, setMode]);

  // Update last session grade
  useEffect(() => {
    if (grade && studentProfile) {
      updateStudentProfile({ lastSessionGrade: parseInt(grade) });
    }
  }, [grade, studentProfile, updateStudentProfile]);

  const handleModeSelect = (newMode: "kungfu" | "homework") => {
    setMode(newMode);
    setSelectedMode(newMode);
  };

  const handleBack = () => {
    setMode(null);
    setSelectedMode(null);
    clearMessages();
  };

  if (!studentProfile) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-6 text-center">
        <h1 className="mb-2 text-2xl font-bold text-foreground">Кабинет ещё не готов</h1>
        <p className="mb-6 max-w-md text-muted-foreground">
          Сначала войди или зарегистрируйся, чтобы открыть личный кабинет и диалог с учителем.
        </p>
        <div className="flex gap-3">
          <Link href="/login">
            <Button>Войти</Button>
          </Link>
          <Link href="/signup">
            <Button variant="outline">Создать аккаунт</Button>
          </Link>
        </div>
      </div>
    );
  }

  // Mode selection screen
  if (!selectedMode && !mode) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-2xl"
        >
          <Link href="/dashboard" className="mb-8 inline-flex items-center gap-2 text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            Назад к свиткам
          </Link>

          <h1 className="mb-2 text-3xl font-bold text-foreground">
            Математика {grade} класс
          </h1>
          <p className="mb-8 text-muted-foreground">
            Выбери режим обучения
          </p>

          <div className="grid gap-4 md:grid-cols-2">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleModeSelect("kungfu")}
              className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary to-jade-dark p-6 text-left shadow-lg transition-shadow hover:shadow-xl"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
              <div className="relative z-10">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-white/20">
                  <Scroll className="h-6 w-6 text-white" />
                </div>
                <h2 className="mb-2 text-xl font-bold text-white">Свитки Кунг-фу</h2>
                <p className="text-sm text-white/80">
                  Глубокое изучение с методом CPA
                </p>
              </div>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleModeSelect("homework")}
              className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-gold to-accent p-6 text-left shadow-lg transition-shadow hover:shadow-xl"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
              <div className="relative z-10">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-white/20">
                  <BookOpen className="h-6 w-6 text-white" />
                </div>
                <h2 className="mb-2 text-xl font-bold text-white">Помощь с ДЗ</h2>
                <p className="text-sm text-white/80">
                  Быстрые объяснения для домашки
                </p>
              </div>
            </motion.button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Active session view
  return (
    <div className="flex h-screen flex-col">
      {/* Session Header */}
      <header className="shrink-0 border-b border-border bg-card">
        <div className="flex h-14 items-center justify-between px-4">
          {/* Left: Navigation */}
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleBack}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Сменить режим</span>
            </Button>
            <div className="h-6 w-px bg-border" />
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="gap-2">
                <Home className="h-4 w-4" />
                <span className="hidden sm:inline">Главная</span>
              </Button>
            </Link>
            <Badge variant="outline" className="ml-2">
              Математика {grade} класс
            </Badge>
          </div>

          {/* Center: Qi Energy */}
          <div className="hidden flex-1 max-w-xs items-center gap-3 px-4 md:flex">
            <Zap className="h-5 w-5 shrink-0 text-gold" />
            <div className="flex-1">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">
                  Энергия Ци
                </span>
                <span className="text-xs font-bold text-foreground">
                  {studentProfile.qiEnergy}/100
                </span>
              </div>
              <Progress 
                value={studentProfile.qiEnergy} 
                className="h-2 [&>div]:bg-gradient-to-r [&>div]:from-gold [&>div]:to-accent"
              />
            </div>
          </div>

          {/* Right: Belt Level */}
          <motion.div
            key={studentProfile.beltLevel}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`flex items-center gap-2 rounded-full border-2 px-3 py-1 ${beltColors[studentProfile.beltLevel]}`}
          >
            <Award className="h-4 w-4" />
            <span className="text-sm font-semibold">
              {beltNames[studentProfile.beltLevel]}
            </span>
          </motion.div>
        </div>
      </header>

      {/* Main Content - Split Screen */}
      <main className="flex flex-1 flex-col overflow-hidden lg:flex-row">
        {/* Chat Interface - Left Side (40%) */}
        <section className="flex h-[50vh] flex-col border-b border-border bg-card lg:h-auto lg:w-[40%] lg:border-b-0 lg:border-r">
          <ChatInterface />
        </section>

        {/* Interactive Blackboard - Right Side (60%) */}
        <section className="flex-1 overflow-auto p-4 lg:w-[60%] lg:p-6">
          <InteractiveBlackboard />
        </section>
      </main>
    </div>
  );
}

export default function SessionPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    }>
      <SessionContent />
    </Suspense>
  );
}
