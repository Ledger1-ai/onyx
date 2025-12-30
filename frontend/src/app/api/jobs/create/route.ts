import { NextResponse } from 'next/server';
import { taskQueue } from '@/lib/queue';

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const { type, payload } = body;

        if (!type) {
            return NextResponse.json(
                { error: 'Job type is required' },
                { status: 400 }
            );
        }

        // Add job to the queue
        const job = await taskQueue.add(type, payload || {}, {
            // Priority handling could go here
            priority: body.priority || 0,
        });

        return NextResponse.json(
            {
                success: true,
                jobId: job.id,
                message: 'Job accepted'
            },
            { status: 202 }
        );
    } catch (error) {
        console.error('Error creating job:', error);
        return NextResponse.json(
            { error: 'Failed to create job' },
            { status: 500 }
        );
    }
}
