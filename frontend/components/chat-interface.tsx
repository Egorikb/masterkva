"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, User, Bot } from "lucide-react";
import { useChatStore } from "@/lib/chat-store";
import { useAuthStore } from "@/lib/auth-store";
import { postPandaChat } from "@/lib/api/panda-client";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { VoiceInput } from "./voice-input";
import { AchievementPopup } from "./achievement-popup";
import type { ChatMessage, ApiResponse, QuestionVisualSection } from "@/lib/types";
import type { PandaChatResponse } from "@/contracts/panda";

export function ChatInterface() {
  const [input, setInput] = useState("");
  const [showAchievement, setShowAchievement] = useState(false);
  const [achievementText, setAchievementText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const initialTurnStartedRef = useRef<"kungfu" | "homework" | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const { 
    messages, 
    addMessage, 
    isLoading, 
    setIsLoading,
    mode,
    addQiEnergy,
    setCurrentVisualData,
    clearMessages,
  } = useChatStore();

  const { user, studentProfile, addQiEnergy: addAuthQiEnergy, updateStudentProfile } = useAuthStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    textareaRef.current?.focus();
  }, [messages.length, isLoading, mode]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    const trimmed = content.trim();
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput("");
    setIsLoading(true);

    try {
      const profile = studentProfile;
      const grade = profile?.lastSessionGrade ?? profile?.currentGrade ?? null;
      const response: PandaChatResponse = await postPandaChat({
        user_id: user?.id ?? profile?.userId ?? "anonymous-student",
        message: trimmed,
        name: user?.name ?? null,
        grade,
        mode,
      });

      const visualData = normalizePandaVisual(response.visual, response.text);
      const assistantChunks = response.text
        .split(/\n\s*\n/)
        .map((chunk) => chunk.trim())
        .filter(Boolean);
      const chunks = assistantChunks.length ? assistantChunks : [response.text.trim()];

      chunks.forEach((chunk, index) => {
        const assistantMessage: ChatMessage = {
          id: `${Date.now()}-${index + 1}`,
          role: "assistant",
          content: chunk,
          audioUrl: undefined,
          visualData: index === chunks.length - 1 ? visualData : undefined,
          timestamp: new Date(),
        };
        addMessage(assistantMessage);
      });

      if (visualData) {
        setCurrentVisualData(visualData);
      }

      const state = response.state;
      if (state?.actual_grade && profile && !profile.lastSessionGrade) {
        updateStudentProfile({ lastSessionGrade: state.actual_grade });
      }

      if (state?.weak_topic) {
        updateStudentProfile({
          weakTopics: Array.from(new Set([...(profile?.weakTopics ?? []), state.weak_topic.topic])),
          lastSessionGrade: state.actual_grade ?? profile?.lastSessionGrade,
        });
      }

      if (state?.report?.practice_result === "success") {
        addQiEnergy(5);
        addAuthQiEnergy(5);
      }
    } catch (error) {
      console.error("[chat] Error sending message:", error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Не удалось связаться с учителем. Проверь, запущен ли backend на 8001.",
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, addMessage, setIsLoading, setCurrentVisualData, user, studentProfile, updateStudentProfile, addQiEnergy, addAuthQiEnergy, mode]);

  useEffect(() => {
    if (!mode) {
      initialTurnStartedRef.current = null;
      return;
    }

    if (messages.length > 0 || isLoading) return;
    if (initialTurnStartedRef.current === mode) return;

    initialTurnStartedRef.current = mode;
    void sendMessage(mode === "kungfu" ? "диагностика" : "начни урок с вопроса");
  }, [mode, messages.length, isLoading, sendMessage]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const normalizePandaVisual = (visual: any, text: string): ChatMessage["visualData"] => {
    const extractCountingFromText = (sourceText: string) => {
      const lower = sourceText.toLowerCase();
      const numbers = Array.from(sourceText.matchAll(/\d+/g), (match) => Number(match[0]));
      if (numbers.length < 2) return undefined;
      if (!/(кружк|круг|шар|яблок|предмет|точк)/i.test(lower)) return undefined;

      const colors: string[] = [];
      if (/красн/i.test(lower)) colors.push("red");
      if (/син/i.test(lower)) colors.push("blue");
      if (/зелён|зелен/i.test(lower)) colors.push("emerald");
      if (/желт/i.test(lower)) colors.push("gold");
      if (/фиолет/i.test(lower)) colors.push("purple");

      return {
        type: "question" as const,
        title: "Счёт предметов",
        prompt: sourceText,
        cpaVisual: "counting" as const,
        objects: "кружки",
        parts: numbers.slice(0, 2),
        colors: colors.length ? colors.slice(0, 2) : undefined,
      };
    };

    if (!visual || typeof visual !== "object") {
      return extractCountingFromText(text);
    }

    if (visual.type === "number_bond" && typeof visual.total === "number" && Array.isArray(visual.parts)) {
      const promptText = text || (typeof visual.prompt === "string" ? visual.prompt : "");
      const promptLower = promptText.toLowerCase();
      const operation = /[-−]|выч|убер|остал|минус|отня/i.test(promptLower) ? "subtract" : "add";
      return {
        type: "number_bond",
        total: visual.total,
        parts: visual.parts,
        prompt: promptText,
        title: typeof visual.title === "string" ? visual.title : undefined,
        operation,
      };
    }
    if (visual.type === "bar_model" && typeof visual.total === "number" && Array.isArray(visual.segments)) {
      return {
        type: "bar_model",
        total: visual.total,
        segments: visual.segments,
      };
    }
    if (visual.type === "ten_frame" && typeof visual.filled === "number") {
      return {
        type: "ten_frame",
        filled: visual.filled,
        total: typeof visual.total === "number" ? visual.total : undefined,
      };
    }
    if (visual.type === "question" && typeof visual.prompt === "string") {
      return {
        type: "question",
        title: typeof visual.title === "string" ? visual.title : "Задание",
        prompt: visual.prompt,
        cpaVisual: typeof visual.cpaVisual === "string" ? visual.cpaVisual : "unknown",
        objects: typeof visual.objects === "string" ? visual.objects : undefined,
        parts: Array.isArray(visual.parts) ? visual.parts.filter((value: unknown): value is number => typeof value === "number") : undefined,
        colors: Array.isArray(visual.colors) ? visual.colors.filter((value: unknown): value is string => typeof value === "string") : undefined,
        answer: typeof visual.answer === "string" ? visual.answer : undefined,
        topic: typeof visual.topic === "string" ? visual.topic : undefined,
        templateType: typeof visual.templateType === "string" ? visual.templateType : undefined,
        templateFamily: typeof visual.templateFamily === "string" ? visual.templateFamily : undefined,
        templateLabel: typeof visual.templateLabel === "string" ? visual.templateLabel : undefined,
        templateStage: typeof visual.templateStage === "string" ? visual.templateStage : undefined,
        templateGlyph: typeof visual.templateGlyph === "string" ? visual.templateGlyph : undefined,
        templateSections: Array.isArray(visual.templateSections)
          ? visual.templateSections
              .map((section: QuestionVisualSection) => ({
                label: typeof section?.label === "string" ? section.label : "",
                kind: section?.kind === "concrete" || section?.kind === "pictorial" || section?.kind === "abstract"
                  ? section.kind
                  : "pictorial",
                bullets: Array.isArray(section?.bullets)
                  ? section.bullets.filter((value: unknown): value is string => typeof value === "string")
                  : [],
              }))
              .filter((section: QuestionVisualSection) => section.label && section.bullets.length > 0)
          : undefined,
        templateHide: typeof visual.templateHide === "string" ? visual.templateHide : undefined,
        templateWhy: typeof visual.templateWhy === "string" ? visual.templateWhy : undefined,
        templateNotes: typeof visual.templateNotes === "string" ? visual.templateNotes : undefined,
        templatePreview: visual.templatePreview && typeof visual.templatePreview === "object" ? visual.templatePreview : undefined,
        templateReason: typeof visual.templateReason === "string" ? visual.templateReason : undefined,
        templateSkills: Array.isArray(visual.templateSkills)
          ? visual.templateSkills.filter((value: unknown): value is string => typeof value === "string")
          : undefined,
      };
    }

    return extractCountingFromText(text);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4">
        <AnimatePresence initial={false}>
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex h-full flex-col items-center justify-center text-center"
            >
              <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
                <Bot className="h-10 w-10 text-primary" />
              </div>
              <h3 className="mb-2 text-xl font-semibold text-foreground">
                {mode === "kungfu" 
                  ? "Добро пожаловать в кабинет учителя!" 
                  : "Чем могу помочь?"}
              </h3>
              <p className="max-w-sm text-muted-foreground">
                {mode === "kungfu"
                  ? "Задай вопрос или напиши 'диагностика' — учитель ответит по нашим материалам 1–9 класса."
                  : "Задай вопрос по любому предмету, и я помогу тебе разобраться."}
              </p>
            </motion.div>
          ) : (
            messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`mb-4 flex gap-3 ${
                  message.role === "user" ? "flex-row-reverse" : ""
                }`}
              >
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
                    message.role === "user"
                      ? "bg-secondary text-secondary-foreground"
                      : "bg-primary text-primary-foreground"
                  }`}
                >
                  {message.role === "user" ? (
                    <User className="h-5 w-5" />
                  ) : (
                    <Bot className="h-5 w-5" />
                  )}
                </div>
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-card border border-border text-card-foreground shadow-sm"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>

        {/* Loading state */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-4 flex gap-3"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
              <Bot className="h-5 w-5" />
            </div>
            <div className="flex items-center gap-2 rounded-2xl border border-border bg-card px-4 py-3 shadow-sm">
              <motion.span
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="text-muted-foreground"
              >
                Мастер размышляет...
              </motion.span>
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="h-2 w-2 rounded-full bg-primary"
                    animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                    transition={{
                      duration: 0.8,
                      repeat: Infinity,
                      delay: i * 0.2,
                    }}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-border bg-card p-4">
        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <VoiceInput onTranscript={(text) => sendMessage(text)} />
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Напиши свой вопрос..."
            className="min-h-[48px] max-h-[120px] resize-none rounded-xl"
            autoFocus
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || isLoading}
            className="h-12 w-12 shrink-0 rounded-xl"
          >
            <Send className="h-5 w-5" />
          </Button>
        </form>
      </div>

      {/* Hidden audio element for TTS */}
      <audio ref={audioRef} className="hidden" />

      {/* Achievement popup */}
      <AchievementPopup show={showAchievement} text={achievementText} />
    </div>
  );
}

// Mock response generator for demo purposes
function generateMockResponse(content: string, mode: string | null): ApiResponse {
  const lowerContent = content.toLowerCase();
  
  // Check for math-related content
  if (lowerContent.includes("5+3") || lowerContent.includes("5 + 3")) {
    return {
      text: "Отлично! Давай разберём 5 + 3 с помощью связей чисел.\n\nПосмотри на доску — я показал тебе связь между числами. Мы видим, что 5 и 3 вместе дают нам 8.\n\nПредставь, что у тебя 5 яблок в одной руке и 3 в другой. Сколько всего? Правильно, 8! 🎉",
      visual_data: {
        type: "number_bond",
        total: 8,
        parts: [5, 3],
      },
      is_correct: true,
      qi_bonus: 10,
    };
  }
  
  if (lowerContent.includes("7+6") || lowerContent.includes("7 + 6")) {
    return {
      text: "Хороший вопрос! Давай используем метод десятки.\n\n7 + 6 — это немного сложнее. Посмотри на десятичную рамку на доске.\n\nМы можем разложить 6 на 3 + 3:\n• 7 + 3 = 10 (заполняем рамку)\n• 10 + 3 = 13\n\nОтвет: 13! Ты молодец! 🥋",
      visual_data: {
        type: "ten_frame",
        filled: 13,
        total: 20,
      },
      is_correct: true,
      qi_bonus: 15,
    };
  }
  
  if (lowerContent.includes("дроб") || lowerContent.includes("fraction")) {
    return {
      text: "Дроби — это части целого! Посмотри на столбиковую модель на доске.\n\nПредставь пиццу, разрезанную на равные части:\n• 1/2 — это половина пиццы\n• 1/4 — это четверть\n\nНа модели видно, как целое делится на части. Какую дробь ты хочешь изучить?",
      visual_data: {
        type: "bar_model",
        total: 1,
        segments: [
          { value: 0.5, label: "1/2", color: "jade" },
          { value: 0.25, label: "1/4", color: "gold" },
          { value: 0.25, label: "1/4", color: "gold" },
        ],
      },
    };
  }
  
  // Default response
  if (mode === "kungfu") {
    return {
      text: "Интересный вопрос, юный ученик! 🥋\n\nВ методе Кунг-фу мы учимся через понимание, а не зубрёжку. Расскажи мне подробнее — какую математическую задачу ты хочешь решить?\n\nНапример:\n• Сложение и вычитание\n• Умножение и деление\n• Дроби\n• Задачи со словами",
    };
  }
  
  return {
    text: "Хороший вопрос! Давай разберёмся вместе.\n\nЧтобы я мог лучше помочь, уточни:\n• По какому предмету задание?\n• Что именно непонятно?\n\nНе стесняйся спрашивать — вместе мы всё решим! 📚",
  };
}
