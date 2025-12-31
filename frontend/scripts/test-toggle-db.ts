
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });
dotenv.config();

import { connectDB } from '../src/lib/db';
import Setting from '../src/models/Setting';
import mongoose from 'mongoose';

const KEY = 'task:configuration';

async function testToggle() {
    try {
        console.log('🔄 Connecting to DB...');
        await connectDB();
        console.log('✅ Connected.');

        // 1. Find
        console.log('🔍 Finding setting...');
        const setting = await Setting.findOne({ key: KEY });
        console.log('📄 Current Value:', setting?.value);

        // 2. Prepare Update
        const updates = { 'TEST_TASK': true };

        // 3. Update
        console.log('💾 Updating setting...');
        const result = await Setting.findOneAndUpdate(
            { key: KEY },
            { value: updates },
            { upsert: true, new: true } // Added new: true to see result
        );
        console.log('✅ Update Result:', result?.value);

        process.exit(0);
    } catch (error) {
        console.error('❌ Failed:', error);
        process.exit(1);
    }
}

testToggle();
