import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({
        recent_sessions: [
            { timestamp: new Date().toISOString(), message: 'System migrated to Full Stack architecture', level: 'success' },
            { timestamp: new Date(Date.now() - 50000).toISOString(), message: 'Worker service initialized', level: 'info' }
        ]
    });
}
