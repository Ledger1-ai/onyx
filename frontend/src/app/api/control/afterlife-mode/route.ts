import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Setting from '@/models/Setting';

const KEY = 'afterlife:mode';

export async function GET() {
    try {
        await connectDB();
        const setting = await Setting.findOne({ key: KEY });
        const isEnabled = setting ? setting.value : false;

        return NextResponse.json({
            status: 'success',
            enabled: isEnabled === true
        });
    } catch (error) {
        return NextResponse.json({ error: 'Failed to fetch status' }, { status: 500 });
    }
}

export async function POST() {
    try {
        await connectDB();
        // Toggle the value directly in MongoDB
        const setting = await Setting.findOne({ key: KEY });
        const currentValue = setting ? setting.value : false;
        const newValue = !currentValue; // Toggle boolean

        // 1. Update Afterlife Mode
        await Setting.findOneAndUpdate(
            { key: KEY },
            { value: newValue },
            { upsert: true }
        );

        // 2. Fetch current task configuration
        const taskConfigSetting = await Setting.findOne({ key: 'task:configuration' });
        let taskConfig = taskConfigSetting ? taskConfigSetting.value : {};

        // 3. Update all relevant tasks based on Afterlife Mode
        // If Enabled: Enable all automation tasks
        // If Disabled: Disable all automation tasks (or revert to defaults? usually just disable)

        const AUTOMATION_TASKS = [
            'TWITTER_TWEET_DAILY', 'TWITTER_REPLY_MENTIONS', 'TWITTER_ENGAGE_TIMELINE',
            'TWITTER_LIKE_KEYWORD', 'TWITTER_MONITOR_TRENDS', 'TWITTER_PERFORMANCE_CHECK',
            'linkedin_post', 'linkedin_thread', 'linkedin_engage', 'linkedin_connect',
            'linkedin_monitor', 'linkedin_analytics',
            'meta_facebook_post', 'meta_instagram_post', 'meta_engage', 'meta_analytics',
            'meta_view_stories', 'meta_view_reels'
        ];

        AUTOMATION_TASKS.forEach(taskId => {
            taskConfig[taskId] = newValue;
        });

        // 4. Save Task Configuration
        await Setting.findOneAndUpdate(
            { key: 'task:configuration' },
            { value: taskConfig },
            { upsert: true }
        );

        return NextResponse.json({
            success: true,
            message: `Afterlife mode ${newValue ? 'enabled' : 'disabled'}`,
            enabled: newValue,
            tasksUpdated: true
        });
    } catch (error) {
        console.error('Error toggling afterlife mode:', error);
        return NextResponse.json({ error: 'Failed to toggle afterlife mode' }, { status: 500 });
    }
}
