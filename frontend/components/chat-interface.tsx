"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, User, Bot } from "lucide-react";
import { VoiceInput } from "./voice-input";
import { AchievementPopup } from "./achievement-popup";
import { useChatStore } from "@/lib/chat-store";
import type { ChatMessage } from "@/lib/types";

// Conversation flow states (State Machine v2.0)
type FlowState = "greeting" | "name" | "grade" | "goal" | "diagnostic" | "teaching" | "topic";

// SYSTEM PROMPT v2.0
const SYSTEM_PROMPT = `Ты — Мастер Кват, мудрая Панда, наставник по математике 🐼

CPA МЕТОД (обязателен):
- Конкретное: предметы, фрукты, яблоки
- Образное: картинки, схемы  
- Абстрактное: цифры, формулы

Тон: мудрый, терпеливый.

ОБУЧЕНИЕ (НОВАЯ ЛОГИКА):
- Показывай страницу учебника (картинку)
- 3 верных ПОДРЯД → след. страница
- 2 ошибки → сначала этой страницы (Grade)
- Каждая тема = новая страница учебника. Используй метафоры: "свитки знаний", "энергия Ци".
Язык: строго русский. Стиль: короткие сообщения. Максимум 1 предложение. Используй простые слова.
ВСЕГДА давай следующий пример ПОСЛЕ подтверждения ответа. Не останавливай диалог. Всегда продолжай объяснение сам, не жди ответа ребёнка.Максимум 1 предложение. Используй простые слова..

Темы: Numbers 1-10, Numbers 11-20, Geometry, Addition, Subtraction, CPA Method, Time/Clock, Position, Review

СТЕЙТ МАШИНА:
Этап А - Привет → Имя → Класс → Выбор: Курс или Тема
Этап Б - Диагностика: 2 ошибки = точка старта
Этап В - Обучение: с первого параграфа уровня
Этап Г - Конкретная тема: сначала
Этап Д - Повторный визит

В диагностике (Этап Б):
- Начинай с "Повторение" (тема 9), класс 1
- 2 ошибки подряд = точка старта (остановись)
- НЕ предлагай 4 варианта выбора

АНАЛИТИКА: После каждого ответа ученика записывай в консоль JSON:
{ "current_level": "grade X", "strong_topics": [...], "weak_spots": [...], "session_goal": "diagnostic|learning", "recommendation": "..." }`;

const getVisualUrl = (grade: number, topic: string) => {
  const topicMap: Record<string, string> = {
    "addition": "094",
    "subtraction": "095",
    "multiplication": "096",
    "division": "097",
    "geometry": "034",
    "numbers": "019",
  };
  const page = topicMap[topic] || "094";
  return `/images/${grade}/${page}`;
};

// Diagonstic questions by topic
const DIAGNOSTIC_QUESTIONS = {
  // Grade 1: Сложение и вычитание
  1: [
    { q: "Сколько будет 3 + 2?", a: "5" },
    { q: "Сколько будет 7 - 4?", a: "3" },
    { q: "Сколько будет 5 + 3?", a: "8" },
    // Additional (after error)
    { q: "Сколько будет 6 + 2?", a: "8" },
    { q: "Сколько будет 9 - 5?", a: "4" },
  ],
  // Grade 2: Умножение
  2: [
    { q: "Сколько будет 2 × 3?", a: "6" },
    { q: "Сколько будет 4 × 2?", a: "8" },
    { q: "Сколько будет 3 × 3?", a: "9" },
    { q: "Сколько будет 5 × 2?", a: "10" },
    { q: "Сколько будет 6 × 2?", a: "12" },
  ],
  // Grade 3: Деление
  3: [
    { q: "Сколько будет 6 ÷ 2?", a: "3" },
    { q: "Сколько будет 8 ÷ 4?", a: "2" },
    { q: "Сколько будет 9 ÷ 3?", a: "3" },
    { q: "Сколько будет 10 ÷ 2?", a: "5" },
    { q: "Сколько будет 12 ÷ 3?", a: "4" },
  ],
  // Grade 4: Многозначные
  4: [
    { q: "Сколько будет 23 + 17?", a: "40" },
    { q: "Сколько будет 45 - 28?", a: "17" },
    { q: "Сколько будет 12 × 4?", a: "48" },
    { q: "Сколько будет 56 ÷ 7?", a: "8" },
    { q: "Сколько будет 15 + 25?", a: "40" },
  ],
  // Grade 5: Дроби и проценты
  5: [
    { q: "Сколько будет 1/2 + 1/4?", a: "3/4" },
    { q: "Сколько будет 25% от 100?", a: "25" },
    { q: "Сколько будет 0.5 + 0.3?", a: "0.8" },
    { q: "Сколько будет 50% от 200?", a: "100" },
    { q: "Сколько будет 3/4 - 1/4?", a: "1/2" },
  ],
  // Grade 6: Проценты и уравнения
  6: [
    { q: "Сколько будет 10% от 150?", a: "15" },
    { q: "Сколько будет 20% от 250?", a: "50" },
    { q: "Чему равен x: x + 5 = 12?", a: "7" },
    { q: "Чему равен x: x × 3 = 18?", a: "6" },
    { q: "Сколько будет 30% от 100?", a: "30" },
  ],
};

export function ChatInterface() {
  const [input, setInput] = useState("");
  const [showAchievement, setShowAchievement] = useState(false);
  const [achievementText, setAchievementText] = useState("");
  
  // State Machine State
  const [flowState, setFlowState] = useState<FlowState>("greeting");
  const [studentName, setStudentName] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("studentName") || "";
    }
    return "";
  });
  const [studentGrade, setStudentGrade] = useState<number | null>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("studentGrade");
      return saved ? parseInt(saved) : null;
    }
    return null;
  });
  const [selectedGoal, setSelectedGoal] = useState<"course" | "topic" | null>(null);
  
  // Diagnostic state
  const [diagnosticErrors, setDiagnosticErrors] = useState(0);
  const [diagnosticGrade, setDiagnosticGrade] = useState(1);
  const [diagnosticQuestion, setDiagnosticQuestion] = useState(0);
  const [attemptMode, setAttemptMode] = useState<"normal" | "extra">("normal");

  // Analytics for parent report
  const [strongTopics, setStrongTopics] = useState<string[]>([]);
  const [weakSpots, setWeakSpots] = useState<string[]>([]);

  // Auto-focus input on load
  useEffect(() => {
    const timer = setTimeout(() => inputRef.current?.focus(), 100);
    return () => clearTimeout(timer);
  }, [])
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const welcomeShownRef = useRef(false);
  
  const { 
    messages, 
    addMessage, 
    isLoading, 
    setIsLoading,
    mode,
    addQiEnergy,
    setCurrentVisualData
  } = useChatStore();
  
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Этап А: Первое знакомство - Приветствие
  useEffect(() => {
    if (!welcomeShownRef.current && messages.length === 0) {
      const welcomeMsg = studentName 
        ? `Привет, ${studentName}! Рад твоему возвращению в наш зал. 🥋\n\nПродолжим с того места в свитке, где остановились?`
        : "Привет, мой юный друг! Я твой наставник Панда. 🐼\n\nКак мне называть тебя в нашем зале математических искусств?";
      addMessage({
        id: "welcome",
        role: "assistant",
        content: welcomeMsg,
        timestamp: new Date(),
      });
      welcomeShownRef.current = true;
      setFlowState(studentName ? "goal" : "name");
    }
  }, [messages.length, addMessage, studentName]);

  // Call Backend (Python) via localhost:8001
  const callBackend = async (userMessage: string): Promise<string> => {
    // Get or create user_id from localStorage (сохраняем навсегда)
    let userId = localStorage.getItem('user_email');
    if (!userId) {
      // Новый пользователь - создаём уникальный ID
      userId = `guest_${Date.now()}_${Math.random().toString(36).slice(2,9)}`;
      localStorage.setItem('user_email', userId);
    }

    // Также читаем name и grade если есть
    const savedName = localStorage.getItem('studentName') || null;
    const savedGrade = localStorage.getItem('studentGrade') || null;

    const response = await fetch("http://localhost:8001/api/v1/plugins/panda/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        user_id: userId,
        message: userMessage,
        name: savedName,
        grade: savedGrade ? parseInt(savedGrade) : null
      })
    });

    if (!response.ok) {
      console.error("Backend error:", response.status);
      return "Извини, произошла ошибка связи с наставником. Попробуй ещё раз!";
    }

    const data = await response.json();
    if (data.text) {
      // Парсим [VISUAL] тег из ответа
      const visualMatch = data.text.match(/\[VISUAL\](.*?)\[\/VISUAL\]/s);
      if (visualMatch) {
        try {
          const visualData = JSON.parse(visualMatch[1]);
          
          // CPA компонент - приоритет!
          if (visualData.type === "cpa_component") {
            console.log("[CPA] Component:", visualData.component);
            localStorage.setItem("cpa_component", JSON.stringify(visualData));
            localStorage.setItem("currentVisualData", visualData.fallback_image || "");
            setCurrentVisualData(null);
          } else {
            // Fallback - страница учебника
            const newUrl = `/api/images/${visualData.grade}/${visualData.page}`;
            console.log("[VISUAL] Updating blackboard:", newUrl);
            localStorage.setItem("blackboard_grade", String(visualData.grade));
            localStorage.setItem("blackboard_topic", visualData.page);
            localStorage.setItem("currentVisualData", newUrl);
            setCurrentVisualData(null);
          }
        } catch (e) {
          console.error("[VISUAL] Parse error:", e);
        }
      }
      return data.text;
    }
    return "Извини, произошла ошибка. Попробуй ещё раз!";
  };

  // Handle diagnostic check
  const checkDiagnosticAnswer = (answer: string): boolean => {
    const questions = DIAGNOSTIC_QUESTIONS[diagnosticGrade as keyof typeof DIAGNOSTIC_QUESTIONS];
    const q = questions[diagnosticQuestion];
    return q && (answer.trim() === q.a || answer.trim().includes(q.a));
  };

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) {
      setInput("");
      return;
    }

    // State Machine Logic
    const typos: Record<string, string> = {
      "lfdfq": "давай",
      "lfdf": "да",
      "ghbdtn": "привет",
      "vtyz": "ты",
      "pkden": "иди",
      "tujh": "егор",
      "lfdeg": "егор",
    };
    let userInput = content.trim();
    // Replace × with * and \ with x for math
    userInput = userInput.replace(/×/g, "*").replace(/\\/g, "x");
    // Auto-correct typos
    Object.keys(typos).forEach(key => {
      if (userInput.toLowerCase().includes(key)) {
        userInput = typos[key];
      }
    });
    
    // Этап А - Получение имени (с валидацией)
    if (flowState === "name") {
      // Блокируем приветствия
      const greetings = ["привет","ghbdtn","hi","hello","hey","хай","прив","123"];
      if (greetings.includes(userInput.toLowerCase())) {
        addMessage({
          id: Date.now().toString(),
          role: "user",
          content: userInput,
          timestamp: new Date(),
        });
        addMessage({
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Это приветствие, а не имя! 🐼 Как тебя звать? Напиши своё имя!",
          timestamp: new Date(),
        });
        setInput("");
          return;
      }
      setStudentName(userInput.trim());
          const cappedName = userInput.trim().charAt(0).toUpperCase() + userInput.trim().slice(1);
      localStorage.setItem("studentName", cappedName);
      addMessage({
        id: Date.now().toString(),
        role: "user",
        content: userInput,
        timestamp: new Date(),
      });
      addMessage({
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Отлично, ${cappedName}! 🐼\n\nВ каком классе ты оттачиваешь свое мастерство в школе?`,
        timestamp: new Date(),
      });
      setFlowState("grade");
      setInput("");
      setInput("");
          return;
    }
    
    // Этап А - Получение класса
    if (flowState === "grade") {
      const grade = parseInt(userInput.replace(/класс/gi, "").trim());
      if (!isNaN(grade) && grade >= 1 && grade <= 6) {
        setStudentGrade(grade);
        localStorage.setItem("studentGrade", grade.toString());
        addMessage({
          id: Date.now().toString(),
          role: "user",
          content: userInput,
          timestamp: new Date(),
        });
        addMessage({
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `Отлично! Ты учишься в ${grade} классе. 🐼\n\nМы начнём полный Путь Мастера (курс) или тебе нужно укрепить конкретную тему сегодня?`,
          timestamp: new Date(),
        });
        setFlowState("goal");
        setInput("");
          return;
      }
    }
    
    // Этап А - Выбор курса или темы
    if (flowState === "goal") {
      const isCourse = userInput.toLowerCase().includes("курс") || 
                      userInput.toLowerCase().includes("путь") ||
                      userInput.toLowerCase().includes("полн");
      const isTopic = userInput.toLowerCase().includes("конкрет") ||
                      userInput.toLowerCase().includes("тему") ||
                      userInput.toLowerCase().includes("одну");
      
      if (isCourse || isTopic) {
        addMessage({
          id: Date.now().toString(),
          role: "user",
          content: userInput,
          timestamp: new Date(),
        });
        setSelectedGoal(isCourse ? "course" : "topic");
        
        if (isCourse) {
          // Начинаем диагностику (Этап Б)
          addMessage({
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `Чтобы подобрать правильный свиток, я проверю твой текущий уровень. Не бойся ошибок — это часть пути! 🐼\n\nНачнём с первого задания:\n\n![image](${getVisualUrl(1, "numbers")})\n\n${DIAGNOSTIC_QUESTIONS[1]?.[0]?.q || "Сколько будет 3 + 2?"}`,
            timestamp: new Date(),
          });
          setInput("");
        setFlowState("diagnostic");
          setDiagnosticQuestion(0);
          setDiagnosticErrors(0);
          console.log("DEBUG: Setting visual to", getVisualUrl(1, "numbers"));
          setCurrentVisualData(getVisualUrl(1, "numbers"));
            localStorage.setItem("currentVisualData", getVisualUrl(1, "numbers"));
          setInput("");
          return;
          setInput("");
          return;
        } else {
          // Конкретная тема (Этап Г)
          addMessage({
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `Какую тему хочешь укрепить? Например: сложение, вычитание, дроби, геометрия...`,
            timestamp: new Date(),
          });
          setFlowState("topic");
          setInput("");
          return;
        }
      }
    }
    
    // Этап Б - Диагностика (новая логика: 3 правильных = +1 Grade, ошибка = 2 доп. попытки)
    if (flowState === "diagnostic") {
      const gradeQuestions = DIAGNOSTIC_QUESTIONS[diagnosticGrade as keyof typeof DIAGNOSTIC_QUESTIONS] || [];
      const isCorrect = checkDiagnosticAnswer(userInput);
      
      addMessage({
        id: Date.now().toString(),
        role: "user",
        content: userInput,
        timestamp: new Date(),
      });
      
      if (isCorrect) {
        if (attemptMode === "extra") {
          // Дополнительные примеры - ВЕРНО! Переходим на след. уровень
          const nextGrade = Math.min(diagnosticGrade + 1, 6);
          if (nextGrade >= 6) {
            // Достигли максимума
            addMessage({
              id: (Date.now() + 1).toString(),
              role: "assistant",
              content: `Великолепно! 🐼 Ты прошёл все уровни!\n\nТвой уровень — 6 класс!\n\nНачинаем обучение!`,
              timestamp: new Date(),
            });
            setStudentGrade(6);
            setInput("");
        setFlowState("teaching");
            setInput("");
            setInput("");
          return;
          }
          addMessage({
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `Верно! 🐼 Переходим к ${nextGrade} классу!\n\n${DIAGNOSTIC_QUESTIONS[nextGrade as keyof typeof DIAGNOSTIC_QUESTIONS]?.[0]?.q || ""}`,
            timestamp: new Date(),
          });
          setDiagnosticGrade(nextGrade);
          setCurrentVisualData(getVisualUrl(nextGrade, "numbers"));
          setDiagnosticQuestion(0);
          setAttemptMode("normal");
          setInput("");
          setInput("");
          return;
        }
        
        // Обычный режим - следующий вопрос
        const nextQ = diagnosticQuestion + 1;
        if (nextQ < 3) {
          // Ещё есть вопросы этого уровня
          addMessage({
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: "addMessage({...\n\n" + gradeQuestions[nextQ]?.q,
            timestamp: new Date(),
          });
          setDiagnosticQuestion(nextQ);
        } else {
          // 3 верных ответа - переходим на следующий уровень
          const nextGrade = Math.min(diagnosticGrade + 1, 6);
          if (nextGrade >= 6) {
            addMessage({
              id: (Date.now() + 1).toString(),
              role: "assistant",
              content: `Великолепно! 🐼 Ты прошёл все уровни!\n\nТвой уровень — 6 класс!\n\nНачинаем обучение!`,
              timestamp: new Date(),
            });
            setStudentGrade(6);
            setInput("");
        setFlowState("teaching");
            setInput("");
            setInput("");
          return;
          }
          addMessage({
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `Отлично! 🐼 Переходим к ${nextGrade} классу!\n\n${DIAGNOSTIC_QUESTIONS[nextGrade as keyof typeof DIAGNOSTIC_QUESTIONS]?.[0]?.q}`,
            timestamp: new Date(),
          });
          setDiagnosticGrade(nextGrade);
          setCurrentVisualData(getVisualUrl(nextGrade, "numbers"));
          setDiagnosticQuestion(0);
        }
      } else {
        // Ошибка!
        if (attemptMode === "normal") {
          // Даём 2 дополнительных примера
          addMessage({
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: "Ты уверен в своём расчёте? Попробуй направить свою Ци ещё раз! 🐼\n\n" + gradeQuestions[3]?.q,
            timestamp: new Date(),
          });
          setAttemptMode("extra");
          setDiagnosticQuestion(3);
        } else {
          // Второй дополнительный пример тоже неверный - ТОЧКА СТАРТА
          addMessage({
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `Хорошая попытка! 🐼 Это твоя точка старта.\n\nТвой уровень — ${diagnosticGrade} класс.\n\nНачинаем обучение с этого места!`,
            timestamp: new Date(),
          });
          setStudentGrade(diagnosticGrade);
          setInput("");
        setFlowState("teaching");
          setInput("");
          setInput("");
          return;
        }
      }
      setInput("");
          return;
    }
    
    // Этап Г - Конкретная тема
    if (flowState === "topic") {
      addMessage({
        id: Date.now().toString(),
        role: "user",
        content: userInput,
        timestamp: new Date(),
      });
      addMessage({
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Отлично! Найду материал по "${userInput}" и начну с самого начала. 🐼\n\nДавай разберём эту тему вместе!`,
        timestamp: new Date(),
      });
      setInput("");
        setFlowState("teaching");
      setInput("");
          return;
    }
    
    // По умолчанию - используем DeepSeek
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: userInput,
      timestamp: new Date(),
    };
    addMessage(userMessage);
    setIsLoading(true);
    setInput("");

    try {
      const raw = await callBackend(userInput);
      const responseContent = raw.replace(/\*\*/g, "").replace(/\*/g, "");
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: responseContent,
        timestamp: new Date(),
      };
      
      addMessage(assistantMessage);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 2).toString(),
        role: "assistant",
        content: "Ошибка! Попробуй ещё раз.",
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, addMessage, setIsLoading, messages, flowState, studentName, studentGrade, diagnosticQuestion, diagnosticErrors]);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <AchievementPopup 
        show={showAchievement} 
        text={achievementText} 
        onClose={() => setShowAchievement(false)} 
      />
      
      <div className="flex-1 overflow-y-auto p-4">
        <>
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
                Welcome to Math Master!
              </h3>
              <p className="max-w-sm text-muted-foreground">
                Ask me anything!
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
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                  message.role === "user" 
                    ? "bg-secondary text-secondary-foreground" 
                    : "bg-primary text-primary-foreground"
                }`}>
                  {message.role === "user" 
                    ? <User className="h-4 w-4" /> 
                    : <Bot className="h-4 w-4" />
                  }
                </div>
                <div className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                  message.role === "user"
                    ? "bg-secondary text-secondary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}>
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  <div className="mt-1 text-xs opacity-50">
                    {message.timestamp?.toLocaleTimeString()}
                  </div>
                </div>
              </motion.div>
            ))
          )}
          <div ref={messagesEndRef} />
        </>
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <form 
          onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
          className="flex gap-2"
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") sendMessage(input); }}
            placeholder="Напиши сообщение..."
            className="flex-1 rounded-full border bg-background px-4 py-2"
            disabled={isLoading}
          />
          <button 
            type="submit"
            disabled={isLoading || !input.trim()}
            className="rounded-full bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
