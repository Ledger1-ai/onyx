import { NextResponse } from 'next/server';
import { redisConnection } from '@/lib/queue';

export async function POST(req: Request) {
    try {
        const now = new Date();

        // 1. Get Configuration
        const configJson = await redisConnection.get('task:configuration');

        let enabledTasks: Record<string, any> = {};

        if (configJson) {
            enabledTasks = JSON.parse(configJson);
        } else {
            enabledTasks = {
                'TWITTER_TWEET_DAILY': true,
                'TWITTER_REPLY_MENTIONS': true,
                'TWITTER_ENGAGE_TIMELINE': true
            };
        }

        // 2. Define Available Task Types based on Config
        // We flat-map them into a list to rotate through
        const availableTaskTypes: { type: string, priority: number, platform: string, label: string }[] = [];

        // Twitter
        if (enabledTasks['TWITTER_ENGAGE_TIMELINE']) availableTaskTypes.push({ type: 'TWITTER_ENGAGE', priority: 2, platform: 'TWITTER', label: 'Timeline Engagement' });
        if (enabledTasks['TWITTER_TWEET_DAILY']) availableTaskTypes.push({ type: 'TWITTER_TWEET', priority: 1, platform: 'TWITTER', label: 'Tweet Generation' });
        if (enabledTasks['TWITTER_REPLY_MENTIONS']) availableTaskTypes.push({ type: 'TWITTER_REPLY', priority: 2, platform: 'TWITTER', label: 'Reply to Mentions' });
        if (enabledTasks['TWITTER_MONITOR_TRENDS']) availableTaskTypes.push({ type: 'TWITTER_TRENDS', priority: 3, platform: 'TWITTER', label: 'Trend Monitoring' });
        if (enabledTasks['TWITTER_FOLLOW_USER']) availableTaskTypes.push({ type: 'TWITTER_FOLLOW', priority: 3, platform: 'TWITTER', label: 'Follow User' });

        // LinkedIn
        // Frontend saves keys like 'linkedin_post', 'linkedin_connect' with values 0-100.
        // We check if value > 0 (or truthy) to determine if we should generate these tasks.

        if (enabledTasks['linkedin_post'] > 0) availableTaskTypes.push({ type: 'LINKEDIN_ARTICLE', priority: 2, platform: 'LINKEDIN', label: 'LinkedIn Article' });
        if (enabledTasks['linkedin_thread'] > 0) availableTaskTypes.push({ type: 'LINKEDIN_ARTICLE', priority: 2, platform: 'LINKEDIN', label: 'LinkedIn Content' });

        if (enabledTasks['linkedin_engage'] > 0) availableTaskTypes.push({ type: 'LINKEDIN_ENGAGE', priority: 2, platform: 'LINKEDIN', label: 'Feed Engagement' });
        if (enabledTasks['linkedin_search_engage'] > 0) availableTaskTypes.push({ type: 'LINKEDIN_ENGAGE', priority: 2, platform: 'LINKEDIN', label: 'Search Engagement' });

        if (enabledTasks['linkedin_connect'] > 0) availableTaskTypes.push({ type: 'LINKEDIN_CONNECT', priority: 3, platform: 'LINKEDIN', label: 'Growing Network' });

        if (enabledTasks['linkedin_monitor'] > 0) availableTaskTypes.push({ type: 'LINKEDIN_CHECK', priority: 3, platform: 'LINKEDIN', label: 'Check Notifications' });

        if (enabledTasks['linkedin_analytics'] > 0) availableTaskTypes.push({ type: 'LINKEDIN_ANALYTICS', priority: 4, platform: 'LINKEDIN', label: 'Fetch Analytics' });

        // Meta (API)
        // Note: Using flat toggle (true/false) from boolean config, but supporting numeric just in case
        if (enabledTasks['meta_facebook_post']) availableTaskTypes.push({ type: 'meta:facebook-post', priority: 2, platform: 'FACEBOOK', label: 'FB Page Post' });
        if (enabledTasks['meta_instagram_post']) availableTaskTypes.push({ type: 'meta:instagram-post', priority: 2, platform: 'INSTAGRAM', label: 'IG Feed Post' });
        if (enabledTasks['meta_engage']) availableTaskTypes.push({ type: 'meta:respond', priority: 3, platform: 'FACEBOOK', label: 'Meta Engagement' });
        if (enabledTasks['meta_analytics']) availableTaskTypes.push({ type: 'meta:analytics', priority: 4, platform: 'FACEBOOK', label: 'Meta Insights' });

        if (enabledTasks['meta_view_stories']) {
            availableTaskTypes.push({ type: 'meta:view-stories', priority: 3, platform: 'FACEBOOK', label: 'Watch FB Stories', data: { platform: 'facebook' } } as any);
            availableTaskTypes.push({ type: 'meta:view-stories', priority: 3, platform: 'INSTAGRAM', label: 'Watch IG Stories', data: { platform: 'instagram' } } as any);
        }
        if (enabledTasks['meta_view_reels']) {
            availableTaskTypes.push({ type: 'meta:view-reels', priority: 3, platform: 'FACEBOOK', label: 'Watch FB Reels', data: { platform: 'facebook' } } as any);
            availableTaskTypes.push({ type: 'meta:view-reels', priority: 3, platform: 'INSTAGRAM', label: 'Watch IG Reels', data: { platform: 'instagram' } } as any);
        }

        // System / Housekeeping (Always good to have some)
        if (enabledTasks['SYSTEM_HEALTH_CHECK']) availableTaskTypes.push({ type: 'SYSTEM_CHECK', priority: 1, platform: 'SYSTEM', label: 'System Health Check' });

        // If nothing enabled, default to Idle
        if (availableTaskTypes.length === 0) {
            availableTaskTypes.push({ type: 'System_Idle', priority: 3, platform: 'SYSTEM', label: 'Idle' });
        }

        // 3. Generate Schedule Loop (00:00 to 23:59) - Full 24h Cycle
        const slots = [];

        // Start at Midnight of today
        let currentSlot = new Date(now);
        currentSlot.setHours(0, 0, 0, 0);

        // End at Midnight of tomorrow
        const endTime = new Date(now);
        endTime.setDate(endTime.getDate() + 1);
        endTime.setHours(0, 0, 0, 0);

        // Helper to advance time
        const addMinutes = (date: Date, minutes: number) => new Date(date.getTime() + minutes * 60000);

        let taskIndex = 0;

        while (currentSlot < endTime) {
            // Select task (Round Robin)
            const task = availableTaskTypes[taskIndex % availableTaskTypes.length];
            taskIndex++;

            slots.push({
                slot_id: `slot_${Date.now()}_${slots.length}`,
                activity_type: task.type,
                start_time: currentSlot.toISOString(),
                end_time: addMinutes(currentSlot, 15).toISOString(), // 15 minute duration
                status: 'pending',
                priority: task.priority
            });

            // Advance time
            currentSlot = addMinutes(currentSlot, 15);
        }

        const newSchedule = {
            date: now.toISOString(),
            slots: slots
        };

        // 4. Save to Redis
        await redisConnection.set('schedule:daily_plan', JSON.stringify(newSchedule));

        return NextResponse.json({
            success: true,
            message: 'Schedule regenerated (24h / 15m intervals)',
            schedule: newSchedule
        });

    } catch (error) {
        console.error('Error regenerating schedule:', error);
        return NextResponse.json(
            { success: false, error: 'Internal Server Error' },
            { status: 500 }
        );
    }
}
