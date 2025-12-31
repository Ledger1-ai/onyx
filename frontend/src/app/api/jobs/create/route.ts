import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Job from '@/models/Job';

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

        await connectDB();

        // Add job to MongoDB
        const job = await Job.create({
            type: type,
            data: payload || {},
            status: 'pending',
            priority: body.priority || 0
        });

        return NextResponse.json(
            {
                success: true,
                jobId: job._id,
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
