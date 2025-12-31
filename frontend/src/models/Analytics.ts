
import mongoose, { Schema, Document, Model } from 'mongoose';

// --- Interfaces ---

export interface IAccountAnalytics extends Document {
    date: string; // YYYY-MM-DD
    time_range: string; // 7D, 2W, etc.
    platform: 'twitter' | 'linkedin' | 'facebook' | 'instagram';
    verified_followers: number;
    total_followers: number;
    impressions: number;
    engagements: number;
    engagement_rate: number;
    profile_visits: number;
    replies: number;
    likes: number;
    reposts: number;
    bookmarks: number;
    shares: number;
    follows: number;
    unfollows: number;
    posts_count: number;
    replies_count: number;
    createdAt: Date;
    updatedAt: Date;
}

export interface IContentPerformance extends Document {
    content_id: string; // tweet_id or post_id
    platform: 'twitter' | 'linkedin' | 'facebook' | 'instagram';
    content_type: 'text' | 'image' | 'video' | 'poll';
    posting_time?: Date;
    metrics: Record<string, any>; // Flexible for platform specific
    engagement_data: {
        likes: number;
        retweets: number;
        replies: number;
        impressions: number;
        clicks: number;
        profile_visits: number;
        follows: number;
        reach: number;
        save_rate?: number;
        share_rate?: number;
    };
    hashtags: string[];
    mentions: string[];
    audience_reached?: number;
    demographics?: Record<string, any>;
    sentiment_score?: number;
    virality_score?: number;
    createdAt: Date;
    updatedAt: Date;
}

// --- Schemas ---

const AccountAnalyticsSchema = new Schema<IAccountAnalytics>(
    {
        date: { type: String, required: true, index: true },
        time_range: { type: String, default: '7D' },
        platform: { type: String, required: true, index: true },
        verified_followers: { type: Number, default: 0 },
        total_followers: { type: Number, default: 0 },
        impressions: { type: Number, default: 0 },
        engagements: { type: Number, default: 0 },
        engagement_rate: { type: Number, default: 0 },
        profile_visits: { type: Number, default: 0 },
        replies: { type: Number, default: 0 },
        likes: { type: Number, default: 0 },
        reposts: { type: Number, default: 0 },
        bookmarks: { type: Number, default: 0 },
        shares: { type: Number, default: 0 },
        follows: { type: Number, default: 0 },
        unfollows: { type: Number, default: 0 },
        posts_count: { type: Number, default: 0 },
        replies_count: { type: Number, default: 0 }
    },
    { timestamps: true, collection: 'account_analytics' }
);

// Compound index for quick lookups
AccountAnalyticsSchema.index({ date: -1, platform: 1 }, { unique: true });

const ContentPerformanceSchema = new Schema<IContentPerformance>(
    {
        content_id: { type: String, required: true, unique: true, index: true },
        platform: { type: String, required: true, index: true },
        content_type: { type: String, default: 'text' },
        posting_time: { type: Date },
        metrics: { type: Schema.Types.Mixed, default: {} },
        engagement_data: {
            likes: { type: Number, default: 0 },
            retweets: { type: Number, default: 0 },
            replies: { type: Number, default: 0 },
            impressions: { type: Number, default: 0 },
            clicks: { type: Number, default: 0 },
            profile_visits: { type: Number, default: 0 },
            follows: { type: Number, default: 0 },
            reach: { type: Number, default: 0 },
            save_rate: { type: Number, default: 0 },
            share_rate: { type: Number, default: 0 }
        },
        hashtags: [{ type: String }],
        mentions: [{ type: String }],
        audience_reached: { type: Number, default: 0 },
        demographics: { type: Schema.Types.Mixed, default: {} },
        sentiment_score: { type: Number, default: 0 },
        virality_score: { type: Number, default: 0 }
    },
    { timestamps: true, collection: 'tweet_performance' } // Naming content_performance generally, or match legacy 'tweet_performance'
);

// --- Models ---

export const AccountAnalytics = mongoose.models.AccountAnalytics || mongoose.model<IAccountAnalytics>('AccountAnalytics', AccountAnalyticsSchema);
export const ContentPerformance = mongoose.models.ContentPerformance || mongoose.model<IContentPerformance>('ContentPerformance', ContentPerformanceSchema);
