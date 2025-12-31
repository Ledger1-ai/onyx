
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });
dotenv.config();

import { connectDB } from '../src/lib/db';
import Setting from '../src/models/Setting';

async function dumpSettings() {
    try {
        await connectDB();
        const settings = await Setting.find({}, { key: 1, _id: 0 }); // Only fetch keys
        console.log('📝 Found Settings Keys:', settings.map(s => s.key));
        process.exit(0);
    } catch (error) {
        console.error('❌ Failed:', error);
        process.exit(1);
    }
}

dumpSettings();
