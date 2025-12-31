
import mongoose from 'mongoose';
import User from '../src/models/User';
import bcrypt from 'bcryptjs';
import dotenv from 'dotenv';
import path from 'path';

// Load env from frontend root
dotenv.config({ path: path.resolve(__dirname, '../.env.local') });
dotenv.config({ path: path.resolve(__dirname, '../.env') });

const MONGODB_URI = process.env.MONGODB_URI || process.env.COSMOS_CONNECTION_STRING;

async function migrate() {
    if (!MONGODB_URI) {
        console.error('No MONGODB_URI found');
        process.exit(1);
    }

    await mongoose.connect(MONGODB_URI);
    console.log('Connected to DB');

    const users = await User.find({});
    console.log(`Found ${users.length} users.`);

    for (const user of users) {
        // Check if already hashed (bcrypt hashes are 60 chars long and start with $2)
        if (user.passwordHash && !user.passwordHash.startsWith('$2')) {
            console.log(`Migrating user: ${user.email}`);
            const hashedPassword = await bcrypt.hash(user.passwordHash, 10);
            user.passwordHash = hashedPassword;
            await user.save();
            console.log('Saved.');
        } else {
            console.log(`Skipping ${user.email} (already hashed or empty)`);
        }
    }

    console.log('Migration complete.');
    process.exit(0);
}

migrate().catch(console.error);
