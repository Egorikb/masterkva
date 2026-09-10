"use client";

import { motion } from "framer-motion";
import type { NumberBondData } from "@/lib/types";

interface NumberBondVizProps {
  data: NumberBondData;
}

function ObjectRow({ count, color }: { count: number; color: string }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="text-sm font-semibold text-white/80">{count}</div>
      <div className="flex flex-wrap justify-center gap-2 rounded-2xl bg-white/10 px-4 py-4">
        {Array.from({ length: count }, (_, index) => (
          <motion.div
            key={index}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className={`h-10 w-10 rounded-full ${color} shadow-md`}
          />
        ))}
      </div>
    </div>
  );
}

export function NumberBondViz({ data }: NumberBondVizProps) {
  const parts = data.parts && data.parts.length ? data.parts : [3, 2];
  const [left = 0, right = 0] = parts;
  const prompt = `${data.title ?? ""} ${data.prompt ?? ""}`.toLowerCase();
  const isSubtract = data.operation === "subtract" || /[-−]|выч|убер|остал|минус|отня/i.test(prompt);
  const symbol = isSubtract ? "−" : "+";
  const title = isSubtract ? "Вычитание глазами" : "Сложение глазами";
  const caption = isSubtract ? "Убери предметы и найди остаток" : "Посчитай предметы и найди ответ";

  return (
    <div className="flex flex-col items-center gap-5">
      <h3 className="text-lg font-semibold text-white/85">{title}</h3>

      <div className="flex items-center justify-center gap-4">
        <ObjectRow count={left} color="bg-red-500" />

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="text-4xl font-bold text-white/80"
          aria-hidden="true"
        >
          {symbol}
        </motion.div>

        <ObjectRow count={right} color="bg-blue-500" />

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="text-4xl font-bold text-white/80"
          aria-hidden="true"
        >
          =
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.35 }}
          className="flex h-24 w-24 items-center justify-center rounded-full border-2 border-dashed border-white/40 bg-white/10 text-4xl font-bold text-white"
          aria-label="Нужно найти ответ"
        >
          ?
        </motion.div>
      </div>

      <div className="rounded-xl bg-white/10 px-4 py-2 text-center text-sm text-white/70">
        {caption}
      </div>
    </div>
  );
}
