
import mongoose, { Schema, Document, Model } from 'mongoose';

// Slot Interface
interface IScheduleSlot {
    slot_id: string;
    start_time: Date;
    end_time: Date;
    activity_type: string;
    activity_config: Record<string, any>;
    priority: number;
    is_flexible: boolean;
    status: 'scheduled' | 'in_progress' | 'completed' | 'failed' | 'skipped';
    execution_log: string[];
}

// Daily Schedule Interface
export interface IDailySchedule extends Document {
    date: string; // YYYY-MM-DD
    slots: IScheduleSlot[];
    strategy_focus: string;
    daily_goals: Record<string, any>;
    performance_targets: Record<string, number>;
    completion_rate: number;
    total_activities: number;
    createdAt: Date;
    updatedAt: Date;
}

const ScheduleSlotSchema = new Schema<IScheduleSlot>({
    slot_id: { type: String, required: true },
    start_time: { type: Date, required: true },
    end_time: { type: Date, required: true },
    activity_type: { type: String, required: true },
    activity_config: { type: Schema.Types.Mixed, default: {} },
    priority: { type: Number, default: 1 },
    is_flexible: { type: Boolean, default: true },
    status: {
        type: String,
        enum: ['scheduled', 'in_progress', 'completed', 'failed', 'skipped'],
        default: 'scheduled'
    },
    execution_log: [{ type: String }]
}, { _id: false }); // Subdocument, no ID needed explicitly if slot_id is used

const DailyScheduleSchema = new Schema<IDailySchedule>(
    {
        date: { type: String, required: true, unique: true, index: true },
        slots: [ScheduleSlotSchema],
        strategy_focus: { type: String },
        daily_goals: { type: Schema.Types.Mixed, default: {} },
        performance_targets: { type: Map, of: Number, default: {} },
        completion_rate: { type: Number, default: 0.0 },
        total_activities: { type: Number, default: 0 }
    },
    { timestamps: true, collection: 'daily_schedules' }
);

export default mongoose.models.DailySchedule || mongoose.model<IDailySchedule>('DailySchedule', DailyScheduleSchema);
