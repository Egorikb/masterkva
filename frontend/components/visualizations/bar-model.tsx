"use client";

import { motion } from "framer-motion";
import type { BarModelData } from "@/lib/types";

interface BarModelVizProps {
  data: BarModelData;
}

const colorMap: Record<string, string> = {
  jade: "rgba(61, 153, 112, 0.9)",
  gold: "rgba(212, 175, 55, 0.9)",
  default: "rgba(255, 255, 255, 0.3)",
};

export function BarModelViz({ data }: BarModelVizProps) {
  const { total, segments } = data;

  return (
    <div className="flex w-full max-w-md flex-col gap-4">
      <h3 className="text-center text-lg font-semibold text-white/80">
        Столбиковая модель
      </h3>

      {/* Total bar */}
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.5 }}
        className="relative h-16 w-full origin-left overflow-hidden rounded-xl bg-white/20 border-2 border-white/40"
      >
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold text-white">
            Всего: {total}
          </span>
        </div>
      </motion.div>

      {/* Segments bar */}
      <div className="relative flex h-20 w-full overflow-hidden rounded-xl border-2 border-white/40">
        {segments.map((segment, index) => {
          const widthPercent = (segment.value / total) * 100;
          const bgColor = colorMap[segment.color || "default"] || colorMap.default;

          return (
            <motion.div
              key={index}
              initial={{ scaleX: 0, opacity: 0 }}
              animate={{ scaleX: 1, opacity: 1 }}
              transition={{ 
                duration: 0.4, 
                delay: 0.5 + index * 0.15,
                ease: "easeOut"
              }}
              style={{ 
                width: `${widthPercent}%`,
                backgroundColor: bgColor,
              }}
              className="relative flex origin-left items-center justify-center border-r border-white/30 last:border-r-0"
            >
              <div className="flex flex-col items-center">
                <span className="text-lg font-bold text-white">
                  {segment.label}
                </span>
                <span className="text-sm text-white/70">
                  {typeof segment.value === 'number' && segment.value < 1 
                    ? `${(segment.value * 100).toFixed(0)}%`
                    : segment.value
                  }
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Legend */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        className="mt-2 flex flex-wrap justify-center gap-4"
      >
        {segments.map((segment, index) => (
          <div key={index} className="flex items-center gap-2">
            <div
              className="h-4 w-4 rounded"
              style={{
                backgroundColor: colorMap[segment.color || "default"],
              }}
            />
            <span className="text-sm text-white/80">{segment.label}</span>
          </div>
        ))}
      </motion.div>
    </div>
  );
}
