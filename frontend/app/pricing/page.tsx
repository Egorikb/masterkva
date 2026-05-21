"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check } from "lucide-react";

const plans = [
  {
    name: "Старт",
    price: "Бесплатно",
    features: ["Базовые уроки", "Диагностика", "Сенсей Панда"],
  },
  {
    name: "Плюс",
    price: "Для родителей",
    features: ["Прогресс и отчёты", "Больше задач", "Персональные рекомендации"],
  },
  {
    name: "Премиум",
    price: "Максимум пользы",
    features: ["Все темы", "Глубокая аналитика", "Приоритетная поддержка"],
  },
];

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-background px-4 py-16">
      <div className="mx-auto max-w-5xl">
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-bold text-foreground">Тарифы</h1>
          <p className="mt-3 text-muted-foreground">Пока это чисто навигационная страница, но ссылка больше не ведёт в 404.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <Card key={plan.name} className="border-border/60">
              <CardHeader>
                <CardTitle>{plan.name}</CardTitle>
                <p className="text-sm text-muted-foreground">{plan.price}</p>
              </CardHeader>
              <CardContent className="space-y-3">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-center gap-2 text-sm text-foreground">
                    <Check className="h-4 w-4 text-primary" />
                    {feature}
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-10 flex justify-center gap-3">
          <Link href="/dashboard">
            <Button>Войти</Button>
          </Link>
          <Link href="/signup">
            <Button variant="outline">Создать аккаунт</Button>
          </Link>
        </div>
      </div>
    </main>
  );
}