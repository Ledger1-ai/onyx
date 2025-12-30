import { NextResponse } from 'next/server';
import { redisConnection } from '@/lib/queue';

const REDIS_KEY = 'task:configuration';

export async function POST(req: Request) {
    try {
        const { taskId } = await req.json();

        if (!taskId) {
            return NextResponse.json(
                { success: false, error: 'Task ID is required' },
                { status: 400 }
            );
        }

        // Get current state
        const currentData = await redisConnection.get(REDIS_KEY);

        // Default Task Definitions (Must match configuration/route.ts)
        const DEFAULT_TASKS = [
            { id: 'TWITTER_TWEET_DAILY', enabled: true },
            { id: 'TWITTER_REPLY_MENTIONS', enabled: true },
            { id: 'TWITTER_ENGAGE_TIMELINE', enabled: true },
            { id: 'TWITTER_CONTENT_CURATION', enabled: false },
            { id: 'TWITTER_FOLLOW_TARGETS', enabled: false },
            { id: 'TWITTER_LIKE_KEYWORD', enabled: true },
            { id: 'TWITTER_RETWEET_PARTNERS', enabled: false },
            { id: 'TWITTER_MONITOR_TRENDS', enabled: true },
            { id: 'TWITTER_PERFORMANCE_CHECK', enabled: true },

            // LinkedIn
            { id: 'linkedin_post', enabled: true },
            { id: 'linkedin_thread', enabled: true },
            { id: 'linkedin_engage', enabled: true },
            { id: 'linkedin_search_engage', enabled: false },
            { id: 'linkedin_connect', enabled: true },
            { id: 'linkedin_monitor', enabled: true },
            { id: 'linkedin_analytics', enabled: true },

            // Meta (API) - Phase 3
            { id: 'meta_facebook_post', enabled: true },
            { id: 'meta_instagram_post', enabled: true },
            { id: 'meta_engage', enabled: true },
            { id: 'meta_analytics', enabled: true },
            { id: 'meta_view_stories', enabled: true },
            { id: 'meta_view_reels', enabled: true },

            // System
            { id: 'SYSTEM_HEALTH_CHECK', enabled: true },
            { id: 'SYSTEM_BACKUP_DAILY', enabled: true }
        ];

        // 1. Build current full state
        const fullState: Record<string, boolean> = {};
        DEFAULT_TASKS.forEach(t => fullState[t.id] = t.enabled);

        if (currentData) {
            const redisState = JSON.parse(currentData);
            Object.assign(fullState, redisState);
        }

        // 2. Toggle
        // For new items not in legacy redis, we rely on the default merged above
        // We still check if the key exists in our 'known universe' to prevent garbage
        const knownIds = new Set(DEFAULT_TASKS.map(t => t.id));

        // Optional: allow unknown IDs (dynamic)? For now, strict is safer.
        if (!knownIds.has(taskId)) {
            // console.warn(`Toggling unknown task ID: ${taskId}`); 
            // We can allow it to support future dynamic keys without redeploy
        }

        fullState[taskId] = !fullState[taskId];

        // 3. Save
        await redisConnection.set(REDIS_KEY, JSON.stringify(fullState));

        return NextResponse.json({
            success: true,
            enabled: fullState[taskId]
        });

    } catch (error) {
        console.error('Error toggling task:', error);
        return NextResponse.json(
            { success: false, error: 'Internal Server Error' },
            { status: 500 }
        );
    }
}
