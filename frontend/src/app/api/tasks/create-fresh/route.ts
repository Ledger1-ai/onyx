import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Setting from '@/models/Setting';

export async function POST(req: Request) {
    try {
        await connectDB();
        // Hard Reset
        await Setting.deleteOne({ key: 'task:configuration' });
        await Setting.deleteOne({ key: 'schedule:daily_plan' });

        return NextResponse.json({
            success: true,
            message: 'System reset to fresh state. Default configuration loaded.'
        });

    } catch (error) {
        console.error('Error resetting system:', error);
        return NextResponse.json(
            { success: false, error: 'Internal Server Error' },
            { status: 500 }
        );
    }
}
