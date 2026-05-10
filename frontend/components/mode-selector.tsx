"use client";

import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Scroll } from "lucide-react";
import { useChatStore } from "@/lib/chat-store";
import type { LearningMode } from "@/lib/types";

const modes = [
  {
    id: "kungfu" as LearningMode,
    title: "Свитки Кунг-фу",
    icon: Scroll,
    description: "Глубокое изучение с китайской педагогикой (метод CPA)",
    gradient: "from-jade-dark to-jade",
  },
  {
    id: "homework" as LearningMode,
    title: "Помощь с ДЗ",
    icon: BookOpen,
    description: "Быстрые объяснения для домашних заданий по всем предметам",
    gradient: "from-gold to-gold-light",
  },
  {
    id: "review" as LearningMode,
    title: "📝 Повторение",
    icon: BookOpen,
    description: "Тесты и задания для закрепления знаний",
    gradient: "from-purple to-purple-light",
  },
];

export function ModeSelector() {
  const { mode, setMode } = useChatStore();

  return (
    <AnimatePresence>
      {!mode && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-sm"
        >
          <div className="w-full max-w-4xl px-6">
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="mb-12 text-center"
            >
              <h1 className="mb-4 text-5xl font-bold text-foreground">
                Мастер Кват
              </h1>
              <p className="text-xl text-muted-foreground">
                Выбери свой путь обучения, юный ученик
              </p>
            </motion.div>

            <div className="grid gap-6 md:grid-cols-2">
              {modes.map((modeOption, index) => (
                <motion.button
                  key={modeOption?.id || `mode-${index}`}
                  initial={{ y: 30, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.2 + index * 0.1 }}
                  whileHover={{ scale: 1.03, y: -4 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setMode(modeOption.id)}
                  className={`group relative overflow-hidden rounded-2xl bg-gradient-to-br ${modeOption.gradient} p-8 text-left shadow-xl transition-shadow hover:shadow-2xl`}
                >
                  {/* Glow effect */}
                  <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                  
                  {/* Animated border glow */}
                  <motion.div
                    className="absolute inset-0 rounded-2xl"
                    animate={{
                      boxShadow: [
                        "0 0 20px rgba(255,255,255,0.1)",
                        "0 0 40px rgba(255,255,255,0.2)",
                        "0 0 20px rgba(255,255,255,0.1)",
                      ],
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />

                  <div className="relative z-10">
                    <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
                      <modeOption.icon className="h-8 w-8 text-white" />
                    </div>
                    <h2 className="mb-2 text-2xl font-bold text-white">
                      {modeOption.title}
                    </h2>
                    <p className="text-white/80">{modeOption.description}</p>
                  </div>

                  {/* Decorative elements */}
                  <div className="absolute -bottom-4 -right-4 h-24 w-24 rounded-full bg-white/10 blur-xl" />
                  <div className="absolute -top-4 -left-4 h-16 w-16 rounded-full bg-white/10 blur-lg" />
                </motion.button>
              ))}
            </div>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-8 text-center text-sm text-muted-foreground"
            >
              Скажи &quot;Математика&quot; или &quot;Помощь&quot; для голосового выбора
            </motion.p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
