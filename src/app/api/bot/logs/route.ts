import { NextResponse } from 'next/server';
import { NextRequest } from 'next/server';

const BOT_SERVICE_PORT = 3002;

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const limit = searchParams.get('limit') || '100';

    const response = await fetch(
      `http://localhost:${BOT_SERVICE_PORT}/logs?limit=${limit}`,
      {
        cache: 'no-store'
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch logs');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        logs: [],
        total: 0,
        error: 'Bot service is unavailable'
      },
      { status: 503 }
    );
  }
}
