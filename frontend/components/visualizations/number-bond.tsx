"use client";

import { motion } from "framer-motion";
import type { NumberBondData } from "@/lib/types";

interface NumberBondVizProps {
  data: NumberBondData;
}

export function NumberBondViz({ data }: NumberBondVizProps) {
  const { total, parts } = data;

  return (
    <div className="flex flex-col items-center gap-4">
      <h3 className="text-lg font-semibold text-white/80">Связи чисел</h3>
      
      <svg
        viewBox="0 0 300 200"
        className="h-auto w-full max-w-[300px]"
      >
        {/* Lines connecting total to parts */}
        {parts.map((_, index) => {
          const partX = 75 + index * 150;
          return (
            <motion.line
              key={`line-${index}`}
              x1="150"
              y1="50"
              x2={partX}
              y2="150"
              stroke="rgba(255,255,255,0.4)"
              strokeWidth="3"
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            />
          );
        })}

        {/* Total circle at top */}
        <motion.g
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200, delay: 0 }}
        >
          <circle
            cx="150"
            cy="50"
            r="40"
            fill="rgba(212, 175, 55, 0.9)"
            stroke="white"
            strokeWidth="3"
          />
          <text
            x="150"
            y="58"
            textAnchor="middle"
            fill="white"
            fontSize="28"
            fontWeight="bold"
          >
            {total}
          </text>
        </motion.g>

        {/* Part circles at bottom */}
        {parts.map((part, index) => {
          const partX = 75 + index * 150;
          return (
            <motion.g
              key={`part-${index}`}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ 
                type: "spring", 
                stiffness: 200, 
                delay: 0.3 + index * 0.15 
              }}
            >
              <circle
                cx={partX}
                cy="150"
                r="35"
                fill="rgba(255,255,255,0.2)"
                stroke="white"
                strokeWidth="3"
              />
              <text
                x={partX}
                y="158"
                textAnchor="middle"
                fill="white"
                fontSize="24"
                fontWeight="bold"
              >
                {part}
              </text>
            </motion.g>
          );
        })}

        {/* Plus sign between parts */}
        <motion.text
          x="150"
          y="158"
          textAnchor="middle"
          fill="rgba(255,255,255,0.6)"
          fontSize="28"
          fontWeight="bold"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          +
        </motion.text>
      </svg>

      {/* Equation display */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="mt-4 rounded-xl bg-white/10 px-6 py-3 text-center"
      >
        <span className="text-2xl font-bold text-white">
          {parts.join(" + ")} = {total}
        </span>
      </motion.div>
    </div>
  );
}
