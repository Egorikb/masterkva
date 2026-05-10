"use client";

import { motion } from "framer-motion";
import type { TenFrameData } from "@/lib/types";

interface TenFrameVizProps {
  data: TenFrameData;
}

export function TenFrameViz({ data }: TenFrameVizProps) {
  const { filled, total = 10 } = data;
  const frameCount = Math.ceil(total / 10);
  const frames = Array.from({ length: frameCount }, (_, frameIndex) => {
    const startIndex = frameIndex * 10;
    return Array.from({ length: 10 }, (_, cellIndex) => {
      const globalIndex = startIndex + cellIndex;
      return globalIndex < filled;
    });
  });

  return (
    <div className="flex flex-col items-center gap-6">
      <h3 className="text-lg font-semibold text-white/80">
        Десятичная рамка
      </h3>

      <div className="flex flex-col gap-6">
        {frames.map((frame, frameIndex) => (
          <motion.div
            key={frameIndex}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: frameIndex * 0.2 }}
            className="relative"
          >
            {/* Frame label */}
            <div className="absolute -left-8 top-1/2 -translate-y-1/2 text-sm font-medium text-white/60">
              {frameIndex * 10 + 1}-{Math.min((frameIndex + 1) * 10, total)}
            </div>

            {/* 2x5 grid */}
            <div className="grid grid-cols-5 gap-2 rounded-xl bg-white/10 p-3 border-2 border-white/30">
              {frame.map((isFilled, cellIndex) => {
                const globalIndex = frameIndex * 10 + cellIndex;
                
                return (
                  <motion.div
                    key={cellIndex}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{
                      type: "spring",
                      stiffness: 300,
                      delay: 0.3 + globalIndex * 0.05,
                    }}
                    className={`relative flex h-12 w-12 items-center justify-center rounded-lg border-2 transition-colors ${
                      isFilled
                        ? "border-gold bg-gold/20"
                        : "border-white/20 bg-white/5"
                    }`}
                  >
                    {isFilled && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{
                          type: "spring",
                          stiffness: 400,
                          delay: 0.4 + globalIndex * 0.05,
                        }}
                        className="h-8 w-8 rounded-full bg-gold shadow-lg"
                      />
                    )}
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Count display */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="flex items-center gap-4 rounded-xl bg-white/10 px-6 py-3"
      >
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded-full bg-gold" />
          <span className="text-lg font-bold text-white">= {filled}</span>
        </div>
        {total > 10 && (
          <>
            <span className="text-white/40">|</span>
            <span className="text-lg text-white/70">
              из {total} ячеек
            </span>
          </>
        )}
      </motion.div>

      {/* Visual equation for numbers over 10 */}
      {filled > 10 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="text-center text-white/80"
        >
          <span className="text-lg">
            10 + {filled - 10} = {filled}
          </span>
        </motion.div>
      )}
    </div>
  );
}
