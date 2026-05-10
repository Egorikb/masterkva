"use client";

import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useAuthStore } from "@/lib/auth-store";
import { 
  Trophy, 
  Star, 
  Zap, 
  Target, 
  Flame, 
  Medal,
  BookOpen,
  Brain,
  Sparkles,
  Crown
} from "lucide-react";
import { cn } from "@/lib/utils";

const achievements = [
  {
    id: "first_answer",
    title: "Первый шаг",
    description: "Ответь на первый вопрос",
    icon: Star,
    requirement: 1,
    type: "answers",
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
  },
  {
    id: "ten_correct",
    title: "Жёлтый пояс",
    description: "Получи 10 правильных ответов",
    icon: Medal,
    requirement: 10,
    type: "correct",
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
  },
  {
    id: "twenty_five_correct",
    title: "Зелёный пояс",
    description: "Получи 25 правильных ответов",
    icon: Medal,
    requirement: 25,
    type: "correct",
    color: "text-green-500",
    bgColor: "bg-green-500/10",
  },
  {
    id: "fifty_correct",
    title: "Чёрный пояс",
    description: "Получи 50 правильных ответов",
    icon: Crown,
    requirement: 50,
    type: "correct",
    color: "text-gray-900",
    bgColor: "bg-gray-900/10",
  },
  {
    id: "qi_master",
    title: "Мастер Ци",
    description: "Накопи 100 энергии Ци",
    icon: Zap,
    requirement: 100,
    type: "qi",
    color: "text-gold",
    bgColor: "bg-gold/10",
  },
  {
    id: "five_lessons",
    title: "Юный ученик",
    description: "Пройди 5 уроков",
    icon: BookOpen,
    requirement: 5,
    type: "lessons",
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  {
    id: "ten_lessons",
    title: "Прилежный ученик",
    description: "Пройди 10 уроков",
    icon: Brain,
    requirement: 10,
    type: "lessons",
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
  },
  {
    id: "accuracy_80",
    title: "Меткий стрелок",
    description: "Достигни 80% точности при 20+ ответах",
    icon: Target,
    requirement: 80,
    type: "accuracy",
    color: "text-red-500",
    bgColor: "bg-red-500/10",
  },
  {
    id: "streak_10",
    title: "В ударе!",
    description: "10 правильных ответов подряд",
    icon: Flame,
    requirement: 10,
    type: "streak",
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
  },
  {
    id: "all_grades",
    title: "Мастер всех искусств",
    description: "Открой все свитки",
    icon: Sparkles,
    requirement: 9,
    type: "grades",
    color: "text-primary",
    bgColor: "bg-primary/10",
  },
];

export default function AchievementsPage() {
  const { studentProfile } = useAuthStore();

  if (!studentProfile) return null;

  const getProgress = (achievement: typeof achievements[0]) => {
    switch (achievement.type) {
      case "answers":
        return studentProfile.totalAnswers;
      case "correct":
        return studentProfile.correctAnswers;
      case "qi":
        return studentProfile.qiEnergy;
      case "lessons":
        return studentProfile.lessonsCompleted;
      case "accuracy":
        return studentProfile.totalAnswers >= 20 
          ? Math.round((studentProfile.correctAnswers / studentProfile.totalAnswers) * 100)
          : 0;
      case "grades":
        return studentProfile.unlockedGrades.length;
      default:
        return 0;
    }
  };

  const earnedCount = achievements.filter(
    (a) => getProgress(a) >= a.requirement
  ).length;

  return (
    <div className="p-6 lg:p-8">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-2xl font-bold text-foreground lg:text-3xl">
          Зал Славы
        </h1>
        <p className="text-muted-foreground">
          Твои достижения и награды
        </p>
      </motion.div>

      {/* Summary */}
      <Card className="mb-8 bg-gradient-to-r from-primary/5 to-gold/5">
        <CardContent className="flex items-center gap-6 p-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gold/20 text-gold">
            <Trophy className="h-8 w-8" />
          </div>
          <div>
            <p className="text-3xl font-bold text-foreground">
              {earnedCount} / {achievements.length}
            </p>
            <p className="text-muted-foreground">достижений получено</p>
          </div>
          <div className="ml-auto hidden md:block">
            <Progress 
              value={(earnedCount / achievements.length) * 100} 
              className="h-3 w-48 [&>div]:bg-gold"
            />
          </div>
        </CardContent>
      </Card>

      {/* Achievements Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {achievements.map((achievement, index) => {
          const progress = getProgress(achievement);
          const isEarned = progress >= achievement.requirement;
          const progressPercent = Math.min(100, (progress / achievement.requirement) * 100);

          return (
            <motion.div
              key={achievement?.id || `key-${Date.now()}`}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.05 * index }}
            >
              <Card className={cn(
                "h-full transition-all",
                isEarned 
                  ? "border-gold/50 bg-gradient-to-br from-gold/5 to-gold/10" 
                  : "opacity-70"
              )}>
                <CardContent className="p-5">
                  <div className="mb-4 flex items-start justify-between">
                    <div className={cn(
                      "flex h-12 w-12 items-center justify-center rounded-xl",
                      isEarned ? achievement.bgColor : "bg-muted",
                      !isEarned && "grayscale"
                    )}>
                      <achievement.icon className={cn(
                        "h-6 w-6",
                        isEarned ? achievement.color : "text-muted-foreground"
                      )} />
                    </div>
                    {isEarned && (
                      <Badge className="bg-gold text-gold-foreground">
                        Получено!
                      </Badge>
                    )}
                  </div>
                  <h3 className={cn(
                    "mb-1 font-semibold",
                    isEarned ? "text-foreground" : "text-muted-foreground"
                  )}>
                    {achievement.title}
                  </h3>
                  <p className="mb-4 text-sm text-muted-foreground">
                    {achievement.description}
                  </p>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Прогресс</span>
                      <span className={isEarned ? "text-primary font-medium" : "text-foreground"}>
                        {progress} / {achievement.requirement}
                      </span>
                    </div>
                    <Progress 
                      value={progressPercent} 
                      className={cn(
                        "h-2",
                        isEarned && "[&>div]:bg-gold"
                      )}
                    />
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
