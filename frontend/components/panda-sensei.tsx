"use client";

import { motion } from "framer-motion";
import { useChatStore } from "@/lib/chat-store";

export function PandaSensei() {
  const { isLoading } = useChatStore();

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.5 }}
      className="absolute bottom-4 right-4 z-10"
    >
      <div className="relative">
        {/* Speech bubble when loading */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute -top-16 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-xl bg-white px-4 py-2 text-sm font-medium text-jade-dark shadow-lg"
          >
            Хммм... 🤔
            <div className="absolute -bottom-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 bg-white" />
          </motion.div>
        )}

        {/* Panda SVG */}
        <motion.svg
          width="100"
          height="120"
          viewBox="0 0 100 120"
          animate={{
            y: isLoading ? [0, -5, 0] : 0,
          }}
          transition={{
            duration: 1,
            repeat: isLoading ? Infinity : 0,
          }}
          className="drop-shadow-lg"
        >
          {/* Body */}
          <ellipse cx="50" cy="85" rx="30" ry="25" fill="white" />
          <ellipse cx="50" cy="90" rx="20" ry="15" fill="#f0f0f0" />

          {/* Head */}
          <circle cx="50" cy="45" r="30" fill="white" />

          {/* Ears */}
          <circle cx="25" cy="22" r="12" fill="#1a1a1a" />
          <circle cx="75" cy="22" r="12" fill="#1a1a1a" />

          {/* Eye patches */}
          <ellipse cx="35" cy="42" rx="12" ry="10" fill="#1a1a1a" />
          <ellipse cx="65" cy="42" rx="12" ry="10" fill="#1a1a1a" />

          {/* Eyes */}
          <motion.g
            animate={{
              scaleY: isLoading ? [1, 0.1, 1] : 1,
            }}
            transition={{
              duration: 0.3,
              repeat: isLoading ? Infinity : 0,
              repeatDelay: 2,
            }}
          >
            <circle cx="35" cy="42" r="5" fill="white" />
            <circle cx="65" cy="42" r="5" fill="white" />
            <circle cx="36" cy="41" r="2" fill="#1a1a1a" />
            <circle cx="66" cy="41" r="2" fill="#1a1a1a" />
          </motion.g>

          {/* Nose */}
          <ellipse cx="50" cy="52" rx="5" ry="3" fill="#1a1a1a" />

          {/* Mouth */}
          <path
            d="M 45 58 Q 50 62 55 58"
            stroke="#1a1a1a"
            strokeWidth="2"
            fill="none"
          />

          {/* Headband */}
          <rect x="20" y="28" width="60" height="6" fill="#d4af37" rx="2" />
          <circle cx="50" cy="31" r="5" fill="#d4af37" />
          <text
            x="50"
            y="34"
            textAnchor="middle"
            fill="#8b7355"
            fontSize="6"
            fontWeight="bold"
          >
            功
          </text>

          {/* Arms */}
          <ellipse cx="25" cy="80" rx="8" ry="15" fill="#1a1a1a" />
          <ellipse cx="75" cy="80" rx="8" ry="15" fill="#1a1a1a" />

          {/* Staff */}
          <motion.g
            animate={{
              rotate: isLoading ? [0, 5, 0, -5, 0] : 0,
            }}
            transition={{
              duration: 2,
              repeat: isLoading ? Infinity : 0,
            }}
            style={{ transformOrigin: "85px 60px" }}
          >
            <rect x="82" y="20" width="4" height="90" fill="#8B4513" rx="2" />
            <circle cx="84" cy="20" r="6" fill="#d4af37" />
          </motion.g>

          {/* Feet */}
          <ellipse cx="35" cy="108" rx="10" ry="6" fill="#1a1a1a" />
          <ellipse cx="65" cy="108" rx="10" ry="6" fill="#1a1a1a" />
        </motion.svg>

        {/* Pointing arrow */}
        <motion.div
          animate={{ x: [-5, 5, -5] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="absolute -left-6 top-1/2 -translate-y-1/2"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            className="text-white/60"
          >
            <path
              d="M12 5l7 7-7 7"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </motion.div>
      </div>
    </motion.div>
  );
}
