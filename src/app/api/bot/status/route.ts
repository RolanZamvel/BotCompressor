import { NextResponse } from 'next/server';

const BOT_SERVICE_PORT = 3002;

export async function GET() {
  try {
    const response = await fetch(`http://localhost:${BOT_SERVICE_PORT}/status`, {
      cache: 'no-store'
    });

    if (!response.ok) {
      throw new Error('Failed to fetch bot status');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        error: 'Bot service is unavailable'
      },
      { status: 503 }
    );
  }
}
