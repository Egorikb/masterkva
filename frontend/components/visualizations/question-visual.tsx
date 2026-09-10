"use client";

import { motion } from "framer-motion";
import { NumberBondViz } from "./number-bond";
import type { QuestionVisualData } from "@/lib/types";

interface QuestionVisualProps {
  data: QuestionVisualData;
}

const circleColors = {
  red: "bg-red-500",
  blue: "bg-blue-500",
  emerald: "bg-emerald-500",
  gold: "bg-gold",
  purple: "bg-purple-500",
} as const;

const captionByVisual: Record<QuestionVisualData["cpaVisual"], string> = {
  counting: "Посчитай предметы",
  position: "Где предмет?",
  carry: "Посмотри на разрядный состав",
  number_line: "Найди число на линии",
  addition: "Сложи предметы глазами",
  shapes: "Найди нужную фигуру",
  clock: "Посмотри на время",
  division: "Раздели предметы на группы",
  mixed_ops: "Разберём пример по шагам",
  unknown: "Посмотри на схему",
};

export function QuestionVisual({ data }: QuestionVisualProps) {
  const parts = data.parts && data.parts.length ? data.parts : [3, 2];

  const renderCaption = () => (
    <div className="text-center text-white/80">
      <div className="text-sm font-medium">{captionByVisual[data.cpaVisual]}</div>
      {data.objects ? <div className="mt-1 text-xs text-white/55">{data.objects}</div> : null}
    </div>
  );

  const templateIconByType: Record<string, string> = {
    ten_frame: "🔟",
    number_line: "➕",
    base_ten_blocks: "🧱",
    place_value_chart: "📊",
    part_part_whole_bar: "🧩",
    area_model_grid: "▦",
    array_matrix: "⬛",
    bar_model_strip_diagram: "▭",
    ratio_table: "↔",
    double_number_line: "〰️",
    double_number_line_dynamic: "〰️",
    fraction_circle_region: "◔",
    percent_grid_10x10: "▦",
    coordinate_plane_plot: "✳️",
    algebra_tiles: "🧩",
    balance_scale_equation: "⚖️",
    balance_scale_linear: "⚖️",
    function_table: "📋",
    cartesian_graph: "📈",
    cartesian_graph_slider: "📈",
    net_of_solid: "🧊",
    geoboard_dynamic: "📐",
    spatial_relations: "⬆️",
    shape_recognition: "◻️",
    clock_face: "🕒",
    fraction_bars: "▭",
    cut_and_drag_parallelogram: "▱",
    division_groups: "÷",
  };

  const renderTemplateBlueprint = () => {
    const stageLabel =
      data.templateStage === "concrete_pictorial_abstract"
        ? "CPA"
        : data.templateStage?.toUpperCase() ?? "Шаблон";

    return (
      <div className="flex w-full max-w-3xl flex-col gap-4 rounded-3xl border border-white/10 bg-white/8 p-5 text-white shadow-2xl backdrop-blur-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-3xl">{templateIconByType[data.templateType ?? ""] ?? "🪄"}</div>
            <h3 className="mt-2 text-xl font-semibold text-white/95">{data.templateLabel ?? data.templateType}</h3>
            <p className="text-sm text-white/65">{data.templateFamily} · {stageLabel}</p>
          </div>
          {data.templateNotes ? (
            <div className="max-w-xs rounded-2xl bg-black/15 px-3 py-2 text-xs text-white/70">
              {data.templateNotes}
            </div>
          ) : null}
          {data.templateReason ? (
            <div className="max-w-sm rounded-2xl bg-white/10 px-3 py-2 text-xs text-white/70">
              {data.templateReason}
            </div>
          ) : null}
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          {(data.templateSections ?? []).map((section) => (
            <div key={section.label} className="rounded-2xl border border-white/10 bg-black/10 p-4">
              <div className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-white/60">
                {section.label}
              </div>
              <ul className="space-y-2 text-sm text-white/85">
                {section.bullets.map((bullet) => (
                  <li key={bullet} className="rounded-xl bg-white/10 px-3 py-2">
                    {bullet}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {data.templateSkills?.length ? (
          <div className="flex flex-wrap gap-2 rounded-2xl border border-white/10 bg-white/8 p-3 text-xs text-white/70">
            <span className="font-semibold uppercase tracking-[0.16em] text-white/45">Skills</span>
            {data.templateSkills.map((skill) => (
              <span key={skill} className="rounded-full bg-white/10 px-2.5 py-1">
                {skill}
              </span>
            ))}
          </div>
        ) : null}

        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl bg-emerald-500/15 p-4">
            <div className="mb-1 text-xs uppercase tracking-[0.18em] text-emerald-100/70">Что скрыть</div>
            <div className="text-sm text-white/85">{data.templateHide}</div>
          </div>
          <div className="rounded-2xl bg-gold/15 p-4">
            <div className="mb-1 text-xs uppercase tracking-[0.18em] text-gold/90">Почему это работает</div>
            <div className="text-sm text-white/85">{data.templateWhy}</div>
          </div>
        </div>
      </div>
    );
  };

  const renderConcreteArithmeticTemplate = () => {
    const numbers = Array.from(data.prompt.matchAll(/\d+/g), (match) => Number(match[0]));
    if (numbers.length < 2) {
      return renderTemplateBlueprint();
    }

    const isSubtract = data.templateType === "number_line"
      || data.templateFamily === "addition_subtraction" && /[-−]|выч|убер|остал|минус|отня/i.test(data.prompt.toLowerCase());

    return (
      <NumberBondViz
        data={{
          type: "number_bond",
          total: isSubtract ? numbers[0] : numbers[0] + numbers[1],
          parts: numbers.slice(0, 2),
          prompt: data.prompt,
          title: data.title,
          operation: isSubtract ? "subtract" : "add",
        }}
      />
    );
  };

  const renderCounting = () => {
    const colors = data.colors && data.colors.length ? data.colors : [];
    const items = parts.flatMap((part, groupIndex) =>
      Array.from({ length: part }, (_, index) => ({
        groupIndex,
        index,
        colorClass:
          circleColors[colors[groupIndex] as keyof typeof circleColors] ??
          circleColors.red,
      }))
    );
    const promptLower = data.prompt.toLowerCase();
    const isSubtract = /[-−]|выч|убер|остал|минус|отня/i.test(promptLower);
    const symbol = isSubtract ? "−" : "+";
    const caption = isSubtract ? "Убери предметы и найди остаток" : captionByVisual[data.cpaVisual];

    return (
      <div className="flex flex-col items-center gap-4">
        <h3 className="text-lg font-semibold text-white/85">{data.title}</h3>
        <div className="rounded-2xl bg-white/10 p-5">
          <div className="grid grid-cols-5 gap-3">
            {items.map((item, idx) => (
              <motion.div
                key={idx}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: idx * 0.04 }}
                className={`h-10 w-10 rounded-full ${item.colorClass} shadow-md`}
                aria-label={`Предмет ${idx + 1}`}
              />
            ))}
          </div>
        </div>
        <div className="text-4xl font-bold text-white/80" aria-hidden="true">{symbol}</div>
        {data.objects ? <div className="rounded-xl bg-white/10 px-4 py-2 text-center text-sm text-white/70">{caption}{data.objects ? ` · ${data.objects}` : ""}</div> : renderCaption()}
      </div>
    );
  };

  const renderPosition = () => (
    <div className="flex flex-col items-center gap-4">
      <h3 className="text-lg font-semibold text-white/85">{data.title}</h3>
      <div className="relative h-44 w-full max-w-md rounded-2xl bg-white/10 p-6">
        <div className="absolute left-6 right-6 top-10 h-3 rounded-full bg-white/20" />
        <div className="absolute left-1/2 top-16 h-12 w-12 -translate-x-1/2 rounded-full bg-gold shadow-lg" />
        <div className="absolute bottom-6 left-6 text-sm text-white/70">под</div>
        <div className="absolute top-2 left-6 text-sm text-white/70">стол</div>
      </div>
      {renderCaption()}
    </div>
  );

  const renderShapes = () => (
    <div className="flex flex-col items-center gap-4">
      <h3 className="text-lg font-semibold text-white/85">{data.title}</h3>
      <div className="flex gap-6">
        <div className="h-20 w-20 rounded-xl border-4 border-white bg-white/10" />
        <div className="h-20 w-20 rounded-full border-4 border-white bg-white/10" />
        <div className="h-20 w-20 rotate-45 border-4 border-white bg-white/10" />
      </div>
      {renderCaption()}
    </div>
  );

  const renderClock = () => (
    <div className="flex flex-col items-center gap-4">
      <h3 className="text-lg font-semibold text-white/85">{data.title}</h3>
      <div className="relative h-48 w-48 rounded-full border-4 border-white/70 bg-white/10">
        <div
          className="absolute left-1/2 top-1/2 h-1 w-16 origin-left -translate-y-1/2 bg-white"
          style={{ transform: "translateY(-50%) rotate(0deg)" }}
        />
        <div
          className="absolute left-1/2 top-1/2 h-1 w-12 origin-left -translate-y-1/2 bg-gold"
          style={{ transform: "translateY(-50%) rotate(90deg)" }}
        />
        <div className="absolute inset-0 flex items-center justify-center text-4xl text-white">
          6:00
        </div>
      </div>
      {renderCaption()}
    </div>
  );

  const renderFallback = () => (
    <div className="flex flex-col items-center gap-4 text-center">
      <h3 className="text-lg font-semibold text-white/85">{data.title}</h3>
      <div className="grid grid-cols-3 gap-3 rounded-2xl bg-white/10 p-5">
        <div className="h-10 w-10 rounded-full bg-red-500 shadow-md" />
        <div className="h-10 w-10 rounded-full bg-blue-500 shadow-md" />
        <div className="h-10 w-10 rounded-full bg-emerald-500 shadow-md" />
      </div>
      {renderCaption()}
    </div>
  );

  if (data.templateType && data.templateSections?.length) {
    const family = data.templateFamily ?? "";
    const promptLower = data.prompt.toLowerCase();
    const looksLikeArithmetic = /[+−-]/.test(data.prompt) || /сколько всего|плюс|прибав|слож|выч|убер|останет|минус|отня/i.test(promptLower);

    if (["addition_subtraction", "place_value"].includes(family) && looksLikeArithmetic) {
      return renderConcreteArithmeticTemplate();
    }

    return renderTemplateBlueprint();
  }

  switch (data.cpaVisual) {
    case "counting":
      return renderCounting();
    case "position":
      return renderPosition();
    case "shapes":
      return renderShapes();
    case "clock":
      return renderClock();
    default:
      return renderFallback();
  }
}
