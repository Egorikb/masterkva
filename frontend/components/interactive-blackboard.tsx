"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useChatStore } from "@/lib/chat-store";
import { useState, useEffect } from "react";

// CPA Components
import { TenFrameViz } from "./visualizations/ten-frame";
import { BarModelViz } from "./visualizations/bar-model";
import { NumberBondViz } from "./visualizations/number-bond";

interface CPAData {
  type: string;
  component: string;
  data: any;
  fallback_image?: string;
}

const API_BASE = "http://localhost:3000";

export function InteractiveBlackboard() {
  const { currentVisualData, isLoading, mode } = useChatStore();
  const [grade, setGrade] = useState(1);
  const [topic, setTopic] = useState(6);
  const [imageUrl, setImageUrl] = useState("");
  const [loadingImg, setLoadingImg] = useState(false);
  
  // CPA Component State
  const [cpaData, setCpaData] = useState<CPAData | null>(null);

  // Load saved image on mount
  useEffect(() => {
    const saved = localStorage.getItem("currentVisualData");
    const savedGrade = localStorage.getItem("blackboard_grade");
    const savedTopic = localStorage.getItem("blackboard_topic");
    const cpaStr = localStorage.getItem("cpa_component");
    
    if (savedGrade) setGrade(parseInt(savedGrade));
    if (savedTopic) setTopic(parseInt(savedTopic));
    if (saved) setImageUrl(saved);
    if (cpaStr) {
      try {
        setCpaData(JSON.parse(cpaStr));
      } catch(e) { console.error("CPA parse error:", e); }
    }
  }, []);

  // Update image when visual changes
  useEffect(() => { 
    console.log("DEBUG Blackboard: currentVisualData =", currentVisualData);
    if (currentVisualData) { setImageUrl(currentVisualData); } else { loadImage(); } 
  }, [currentVisualData]);

  // Load image when topic/grade changes or in review mode
  useEffect(() => {
    if (mode === "review") {
      loadImage();
    }
  }, [grade, topic, mode]);

  const loadImage = async () => {
    setLoadingImg(true);
    try {
      const res = await fetch(`${API_BASE}/api/images/${grade}/${topic}`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        setImageUrl(url);
      }
    } catch (e) {
      console.error("Failed to load image:", e);
    }
    setLoadingImg(false);
  };

  return (
    <div className="relative flex h-full flex-col overflow-hidden rounded-2xl bg-gradient-to-br from-jade-dark via-jade to-jade-light p-6 shadow-xl">
      {/* Blackboard texture */}
      <div className="pointer-events-none absolute inset-0 opacity-10 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjZmZmIj48L3JlY3Q+CjxwYXRoIGQ9Ik0wIDBMNCA0Wk00IDBMMCA0WiIgc3Ryb2tlLXdpZHRoPSIwLjUiIHN0cm9rZT0iIzAwMCI+PC9wYXRoPgo8L3N2Zz4=')]" />

      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-bold text-white/90">
          📸 Интерактивная доска
        </h2>
        <div className="flex items-center gap-2">
          {/* Grade selector */}
          <select
            value={grade || 1}
            onChange={(e) => setGrade(Number(e.target.value))}
            className="rounded bg-white/20 px-2 py-1 text-sm text-white"
          >
            {[1,2,3,4,5,6].map(g => <option key={g} value={g}>Класс {g}</option>)}
          </select>
          
          {/* Topic selector */}
          <select
            value={topic || 1}
            onChange={(e) => setTopic(Number(e.target.value))}
            className="rounded bg-white/20 px-2 py-1 text-sm text-white"
          >
            <option value={1}>Числа 1-10</option>
            <option value={2}>Числа 11-20</option>
            <option value={3}>Геометрия</option>
            <option value={4}>Сложение</option>
            <option value={5}>Вычитание</option>
            <option value={6}>CPA Метод</option>
            <option value={7}>Время</option>
            <option value={8}>Позиция</option>
            <option value={9}>Повторение</option>
          </select>

          <button
            onClick={loadImage}
            disabled={loadingImg}
            className="rounded-full bg-gold px-3 py-1 text-sm font-bold text-black"
          >
            {loadingImg ? "..." : "🔄"}
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="relative flex-1 overflow-hidden rounded-xl bg-white/5 backdrop-blur-sm">
        <AnimatePresence mode="wait">
          {/* CPA Component Priority */}
          {cpaData ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="flex h-full items-center justify-center p-4"
            >
              {cpaData.component === "TenFrame" && (
                <TenFrameViz data={{ type: 'ten_frame', filled: cpaData.data.filled, total: cpaData.data.total }} />
              )}
              {cpaData.component === "BarModel" && (
                <BarModelViz data={{ type: 'bar_model', total: 10, segments: cpaData.data.segments || [] }} />
              )}
              {cpaData.component === "NumberBond" && (
                <NumberBondViz data={{ type: 'number_bond', total: cpaData.data.total, parts: cpaData.data.parts || [] }} />
              )}
            </motion.div>
          ) : loadingImg ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex h-full items-center justify-center"
            >
              <img src={currentVisualData} alt="Math" className="max-h-full max-w-full object-contain"/>
            </motion.div>
          ) : imageUrl ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex h-full items-center justify-center p-4"
            >
              <img
                src={imageUrl}
                alt="Math"
                className="max-h-full max-w-full object-contain"
              />
            </motion.div>
          ) : currentVisualData ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex h-full items-center justify-center p-6"
            >
              {/* Legacy visualizations */}
              <img src={currentVisualData} alt="Math" className="max-h-full max-w-full object-contain"/>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex h-full flex-col items-center justify-center text-white/60"
            >
              <div className="mb-4 text-4xl">📚</div>
              <div>Выберите тему для повторения</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
