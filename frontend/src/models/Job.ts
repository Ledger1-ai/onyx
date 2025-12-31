import mongoose, { Schema, Document, Model } from 'mongoose';

export interface IJob extends Document {
    type: string;
    data: any;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    result?: any;
    error?: string;
    priority: number;
    createdAt: Date;
    updatedAt: Date;
    processedAt?: Date;
}

const JobSchema: Schema = new Schema(
    {
        type: { type: String, required: true, index: true },
        data: { type: Schema.Types.Mixed, default: {} },
        status: {
            type: String,
            enum: ['pending', 'processing', 'completed', 'failed'],
            default: 'pending',
            index: true
        },
        priority: { type: Number, default: 0, index: true },
        result: { type: Schema.Types.Mixed },
        error: { type: String },
        processedAt: { type: Date }
    },
    {
        timestamps: true,
        collection: 'jobs'
    }
);

// Indexes for polling performance
JobSchema.index({ status: 1, priority: -1, createdAt: 1 });

// Prevent overwrite in dev
const Job: Model<IJob> = mongoose.models.Job || mongoose.model<IJob>('Job', JobSchema);

export default Job;
