import { NextResponse } from 'next/server';

const BOT_SERVICE_PORT = 3002;

export async function POST() {
  try {
    const response = await fetch(`http://localhost:${BOT_SERVICE_PORT}/restart`, {
      method: 'GET',
      cache: 'no-store'
    });

    if (!response.ok) {
      throw new Error('Failed to restart bot');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to restart bot'
      },
      { status: 503 }
    );
  }
}
