import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({
        unread_count: 3,
        urgent_count: 1,
        recent: [
            { id: 1, message: 'System Update Complete', type: 'info' },
            { id: 2, message: 'Worker Node Connected', type: 'success' }
        ]
    });
}
