
import mongoose, { Schema, Document } from 'mongoose';

export const PERMISSIONS = {
    // User Management
    USERS_READ: 'users:read',
    USERS_CREATE: 'users:create',
    USERS_EDIT: 'users:edit',
    USERS_DELETE: 'users:delete',

    // Team Management
    TEAMS_READ: 'teams:read',
    TEAMS_CREATE: 'teams:create',
    TEAMS_EDIT: 'teams:edit',
    TEAMS_DELETE: 'teams:delete',

    // Role Management
    ROLES_MANAGE: 'roles:manage', // Create/Edit/Delete Roles

    // System
    SYSTEM_ACCESS_ALL: 'system:access_all_data' // Global data access
};

export interface IRole extends Document {
    name: string;
    description?: string;
    permissions: string[];
    isSystem: boolean; // If true, cannot be deleted (e.g. Super Admin)
    createdAt: Date;
    updatedAt: Date;
}

const RoleSchema: Schema = new Schema(
    {
        name: { type: String, required: true, unique: true },
        description: { type: String },
        permissions: { type: [String], default: [] },
        isSystem: { type: Boolean, default: false }
    },
    {
        timestamps: true,
        collection: 'roles'
    }
);

// Prevent re-compilation
export default mongoose.models.Role || mongoose.model<IRole>('Role', RoleSchema);
