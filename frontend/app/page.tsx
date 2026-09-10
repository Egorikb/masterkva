"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PandaSensei } from "@/components/panda-sensei";
import { useAuthStore } from "@/lib/auth-store";
import { 
  BookOpen, 
  GraduationCap, 
  Trophy, 
  Zap,
  ArrowRight,
  CheckCircle2,
  Brain,
  Sparkles,
  BarChart3,
  Shield
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "CPA Методика",
    description: "Конкретное → Наглядное → Абстрактное. Понимание вместо зубрёжки.",
  },
  {
    icon: BarChart3,
    title: "Барные модели",
    description: "Визуализация задач для глубокого понимания математики.",
  },
  {
    icon: Sparkles,
    title: "Геймификация",
    description: "Пояса, энергия Ци и достижения делают обучение увлекательным.",
  },
  {
    icon: Shield,
    title: "Безопасно для детей",
    description: "Дружелюбный интерфейс и родительский контроль.",
  },
];

const modes = [
  {
    title: "Путь Кунг-фу",
    icon: GraduationCap,
    description: "Глубокое изучение математики с Сенсеем Пандой",
    features: ["Пошаговое объяснение", "Интерактивная доска", "Визуализации CPA"],
    color: "from-primary to-jade-dark",
  },
  {
    title: "Помощь с ДЗ",
    icon: BookOpen,
    description: "Быстрая помощь с домашним заданием",
    features: ["Проверка решений", "Подсказки к задачам", "Разбор ошибок"],
    color: "from-gold to-accent",
  },
];

export default function LandingPage() {
  const { isAuthenticated } = useAuthStore();
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Zap className="h-6 w-6" />
            </div>
            <span className="text-xl font-bold text-foreground">Мастер Кват</span>
          </Link>
          <div className="hidden items-center gap-8 md:flex">
            <Link href="#methodology" className="text-muted-foreground transition-colors hover:text-foreground">
              Методика
            </Link>
            <Link href="#modes" className="text-muted-foreground transition-colors hover:text-foreground">
              Режимы
            </Link>
            <Link href="/pricing" className="text-muted-foreground transition-colors hover:text-foreground">
              Тарифы
            </Link>
          </div>
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link href="/dashboard">
                <Button variant="outline" size="sm">Кабинет</Button>
              </Link>
            ) : null}
            <Link href="/login">
              <Button variant="ghost" size="sm">Войти</Button>
            </Link>
            <Link href="/signup">
              <Button size="sm" className="bg-primary hover:bg-primary/90">
                Начать бесплатно
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden px-4 py-16 md:py-24">
        {/* Bamboo pattern background */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute left-0 top-0 h-full w-16 bg-gradient-to-r from-primary to-transparent" />
          <div className="absolute left-20 top-0 h-full w-8 bg-gradient-to-r from-primary/50 to-transparent" />
          <div className="absolute right-0 top-0 h-full w-16 bg-gradient-to-l from-primary to-transparent" />
          <div className="absolute right-20 top-0 h-full w-8 bg-gradient-to-l from-primary/50 to-transparent" />
        </div>

        <div className="relative mx-auto max-w-7xl">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center lg:text-left"
            >
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm text-primary">
                <Trophy className="h-4 w-4" />
                <span>Новый подход к математике</span>
              </div>
              <h1 className="mb-6 text-balance text-4xl font-bold tracking-tight text-foreground md:text-5xl lg:text-6xl">
                Освой математику с{" "}
                <span className="bg-gradient-to-r from-primary to-jade-dark bg-clip-text text-transparent">
                  китайскими техниками
                </span>
              </h1>
              <p className="mb-8 text-pretty text-lg text-muted-foreground md:text-xl">
                Интерактивная платформа для детей 7-12 лет. Сенсей Панда научит 
                решать задачи методами CPA и барных моделей в стиле Кунг-фу.
              </p>
              <div className="flex flex-col items-center gap-4 sm:flex-row lg:justify-start">
                <Link href="/signup">
                  <Button size="lg" className="w-full bg-primary px-8 hover:bg-primary/90 sm:w-auto">
                    Попробовать бесплатно
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
                <Link href="#methodology">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto">
                    Узнать больше
                  </Button>
                </Link>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative flex justify-center"
            >
              <div className="relative">
                {/* Glow effect */}
                <div className="absolute -inset-4 rounded-full bg-gradient-to-r from-primary/20 via-gold/20 to-primary/20 blur-3xl" />
                <div className="relative h-64 w-64 md:h-80 md:w-80">
                  <PandaSensei />
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Methodology Section */}
      <section id="methodology" className="bg-muted/30 px-4 py-16 md:py-24">
        <div className="mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-12 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold text-foreground md:text-4xl">
              Проверенная методика
            </h2>
            <p className="mx-auto max-w-2xl text-muted-foreground">
              Мы используем сингапурский метод математики, который помог 
              Сингапуру занять первое место в мировых рейтингах PISA.
            </p>
          </motion.div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="h-full border-border/50 bg-card transition-shadow hover:shadow-lg">
                  <CardContent className="p-6">
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                      <feature.icon className="h-6 w-6" />
                    </div>
                    <h3 className="mb-2 font-semibold text-foreground">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          {/* CPA Diagram */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-16"
          >
            <Card className="overflow-hidden border-border/50">
              <CardContent className="p-8">
                <h3 className="mb-8 text-center text-xl font-semibold text-foreground">
                  Метод CPA в действии
                </h3>
                <div className="flex flex-col items-center justify-center gap-8 md:flex-row">
                  {[
                    { label: "Конкретное", desc: "Физические объекты", icon: "🎲" },
                    { label: "Наглядное", desc: "Картинки и схемы", icon: "📊" },
                    { label: "Абстрактное", desc: "Числа и символы", icon: "✨" },
                  ].map((step, i) => (
                    <div key={step.label} className="flex items-center gap-4">
                      <motion.div
                        initial={{ scale: 0 }}
                        whileInView={{ scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ delay: i * 0.2 }}
                        className="flex flex-col items-center"
                      >
                        <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-jade-dark text-2xl text-white shadow-lg">
                          {step.icon}
                        </div>
                        <span className="font-medium text-foreground">{step.label}</span>
                        <span className="text-sm text-muted-foreground">{step.desc}</span>
                      </motion.div>
                      {i < 2 && (
                        <ArrowRight className="hidden h-6 w-6 text-muted-foreground md:block" />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* Modes Section */}
      <section id="modes" className="px-4 py-16 md:py-24">
        <div className="mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-12 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold text-foreground md:text-4xl">
              Два режима обучения
            </h2>
            <p className="mx-auto max-w-2xl text-muted-foreground">
              Выберите подход, который подходит именно вам
            </p>
          </motion.div>

          <div className="grid gap-8 md:grid-cols-2">
            {modes.map((mode, index) => (
              <motion.div
                key={mode.title}
                initial={{ opacity: 0, x: index === 0 ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="h-full overflow-hidden border-border/50 transition-shadow hover:shadow-xl">
                  <div className={`h-2 bg-gradient-to-r ${mode.color}`} />
                  <CardContent className="p-8">
                    <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                      <mode.icon className="h-7 w-7" />
                    </div>
                    <h3 className="mb-2 text-xl font-bold text-foreground">{mode.title}</h3>
                    <p className="mb-6 text-muted-foreground">{mode.description}</p>
                    <ul className="space-y-3">
                      {mode.features.map((feature) => (
                        <li key={feature} className="flex items-center gap-3 text-sm text-foreground">
                          <CheckCircle2 className="h-5 w-5 text-primary" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 py-16 md:py-24">
        <div className="mx-auto max-w-4xl">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <Card className="overflow-hidden border-0 bg-gradient-to-br from-primary to-jade-dark shadow-2xl">
              <CardContent className="p-8 text-center md:p-12">
                <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl">
                  Готовы начать путь мастера?
                </h2>
                <p className="mx-auto mb-8 max-w-xl text-white/80">
                  Присоединяйтесь к тысячам учеников, которые уже улучшили свои 
                  математические навыки с Мастером Кватом.
                </p>
                <Link href="/signup">
                  <Button size="lg" variant="secondary" className="bg-white px-8 text-primary hover:bg-white/90">
                    Начать бесплатно
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/30 px-4 py-12">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-8 md:grid-cols-4">
            <div>
              <Link href="/" className="mb-4 flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Zap className="h-4 w-4" />
                </div>
                <span className="font-bold text-foreground">Мастер Кват</span>
              </Link>
              <p className="text-sm text-muted-foreground">
                Образовательная платформа для детей с геймификацией и китайскими методиками.
              </p>
            </div>
            <div>
              <h4 className="mb-4 font-semibold text-foreground">Продукт</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="#methodology" className="hover:text-foreground">Методика</Link></li>
                <li><Link href="#modes" className="hover:text-foreground">Режимы</Link></li>
                <li><Link href="/pricing" className="hover:text-foreground">Тарифы</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 font-semibold text-foreground">Компания</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="/about" className="hover:text-foreground">О нас</Link></li>
                <li><Link href="/contact" className="hover:text-foreground">Контакты</Link></li>
                <li><Link href="/blog" className="hover:text-foreground">Блог</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 font-semibold text-foreground">Поддержка</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="/help" className="hover:text-foreground">Помощь</Link></li>
                <li><Link href="/privacy" className="hover:text-foreground">Конфиденциальность</Link></li>
                <li><Link href="/terms" className="hover:text-foreground">Условия</Link></li>
              </ul>
            </div>
          </div>
          <div className="mt-8 border-t border-border pt-8 text-center text-sm text-muted-foreground">
            <p>&copy; 2026 Мастер Кват. Все права защищены.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
