"use client";

import { motion } from "framer-motion";
import { Zap, Award, ArrowLeft } from "lucide-react";
import { useChatStore } from "@/lib/chat-store";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";

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

export function ProgressHeader() {
  const { progress, mode, setMode, clearMessages } = useChatStore();

  const handleBack = () => {
    setMode(null);
    clearMessages();
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-card/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        {/* Left: Back button and Logo */}
        <div className="flex items-center gap-4">
          {mode && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleBack}
              className="shrink-0"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
          )}
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <span className="text-lg font-bold">功</span>
            </div>
            <span className="hidden text-xl font-bold text-foreground sm:inline">
              Мастер Кват
            </span>
          </div>
        </div>

        {/* Center: Qi Energy Progress */}
        <div className="flex flex-1 max-w-xs items-center gap-3 px-4">
          <Zap className="h-5 w-5 shrink-0 text-gold" />
          <div className="flex-1">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">
                Энергия Ци
              </span>
              <span className="text-xs font-bold text-foreground">
                {progress.qiEnergy}/100
              </span>
            </div>
            <Progress 
              value={progress.qiEnergy} 
              className="h-2 [&>div]:bg-gold"
            />
          </div>
        </div>

        {/* Right: Belt Level */}
        <motion.div
          key={progress?.beltLevel}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className={`flex items-center gap-2 rounded-full border-2 px-4 py-1.5 ${beltColors[progress.beltLevel]}`}
        >
          <Award className="h-4 w-4" />
          <span className="text-sm font-semibold">
            {beltNames[progress.beltLevel]}
          </span>
        </motion.div>
      </div>
    </header>
  );
}
