import { NextRequest, NextResponse } from 'next/server';
import * as path from 'path';
import * as fs from 'fs';

const imagesDir = path.join(process.cwd(), 'public', 'images');

// Mapping: topic -> textbook page
const topicToPage: Record<string, string> = {
  addition: '094',
  subtraction: '095',
  multiplication: '096',
  division: '097',
  geometry: '034',
  numbers: '019',
  cpa: '094',
  time: '110',
  position: '120',
  '1': '019',
  '2': '025',
  '3': '034',
  '4': '042',
  '5': '052',
  '6': '094',
  '7': '110',
  '8': '120',
  '9': '200',
  '019': '019',
  '025': '025',
  '034': '034',
  '042': '042',
  '052': '052',
  '094': '094',
  '095': '095',
  '096': '096',
  '097': '097',
  '110': '110',
  '120': '120',
};

// Fallback простой серый квадрат
const fallbackPng = Buffer.from([
  0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
  0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
  0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE,
]);

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ grade: string; topic: string }> }
) {
  const { grade, topic } = await params;
  const page = topicToPage[topic] || topic.padStart(3, '0');

  const candidates = [
    path.join(imagesDir, grade, `${page}.png`),
    path.join(imagesDir, grade, `page${page}.png`),
    path.join(imagesDir, grade, `grade${grade}_page${page}.png`),
    path.join(imagesDir, grade, `grade${grade}_page94.png`),
  ];

  for (const filepath of candidates) {
    try {
      if (fs.existsSync(filepath)) {
        const stat = fs.statSync(filepath);
        if (stat.isFile() && stat.size > 100) {
          const buffer = fs.readFileSync(filepath);
          return new NextResponse(buffer, { headers: { 'Content-Type': 'image/png' } });
        }
      }
    } catch {
      // ignore and continue fallback chain
    }
  }

  return new NextResponse(fallbackPng, {
    headers: { 'Content-Type': 'image/png' },
  });
}