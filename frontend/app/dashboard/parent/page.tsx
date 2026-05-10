"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuthStore } from "@/lib/auth-store";
import { 
  BarChart3, 
  TrendingUp, 
  AlertTriangle, 
  CreditCard,
  CheckCircle2,
  Calendar,
  Clock,
  Target,
  BookOpen,
  Star,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

const weekDays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const plans = [
  {
    id: "free",
    name: "Бесплатный",
    price: "0 ₽",
    period: "навсегда",
    features: ["5 уроков в день", "Базовые темы", "Email поддержка"],
    current: true,
  },
  {
    id: "basic",
    name: "Базовый",
    price: "499 ₽",
    period: "в месяц",
    features: ["Безлимитные уроки", "Все темы", "Приоритетная поддержка", "Без рекламы"],
    popular: true,
  },
  {
    id: "premium",
    name: "Премиум",
    price: "999 ₽",
    period: "в месяц",
    features: ["Всё из Базового", "Индивидуальные уроки", "Отчёты для учителя", "Семейный доступ (до 3 детей)"],
  },
];

export default function ParentPortalPage() {
  const { studentProfile, user, subscription } = useAuthStore();
  const [activeTab, setActiveTab] = useState("progress");

  if (!studentProfile || !user) return null;

  // Prepare chart data
  const chartData = studentProfile.weeklyProgress.map((value, index) => ({
    day: weekDays[index],
    lessons: value,
  }));

  const totalWeeklyLessons = studentProfile.weeklyProgress.reduce((a, b) => a + b, 0);
  const accuracy = studentProfile.totalAnswers > 0 
    ? Math.round((studentProfile.correctAnswers / studentProfile.totalAnswers) * 100)
    : 0;

  return (
    <div className="p-6 lg:p-8">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground lg:text-3xl">
              Портал для родителей
            </h1>
            <p className="text-muted-foreground">
              Отслеживайте успехи {user.name}
            </p>
          </div>
          <Badge variant="outline" className="gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500" />
            Активен
          </Badge>
        </div>
      </motion.div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="progress" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline">Прогресс</span>
          </TabsTrigger>
          <TabsTrigger value="analysis" className="gap-2">
            <Target className="h-4 w-4" />
            <span className="hidden sm:inline">Анализ</span>
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-2">
            <CreditCard className="h-4 w-4" />
            <span className="hidden sm:inline">Подписка</span>
          </TabsTrigger>
        </TabsList>

        {/* Progress Tab */}
        <TabsContent value="progress" className="space-y-6">
          {/* Quick Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <BookOpen className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{totalWeeklyLessons}</p>
                    <p className="text-xs text-muted-foreground">Уроков за неделю</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-100 text-green-600">
                    <TrendingUp className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{accuracy}%</p>
                    <p className="text-xs text-muted-foreground">Точность</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gold/20 text-gold">
                    <Star className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{studentProfile.correctAnswers}</p>
                    <p className="text-xs text-muted-foreground">Верных ответов</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
                    <Clock className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{studentProfile.lessonsCompleted}</p>
                    <p className="text-xs text-muted-foreground">Всего уроков</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Weekly Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-primary" />
                Активность за неделю
              </CardTitle>
              <CardDescription>
                Количество пройденных уроков по дням
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <XAxis 
                      dataKey="day" 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    />
                    <YAxis 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="rounded-lg border border-border bg-card p-2 shadow-lg">
                              <p className="text-sm font-medium">{payload[0].payload.day}</p>
                              <p className="text-sm text-muted-foreground">
                                {payload[0].value} урок(а)
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar 
                      dataKey="lessons" 
                      fill="hsl(var(--primary))" 
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Belt Progress */}
          <Card>
            <CardHeader>
              <CardTitle>Путь к мастерству</CardTitle>
              <CardDescription>Прогресс получения поясов</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { belt: "white", name: "Белый пояс", req: 0, next: 10 },
                  { belt: "yellow", name: "Жёлтый пояс", req: 10, next: 25 },
                  { belt: "green", name: "Зелёный пояс", req: 25, next: 50 },
                  { belt: "black", name: "Чёрный пояс", req: 50, next: null },
                ].map((item) => {
                  const isEarned = studentProfile.correctAnswers >= item.req;
                  const isCurrent = studentProfile.beltLevel === item.belt;
                  const progress = item.next 
                    ? Math.min(100, ((studentProfile.correctAnswers - item.req) / (item.next - item.req)) * 100)
                    : 100;

                  return (
                    <div 
                      key={item.belt}
                      className={cn(
                        "flex items-center gap-4 rounded-xl p-3",
                        isCurrent && "bg-primary/5 ring-1 ring-primary/20"
                      )}
                    >
                      <div className={cn(
                        "flex h-10 w-10 items-center justify-center rounded-full",
                        item.belt === "white" && "bg-gray-100",
                        item.belt === "yellow" && "bg-yellow-400",
                        item.belt === "green" && "bg-primary",
                        item.belt === "black" && "bg-gray-900",
                        !isEarned && "opacity-40"
                      )}>
                        {isEarned && <CheckCircle2 className="h-5 w-5 text-white" />}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className={cn(
                            "font-medium",
                            !isEarned && "text-muted-foreground"
                          )}>
                            {item.name}
                          </span>
                          {isCurrent && (
                            <Badge variant="outline" className="text-xs">Текущий</Badge>
                          )}
                        </div>
                        {isCurrent && item.next && (
                          <div className="mt-2">
                            <Progress value={Math.max(0, progress)} className="h-2" />
                            <p className="mt-1 text-xs text-muted-foreground">
                              {studentProfile.correctAnswers} / {item.next} ответов
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis" className="space-y-6">
          {/* Weak Topics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                Темы для повторения
              </CardTitle>
              <CardDescription>
                Темы, которые требуют дополнительной практики
              </CardDescription>
            </CardHeader>
            <CardContent>
              {studentProfile.weakTopics.length > 0 ? (
                <ul className="space-y-3">
                  {studentProfile.weakTopics.map((topic, index) => (
                    <li 
                      key={index}
                      className="flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 p-4"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100 text-amber-600">
                          <Target className="h-4 w-4" />
                        </div>
                        <span className="font-medium text-amber-900">{topic}</span>
                      </div>
                      <ChevronRight className="h-5 w-5 text-amber-400" />
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="flex flex-col items-center py-8 text-center">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                    <CheckCircle2 className="h-8 w-8 text-green-600" />
                  </div>
                  <h3 className="mb-2 font-semibold text-foreground">Отлично!</h3>
                  <p className="text-muted-foreground">
                    Пока нет тем, требующих повторения
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle>Рекомендации</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-start gap-3 rounded-xl bg-blue-50 p-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                    <Clock className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="font-medium text-blue-900">Регулярность</h4>
                    <p className="text-sm text-blue-700">
                      Рекомендуем заниматься 15-20 минут каждый день для лучших результатов.
                    </p>
                  </div>
                </li>
                <li className="flex items-start gap-3 rounded-xl bg-green-50 p-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-100 text-green-600">
                    <TrendingUp className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="font-medium text-green-900">Прогресс</h4>
                    <p className="text-sm text-green-700">
                      Точность {accuracy}% — {accuracy >= 70 ? "отличный результат!" : "есть куда расти!"}
                    </p>
                  </div>
                </li>
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Billing Tab */}
        <TabsContent value="billing" className="space-y-6">
          {/* Current Plan */}
          <Card className="border-primary/20 bg-primary/5">
            <CardHeader>
              <CardTitle>Текущий план</CardTitle>
              <CardDescription>Управление подпиской</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xl font-bold text-foreground">
                    {subscription.plan === "free" && "Бесплатный"}
                    {subscription.plan === "basic" && "Базовый"}
                    {subscription.plan === "premium" && "Премиум"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Статус: {subscription.status === "active" ? "Активен" : "Неактивен"}
                  </p>
                </div>
                <Badge variant="outline" className="text-primary">
                  {subscription.status === "active" ? "Активен" : "Истёк"}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Plans */}
          <div className="grid gap-4 md:grid-cols-3">
            {plans.map((plan) => (
              <Card 
                key={plan?.id || `key-${Date.now()}`}
                className={cn(
                  "relative",
                  plan.popular && "border-primary shadow-lg",
                  plan.current && "bg-muted/50"
                )}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-primary">Популярный</Badge>
                  </div>
                )}
                <CardHeader>
                  <CardTitle>{plan.name}</CardTitle>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground">/ {plan.period}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="mb-6 space-y-2">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-2 text-sm">
                        <CheckCircle2 className="h-4 w-4 text-primary" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Button 
                    className="w-full"
                    variant={plan.current ? "outline" : plan.popular ? "default" : "outline"}
                    disabled={plan.current}
                  >
                    {plan.current ? "Текущий план" : "Выбрать"}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
