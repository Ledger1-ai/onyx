
import mongoose, { Schema, Document, Model } from 'mongoose';

export interface IUser extends Document {
    email: string;
    passwordHash: string;
    name: string;
    role: 'admin' | 'user' | 'super_admin';
    teamId?: string; // Reference to Team
    createdAt: Date;
    updatedAt: Date;
}

const UserSchema: Schema = new Schema(
    {
        email: { type: String, required: true, unique: true, index: true },
        passwordHash: { type: String, required: true },
        name: { type: String, required: true },
        role: { type: String }, // Storing Role ID now. (Legacy users have string 'admin'/'user')
        teamId: { type: String } // Storing as string ID for simplicity, could be ObjectId ref
    },
    {
        timestamps: true,
        collection: 'users'
    }
);

export default mongoose.models.User || mongoose.model<IUser>('User', UserSchema);
