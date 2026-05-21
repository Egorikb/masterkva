"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, User, Bot } from "lucide-react";
import { useChatStore } from "@/lib/chat-store";
import { useAuthStore } from "@/lib/auth-store";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { VoiceInput } from "./voice-input";
import { AchievementPopup } from "./achievement-popup";
import type { ChatMessage, ApiResponse } from "@/lib/types";

export function ChatInterface() {
  const [input, setInput] = useState("");
  const [showAchievement, setShowAchievement] = useState(false);
  const [achievementText, setAchievementText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const { 
    messages, 
    addMessage, 
    isLoading, 
    setIsLoading,
    mode,
    addQiEnergy,
    setCurrentVisualData
  } = useChatStore();

  // Also update auth store for persistent Qi tracking
  const { addQiEnergy: addAuthQiEnergy, isAuthenticated } = useAuthStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput("");
    setIsLoading(true);

    try {
      // Mock API response for demo - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Simulate different responses based on content
      const mockResponse: ApiResponse = generateMockResponse(content, mode);
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: mockResponse.text,
        audioUrl: mockResponse.audio_url,
        visualData: mockResponse.visual_data,
        timestamp: new Date(),
      };

      addMessage(assistantMessage);

      // Update visual data if present
      if (mockResponse.visual_data) {
        setCurrentVisualData(mockResponse.visual_data);
      }

      // Handle correct answer bonus
      if (mockResponse.is_correct && mockResponse.qi_bonus) {
        addQiEnergy(mockResponse.qi_bonus);
        // Also update auth store if user is logged in
        if (isAuthenticated) {
          addAuthQiEnergy(mockResponse.qi_bonus);
        }
        setAchievementText(`+${mockResponse.qi_bonus} Ци`);
        setShowAchievement(true);
        setTimeout(() => setShowAchievement(false), 2000);
      }

      // Play audio if available
      if (mockResponse.audio_url && audioRef.current) {
        audioRef.current.src = mockResponse.audio_url;
        audioRef.current.play().catch(() => {});
      }
    } catch (error) {
      console.error("[v0] Error sending message:", error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Простите, произошла ошибка. Попробуйте ещё раз.",
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, addMessage, setIsLoading, mode, addQiEnergy, setCurrentVisualData, isAuthenticated, addAuthQiEnergy]);

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
                  ? "Добро пожаловать в додзё!" 
                  : "Чем могу помочь?"}
              </h3>
              <p className="max-w-sm text-muted-foreground">
                {mode === "kungfu"
                  ? "Я научу тебя математике по методу Кунг-фу. Начни с простого вопроса!"
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
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Напиши свой вопрос..."
            className="min-h-[48px] max-h-[120px] resize-none rounded-xl"
            disabled={isLoading}
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
