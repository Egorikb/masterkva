"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useAuthStore } from "@/lib/auth-store";
import { 
  Zap, 
  Play, 
  Lock, 
  Unlock, 
  BookOpen, 
  Trophy,
  TrendingUp,
  Star
} from "lucide-react";
import { cn } from "@/lib/utils";

const scrolls = [
  { grade: 1, subject: "Математика", icon: "🔢" },
  { grade: 2, subject: "Математика", icon: "➕" },
  { grade: 3, subject: "Математика", icon: "✖️" },
  { grade: 4, subject: "Математика", icon: "➗" },
  { grade: 5, subject: "Математика", icon: "📐" },
  { grade: 6, subject: "Математика", icon: "📊" },
  { grade: 7, subject: "Математика", icon: "📈" },
  { grade: 8, subject: "Математика", icon: "🔬" },
  { grade: 9, subject: "Математика", icon: "🧮" },
  { grade: 10, subject: "Наука", label: "Наука 1", icon: "🌍" },
  { grade: 11, subject: "Наука", label: "Наука 2", icon: "⚗️" },
  { grade: 12, subject: "Наука", label: "Наука 3", icon: "🧬" },
];

export default function DashboardPage() {
  const { user, studentProfile } = useAuthStore();

  const beltNames: Record<string, string> = {
    white: "Белый пояс",
    yellow: "Жёлтый пояс",
    green: "Зелёный пояс",
    black: "Чёрный пояс",
  };

  const beltColors: Record<string, string> = {
    white: "from-gray-100 to-gray-200 text-gray-800",
    yellow: "from-yellow-300 to-yellow-500 text-yellow-900",
    green: "from-primary to-jade-dark text-white",
    black: "from-gray-800 to-gray-900 text-white",
  };

  if (!studentProfile) return null;

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <motion.h1 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-2xl font-bold text-foreground lg:text-3xl"
        >
          Привет, {user?.name}!
        </motion.h1>
        <p className="text-muted-foreground">Готов к новым свершениям?</p>
      </div>

      {/* Top Cards Grid */}
      <div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Continue Journey Card */}
        {studentProfile.lastSessionGrade && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Play className="h-5 w-5 text-primary" />
                  Продолжить путь
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-4 text-muted-foreground">
                  Последний урок: Математика {studentProfile.lastSessionGrade} класс
                </p>
                <Link href={`/dashboard/session?grade=${studentProfile.lastSessionGrade}`}>
                  <Button className="w-full bg-primary hover:bg-primary/90">
                    Продолжить
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Qi Energy Hub */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Zap className="h-5 w-5 text-gold" />
                Энергия Ци
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-3 flex items-end justify-between">
                <span className="text-3xl font-bold text-foreground">
                  {studentProfile.qiEnergy}
                </span>
                <span className="text-sm text-muted-foreground">/ 100</span>
              </div>
              <Progress 
                value={studentProfile.qiEnergy} 
                className="h-3 [&>div]:bg-gradient-to-r [&>div]:from-gold [&>div]:to-accent"
              />
              <p className="mt-3 text-sm text-muted-foreground">
                Зарабатывай Ци правильными ответами!
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Belt Level */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className={cn(
            "bg-gradient-to-br",
            beltColors[studentProfile.beltLevel]
          )}>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Star className="h-5 w-5" />
                Твой ранг
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {beltNames[studentProfile.beltLevel]}
              </p>
              <p className="mt-2 text-sm opacity-80">
                {studentProfile.correctAnswers} правильных ответов
              </p>
              <div className="mt-3 text-xs opacity-70">
                До следующего пояса: {
                  studentProfile.beltLevel === "white" ? 10 - studentProfile.correctAnswers :
                  studentProfile.beltLevel === "yellow" ? 25 - studentProfile.correctAnswers :
                  studentProfile.beltLevel === "green" ? 50 - studentProfile.correctAnswers :
                  "Максимальный уровень!"
                }
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Stats Row */}
      <div className="mb-8 grid gap-4 grid-cols-2 lg:grid-cols-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <BookOpen className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{studentProfile.lessonsCompleted}</p>
              <p className="text-xs text-muted-foreground">Уроков пройдено</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-100 text-green-600">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">
                {studentProfile.totalAnswers > 0 
                  ? Math.round((studentProfile.correctAnswers / studentProfile.totalAnswers) * 100)
                  : 0}%
              </p>
              <p className="text-xs text-muted-foreground">Точность</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gold/20 text-gold">
              <Trophy className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{studentProfile.correctAnswers}</p>
              <p className="text-xs text-muted-foreground">Верных ответов</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
              <Unlock className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{studentProfile.unlockedGrades.length}</p>
              <p className="text-xs text-muted-foreground">Свитков открыто</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Scroll Map */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <h2 className="mb-4 text-xl font-bold text-foreground">Карта Свитков</h2>
        <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {scrolls.map((scroll, index) => {
            const isUnlocked = studentProfile.unlockedGrades.includes(scroll.grade);
            return (
              <motion.div
                key={scroll.grade}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.05 * index }}
              >
                {isUnlocked ? (
                  <Link href={`/dashboard/session?grade=${scroll.grade}`}>
                    <Card className="group cursor-pointer border-primary/20 transition-all hover:border-primary hover:shadow-lg">
                      <CardContent className="flex flex-col items-center p-4 text-center">
                        <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-2xl transition-transform group-hover:scale-110">
                          {scroll.icon}
                        </div>
                        <span className="text-sm font-medium text-foreground">
                          {scroll.label || `${scroll.subject} ${scroll.grade}`}
                        </span>
                        <span className="mt-1 flex items-center gap-1 text-xs text-primary">
                          <Unlock className="h-3 w-3" />
                          Открыто
                        </span>
                      </CardContent>
                    </Card>
                  </Link>
                ) : (
                  <Card className="cursor-not-allowed opacity-50">
                    <CardContent className="flex flex-col items-center p-4 text-center">
                      <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-muted text-2xl grayscale">
                        {scroll.icon}
                      </div>
                      <span className="text-sm font-medium text-muted-foreground">
                        {scroll.label || `${scroll.subject} ${scroll.grade}`}
                      </span>
                      <span className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                        <Lock className="h-3 w-3" />
                        Закрыто
                      </span>
                    </CardContent>
                  </Card>
                )}
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}
