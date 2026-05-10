import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

const imagesDir = '/home/egor/ai-agent/workspace/deeptutor_analyzed/public/images/china_math';
const textbookDir = '/home/egor/ai-agent/workspace/front_deeptutor/public/images/textbook';

// Mapping: topic -> textbook page
const topicToPage: Record<string, string> = {
  'addition': '042', 'subtraction': '052', 'multiplication': '096',
  'division': '097', 'geometry': '034', 'numbers': '019',
  'cpa': '094', 'time': '110', 'position': '120',
  '1': '019', '2': '025', '3': '034', '4': '042', 
  '5': '052', '6': '094', '7': '110', '8': '120', '9': '200',
  '019': '019', '025': '025', '034': '034', '042': '042',
  '052': '052', '094': '094', '110': '110', '120': '120',
};

// Fallback простой серый квадрат
const fallbackPng = Buffer.from([
  0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
  0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
  0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE
]);

export async function GET(request: NextRequest, { params }: { params: Promise<{ grade: string; topic: string }> }) {
  const { grade, topic } = await params;
  const page = topicToPage[topic] || topic.padStart(3, '0');
  
  // 1. Пробуем textbook (реальные страницы)
  // Ищем: gradeX_pageYYY.png или page22.png
  const textbookNames = [
    `grade${grade}_page${page}.png`,
    `grade1_page94.png`,  // CPA method
    `page22.png`,
  ];
  
  for (const filename of textbookNames) {
    const filepath = path.join(textbookDir, filename);
    if (fs.existsSync(filepath)) {
      const buffer = fs.readFileSync(filepath);
      return new NextResponse(buffer, { headers: { 'Content-Type': 'image/png' } });
    }
  }
  
  // 2. Пробуем china_math директорию
  for (const filename of textbookNames) {
    const filepath = path.join(imagesDir, filename);
    try {
      if (fs.existsSync(filepath)) {
        const stat = fs.statSync(filepath);
        if (stat.size > 100) {
          const buffer = fs.readFileSync(filepath);
          return new NextResponse(buffer, { headers: { 'Content-Type': 'image/png' } });
        }
      }
    } catch {}
  }
  
  // 3. Fallback - серый квадрат
  return new NextResponse(fallbackPng, {
    headers: { 'Content-Type': 'image/png' },
  });
}