import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Setting from '@/models/Setting';

const DEFAULT_TASKS = [
    // Twitter - Core
    { id: 'TWITTER_TWEET_DAILY', name: 'Daily Tweet Generation', enabled: true },
    { id: 'TWITTER_REPLY_MENTIONS', name: 'Auto-Reply to Mentions', enabled: true },
    { id: 'TWITTER_ENGAGE_TIMELINE', name: 'Timeline Engagement', enabled: true },
    { id: 'TWITTER_CONTENT_CURATION', name: 'Content Curation', enabled: false },

    // Twitter - Growth
    { id: 'TWITTER_FOLLOW_TARGETS', name: 'Auto-Follow Target Audience', enabled: false },
    { id: 'TWITTER_LIKE_KEYWORD', name: 'Like Tweets by Keyword', enabled: true },
    { id: 'TWITTER_RETWEET_PARTNERS', name: 'Retweet Partners', enabled: false },

    // Twitter - Monitoring
    { id: 'TWITTER_MONITOR_TRENDS', name: 'Trend Monitoring', enabled: true },
    { id: 'TWITTER_PERFORMANCE_CHECK', name: 'Performance Analysis', enabled: true },

    // LinkedIn - Phase 2 (The Professional)
    { id: 'linkedin_post', name: 'Post Content (Text/Image/Video)', enabled: true },
    { id: 'linkedin_thread', name: 'Post Articles', enabled: true },
    { id: 'linkedin_engage', name: 'Feed Engagement', enabled: true },
    { id: 'linkedin_search_engage', name: 'Search & Engage (Risky)', enabled: false },
    { id: 'linkedin_connect', name: 'Network Growth (Connect)', enabled: true },
    { id: 'linkedin_monitor', name: 'Monitor Notifications', enabled: true },
    { id: 'linkedin_analytics', name: 'Scrape Analytics', enabled: true },

    // Meta (API) - Phase 3
    { id: 'meta_facebook_post', name: 'Facebook Page Post', enabled: true },
    { id: 'meta_instagram_post', name: 'Instagram Feed Post', enabled: true },
    { id: 'meta_engage', name: 'Auto-Reply to Comments', enabled: true },
    { id: 'meta_analytics', name: 'Fetch Page Insights', enabled: true },
    { id: 'meta_view_stories', name: 'Watch Stories (FB/IG)', enabled: true },
    { id: 'meta_view_reels', name: 'Watch Reels (FB/IG)', enabled: true },

    // System
    { id: 'SYSTEM_HEALTH_CHECK', name: 'System Health Monitoring', enabled: true },
    { id: 'SYSTEM_BACKUP_DAILY', name: 'Daily Backup', enabled: true }
];

export async function GET() {
    try {
        await connectDB();
        // Fetch enabled states from MongoDB
        const setting = await Setting.findOne({ key: 'task:configuration' });

        let finalTasks = DEFAULT_TASKS;

        if (setting && setting.value) {
            const configMap = setting.value;
            // innovative merge: use defaults for definition, but override enabled status from DB
            finalTasks = DEFAULT_TASKS.map(task => ({
                ...task,
                enabled: configMap[task.id] !== undefined ? configMap[task.id] : task.enabled
            }));
        }

        return NextResponse.json({
            success: true,
            tasks: finalTasks
        });
    } catch (error) {
        console.error('Failed to fetch config:', error);
        // Fallback to defaults on error
        return NextResponse.json({
            success: true,
            tasks: DEFAULT_TASKS
        });
    }
}
