"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/lib/auth-store";
import { Lock, Unlock, BookOpen, Star, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

const scrolls = [
  { 
    grade: 1, 
    subject: "Математика", 
    icon: "🔢",
    topics: ["Счёт до 20", "Сложение", "Вычитание"]
  },
  { 
    grade: 2, 
    subject: "Математика", 
    icon: "➕",
    topics: ["Счёт до 100", "Таблица сложения", "Введение в умножение"]
  },
  { 
    grade: 3, 
    subject: "Математика", 
    icon: "✖️",
    topics: ["Таблица умножения", "Деление", "Задачи на логику"]
  },
  { 
    grade: 4, 
    subject: "Математика", 
    icon: "➗",
    topics: ["Многозначные числа", "Деление в столбик", "Дроби"]
  },
  { 
    grade: 5, 
    subject: "Математика", 
    icon: "📐",
    topics: ["Десятичные дроби", "Проценты", "Геометрия"]
  },
  { 
    grade: 6, 
    subject: "Математика", 
    icon: "📊",
    topics: ["Отрицательные числа", "Пропорции", "Уравнения"]
  },
  { 
    grade: 7, 
    subject: "Математика", 
    icon: "📈",
    topics: ["Алгебра", "Функции", "Системы уравнений"]
  },
  { 
    grade: 8, 
    subject: "Математика", 
    icon: "🔬",
    topics: ["Квадратные уравнения", "Теорема Пифагора", "Тригонометрия"]
  },
  { 
    grade: 9, 
    subject: "Математика", 
    icon: "🧮",
    topics: ["Прогрессии", "Статистика", "Подготовка к ОГЭ"]
  },
];

export default function ScrollsPage() {
  const { studentProfile } = useAuthStore();

  if (!studentProfile) return null;

  return (
    <div className="p-6 lg:p-8">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-2xl font-bold text-foreground lg:text-3xl">
          Библиотека Свитков
        </h1>
        <p className="text-muted-foreground">
          Выбери класс и начни тренировку
        </p>
      </motion.div>

      {/* Stats */}
      <div className="mb-8 flex gap-4">
        <Badge variant="outline" className="gap-2 px-4 py-2 text-sm">
          <Unlock className="h-4 w-4 text-primary" />
          {studentProfile.unlockedGrades.length} открыто
        </Badge>
        <Badge variant="outline" className="gap-2 px-4 py-2 text-sm">
          <Lock className="h-4 w-4 text-muted-foreground" />
          {9 - studentProfile.unlockedGrades.length} закрыто
        </Badge>
      </div>

      {/* Scrolls Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {scrolls.map((scroll, index) => {
          const isUnlocked = studentProfile.unlockedGrades.includes(scroll.grade);
          const isLast = studentProfile.lastSessionGrade === scroll.grade;

          return (
            <motion.div
              key={scroll.grade}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * index }}
            >
              {isUnlocked ? (
                <Link href={`/dashboard/session?grade=${scroll.grade}`}>
                  <Card className={cn(
                    "group h-full cursor-pointer border-primary/20 transition-all hover:border-primary hover:shadow-lg",
                    isLast && "ring-2 ring-primary ring-offset-2"
                  )}>
                    {isLast && (
                      <div className="absolute -top-2 left-4">
                        <Badge className="bg-primary text-xs">Последний</Badge>
                      </div>
                    )}
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-3xl transition-transform group-hover:scale-110">
                          {scroll.icon}
                        </div>
                        <Badge variant="outline" className="gap-1 text-primary">
                          <Unlock className="h-3 w-3" />
                          Открыто
                        </Badge>
                      </div>
                      <CardTitle className="text-xl">
                        {scroll.subject} {scroll.grade} класс
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="mb-3 text-sm text-muted-foreground">Темы:</p>
                      <ul className="space-y-2">
                        {scroll.topics.map((topic) => (
                          <li key={topic} className="flex items-center gap-2 text-sm text-foreground">
                            <CheckCircle2 className="h-4 w-4 text-primary" />
                            {topic}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                </Link>
              ) : (
                <Card className="h-full cursor-not-allowed opacity-60">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted text-3xl grayscale">
                        {scroll.icon}
                      </div>
                      <Badge variant="outline" className="gap-1 text-muted-foreground">
                        <Lock className="h-3 w-3" />
                        Закрыто
                      </Badge>
                    </div>
                    <CardTitle className="text-xl text-muted-foreground">
                      {scroll.subject} {scroll.grade} класс
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Star className="h-4 w-4" />
                      <span>Пройди предыдущий уровень</span>
                    </div>
                  </CardContent>
                </Card>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
