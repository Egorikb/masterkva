import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ filename: string }> }
) {
  const { filename } = await params;
  
  // Path to backend audio storage
  const audioDir = '/home/egor/ai-agent/workspace/deeptutor_analyzed/audio_storage';
  const filePath = path.join(audioDir, filename);
  
  if (!fs.existsSync(filePath)) {
    return new NextResponse('Not Found', { status: 404 });
  }
  
  const fileBuffer = fs.readFileSync(filePath);
  
  return new NextResponse(fileBuffer, {
    headers: {
      'Content-Type': 'audio/ogg',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
