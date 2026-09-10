"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useChatStore } from "@/lib/chat-store";
import { NumberBondViz } from "./visualizations/number-bond";
import { BarModelViz } from "./visualizations/bar-model";
import { TenFrameViz } from "./visualizations/ten-frame";
import { QuestionVisual } from "./visualizations/question-visual";
import { PandaSensei } from "./panda-sensei";

export function InteractiveBlackboard() {
  const { currentVisualData, isLoading, mode } = useChatStore();

  return (
    <div className="relative flex h-full flex-col overflow-hidden rounded-2xl bg-gradient-to-br from-jade-dark via-jade to-jade-light p-6 shadow-xl">
      {/* Blackboard texture overlay */}
      <div className="pointer-events-none absolute inset-0 opacity-10 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjZmZmIj48L3JlY3Q+CjxwYXRoIGQ9Ik0wIDBMNCA0Wk00IDBMMCA0WiIgc3Ryb2tlLXdpZHRoPSIwLjUiIHN0cm9rZT0iIzAwMCI+PC9wYXRoPgo8L3N2Zz4=')]" />

      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-bold text-white/90">
          Интерактивная доска
        </h2>
        <div className="flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-sm text-white/80">
          <span className="h-2 w-2 rounded-full bg-gold animate-pulse" />
          {isLoading ? "Обновление..." : "Готово"}
        </div>
      </div>

      {/* Main content area */}
      <div className="relative flex-1 overflow-hidden rounded-xl bg-white/5 backdrop-blur-sm">
        <AnimatePresence mode="wait">
          {currentVisualData ? (
            <motion.div
              key={JSON.stringify(currentVisualData)}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
              className="flex h-full items-center justify-center p-6"
            >
              {currentVisualData.type === "number_bond" && (
                <NumberBondViz data={currentVisualData} />
              )}
              {currentVisualData.type === "bar_model" && (
                <BarModelViz data={currentVisualData} />
              )}
              {currentVisualData.type === "ten_frame" && (
                <TenFrameViz data={currentVisualData} />
              )}
              {currentVisualData.type === "question" && (
                <QuestionVisual data={currentVisualData} />
              )}
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex h-full flex-col items-center justify-center p-6 text-center"
            >
              <motion.div
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-white/10"
              >
                <span className="text-5xl">📐</span>
              </motion.div>
              <h3 className="mb-2 text-xl font-semibold text-white/90">
                {mode === "kungfu" 
                  ? "Визуализации появятся здесь" 
                  : "Доска для объяснений"}
              </h3>
              <p className="max-w-sm text-white/60">
                Задай вопрос в чате, и я покажу тебе наглядное решение
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Zen loading animation */}
        <AnimatePresence>
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 flex items-center justify-center bg-jade-dark/50 backdrop-blur-sm"
            >
              <div className="flex flex-col items-center gap-4">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                  className="h-16 w-16 rounded-full border-4 border-white/20 border-t-gold"
                />
                <span className="text-lg font-medium text-white/80">
                  Мастер размышляет...
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Panda Sensei */}
      <PandaSensei />

      {/* Decorative chalk marks */}
      <div className="pointer-events-none absolute bottom-4 right-4 opacity-20">
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
          <path
            d="M10 70 Q 40 10 70 70"
            stroke="white"
            strokeWidth="2"
            strokeDasharray="4 4"
          />
          <circle cx="40" cy="20" r="8" stroke="white" strokeWidth="2" />
        </svg>
      </div>
    </div>
  );
}
