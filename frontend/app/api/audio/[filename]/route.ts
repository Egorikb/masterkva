import { NextRequest, NextResponse } from 'next/server';

const BACKEND_AUDIO_BASE_URL =
  process.env.BACKEND_AUDIO_BASE_URL ?? 'http://127.0.0.1:8001/audio_storage';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ filename: string }> }
) {
  const { filename } = await params;
  const url = `${BACKEND_AUDIO_BASE_URL.replace(/\/$/, '')}/${encodeURIComponent(filename)}`;

  try {
    const upstream = await fetch(url, { cache: 'no-store' });
    if (!upstream.ok) {
      return new NextResponse('Not Found', { status: 404 });
    }

    const audio = await upstream.arrayBuffer();
    return new NextResponse(audio, {
      headers: {
        'Content-Type': upstream.headers.get('content-type') ?? 'audio/ogg',
        'Cache-Control': 'public, max-age=3600',
      },
    });
  } catch {
    return new NextResponse('Audio service unavailable', { status: 502 });
  }
}
