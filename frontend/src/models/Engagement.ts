
import mongoose, { Schema, Document, Model } from 'mongoose';

export interface IEngagementSession extends Document {
    session_id: string;
    start_time: Date;
    end_time?: Date;
    activity_type: string;
    accounts_engaged: string[];
    interactions_made: Record<string, number>; // { like: 5, reply: 2 }
    topics_engaged: string[];
    engagement_quality_score: number;
    session_notes?: string;
    createdAt: Date;
    updatedAt: Date;
}

const EngagementSessionSchema = new Schema<IEngagementSession>(
    {
        session_id: { type: String, required: true, unique: true, index: true },
        start_time: { type: Date, required: true },
        end_time: { type: Date },
        activity_type: { type: String, required: true }, // e.g., 'scroll_engage', 'search_engage'
        accounts_engaged: [{ type: String }], // List of usernames or IDs
        interactions_made: { type: Map, of: Number, default: {} },
        topics_engaged: [{ type: String }],
        engagement_quality_score: { type: Number, default: 0.0 },
        session_notes: { type: String }
    },
    { timestamps: true, collection: 'engagement_sessions' }
);

export default mongoose.models.EngagementSession || mongoose.model<IEngagementSession>('EngagementSession', EngagementSessionSchema);
