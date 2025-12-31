
import mongoose from 'mongoose';
import User from '../src/models/User';
import Role from '../src/models/Role';
import dotenv from 'dotenv';
import path from 'path';

// Fix import path resolution for ts-node
dotenv.config({ path: path.resolve(__dirname, '../.env.local') });
dotenv.config({ path: path.resolve(__dirname, '../.env') });

const MONGODB_URI = process.env.MONGODB_URI || process.env.COSMOS_CONNECTION_STRING;

async function migrateRoles() {
    if (!MONGODB_URI) {
        console.error('No MONGODB_URI found');
        process.exit(1);
    }

    await mongoose.connect(MONGODB_URI);
    console.log('Connected to DB');

    // 1. Fetch new Role IDs
    const roles = await Role.find({});
    const roleMap: Record<string, string> = {};

    roles.forEach(r => {
        if (r.name === 'Partner Super Admin') roleMap['super_admin'] = r._id.toString();
        if (r.name === 'Admin') roleMap['admin'] = r._id.toString();
        if (r.name === 'User') roleMap['user'] = r._id.toString();
    });

    console.log('Role Mapping:', roleMap);

    const users = await User.find({});
    console.log(`Found ${users.length} users.`);

    for (const user of users) {
        const legacyRole = user.role;
        // Check if role is one of the legacy strings
        if (['admin', 'user', 'super_admin'].includes(legacyRole)) {
            const newRoleId = roleMap[legacyRole];
            if (newRoleId) {
                console.log(`Migrating user ${user.email}: ${legacyRole} -> ${newRoleId}`);
                user.role = newRoleId;
                await user.save();
            } else {
                console.warn(`No mapping found for role: ${legacyRole} (User: ${user.email})`);
            }
        } else {
            // Check if it looks like an ObjectId (already migrated)
            if (mongoose.Types.ObjectId.isValid(legacyRole)) {
                console.log(`Skipping ${user.email} (already looks like an ID: ${legacyRole})`);
            } else {
                console.warn(`Unknown role format for ${user.email}: ${legacyRole}`);
            }
        }
    }

    console.log('Role migration complete.');
    process.exit(0);
}

migrateRoles().catch(console.error);
