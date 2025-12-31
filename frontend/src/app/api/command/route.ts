import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Job from '@/models/Job';
import { getCurrentUser } from '@/lib/auth';

export async function POST(request: Request) {
    try {
        await connectDB();

        // 1. Authenticate User
        const user = await getCurrentUser();
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const body = await request.json();
        const { command } = body;

        if (!command) {
            return NextResponse.json({ error: 'Command is required' }, { status: 400 });
        }

        // Simple parser to guess job type
        let jobType = 'twitter-scrape';
        let jobData: any = {
            command,
            userId: user._id // Inject User ID for multi-tenant isolation
        };

        const cmd = command.toLowerCase();

        if (cmd.startsWith('tweet ')) {
            jobType = 'twitter:post';
            jobData.content = command.slice(6);
        } else if (cmd.includes('search')) {
            jobType = 'twitter-scrape';
            jobData.query = command.replace('search', '').trim();
        } else if (cmd.includes('follow')) {
            jobType = 'twitter:follow';
            jobData.target = command.replace('follow', '').trim();
        } else if (cmd === 'ping' || cmd === 'test') {
            jobType = 'test-job';
        }

        // Create Job in MongoDB
        const job = await Job.create({
            type: jobType,
            data: jobData,
            status: 'pending'
        });

        return NextResponse.json({
            success: true,
            message: `Command dispatched: ${jobType}`,
            jobId: job._id,
            result: `✅ Task dispatched: ${jobType} (ID: ${job._id})` // Keeping same format for UI
        });

    } catch (error) {
        console.error('Error processing command:', error);
        return NextResponse.json(
            { error: 'Internal Server Error', details: String(error) },
            { status: 500 }
        );
    }
}
