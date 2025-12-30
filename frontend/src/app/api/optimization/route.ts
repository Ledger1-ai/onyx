import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({
        current_strategy: {
            name: 'Growth & Engagement',
            description: 'Focusing on high-value interactions'
        },
        activity_distribution: {
            twitter: 60,
            linkedin: 40
        }
    });
}
