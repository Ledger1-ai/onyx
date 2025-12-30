import { NextResponse } from 'next/server';
import { redisConnection } from '@/lib/queue';

export async function GET() {
    const now = new Date();

    try {
        const cachedSchedule = await redisConnection.get('schedule:daily_plan');

        if (cachedSchedule) {
            return NextResponse.json(JSON.parse(cachedSchedule));
        }

        // Fallback Mock Data
        const mockData = {
            date: now.toISOString(),
            slots: [
                {
                    slot_id: '1',
                    activity_type: 'MORNING_BRIEFING',
                    start_time: new Date(now.setHours(10, 0, 0)).toISOString(),
                    end_time: new Date(now.setHours(10, 30, 0)).toISOString(),
                    status: 'completed',
                    priority: 1
                },
                {
                    slot_id: '2',
                    activity_type: 'TWITTER_THREAD',
                    start_time: new Date(now.setHours(14, 0, 0)).toISOString(),
                    end_time: new Date(now.setHours(14, 45, 0)).toISOString(),
                    status: 'pending',
                    priority: 2
                }
            ]
        };

        return NextResponse.json(mockData);

    } catch (error) {
        console.error('Error fetching schedule:', error);
        return NextResponse.json({ date: now.toISOString(), slots: [] });
    }
}
