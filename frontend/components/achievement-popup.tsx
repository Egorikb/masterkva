"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Sparkles } from "lucide-react";

interface AchievementPopupProps {
  show: boolean;
  text: string;
}

export function AchievementPopup({ show, text }: AchievementPopupProps) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, scale: 0.5, y: 50 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.5, y: -50 }}
          className="fixed bottom-8 left-1/2 z-50 -translate-x-1/2"
        >
          <motion.div
            animate={{
              boxShadow: [
                "0 0 20px rgba(212, 175, 55, 0.3)",
                "0 0 40px rgba(212, 175, 55, 0.6)",
                "0 0 20px rgba(212, 175, 55, 0.3)",
              ],
            }}
            transition={{ duration: 0.5, repeat: Infinity }}
            className="flex items-center gap-3 rounded-full bg-gradient-to-r from-gold to-gold-light px-6 py-3 text-foreground shadow-xl"
          >
            <motion.div
              animate={{ rotate: [0, 15, -15, 0] }}
              transition={{ duration: 0.5, repeat: Infinity }}
            >
              <Sparkles className="h-6 w-6" />
            </motion.div>
            <span className="text-lg font-bold">{text}</span>
            <motion.div
              animate={{ rotate: [0, -15, 15, 0] }}
              transition={{ duration: 0.5, repeat: Infinity }}
            >
              <Sparkles className="h-6 w-6" />
            </motion.div>
          </motion.div>

          {/* Particle effects */}
          {[...Array(8)].map((_, i) => (
            <motion.div
              key={i}
              initial={{ 
                opacity: 1, 
                scale: 0,
                x: 0,
                y: 0
              }}
              animate={{ 
                opacity: 0, 
                scale: 1,
                x: Math.cos((i * Math.PI) / 4) * 80,
                y: Math.sin((i * Math.PI) / 4) * 80 - 40
              }}
              transition={{ duration: 0.8, delay: i * 0.05 }}
              className="absolute left-1/2 top-1/2 h-3 w-3 rounded-full bg-gold"
            />
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
