import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import mongoose from 'mongoose';
import Setting from '@/models/Setting';

export const dynamic = 'force-dynamic';

export async function GET() {
    let dbStatus = false;
    let workerStatus = false;
    let activeMode = 'standard';

    try {
        // Check MongoDB Connection
        await connectDB();
        if (mongoose.connection.readyState === 1) {
            dbStatus = true;

            // Check Worker Heartbeat via Settings
            // Worker should update this key periodically
            const heartbeatSetting = await Setting.findOne({ key: 'worker:heartbeat' });
            if (heartbeatSetting && heartbeatSetting.value) {
                const lastHeartbeat = parseInt(heartbeatSetting.value);
                const diff = Date.now() - lastHeartbeat;
                // Allow up to 2 minutes delay for polling
                if (diff < 120000) {
                    workerStatus = true;
                }
            }

            // Check Afterlife Mode
            const afterlifeSetting = await Setting.findOne({ key: 'afterlife:mode' });
            if (afterlifeSetting && afterlifeSetting.value === true) {
                activeMode = 'afterlife';
            }
        }
    } catch (e) {
        console.error('Status check failed:', e);
    }

    return NextResponse.json({
        database: dbStatus,
        worker: workerStatus,
        active_mode: activeMode,
        daily_progress: 0.45, // Placeholder metric
        completed_activities: 12,
        total_activities: 45
    });
}
