
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });
dotenv.config();

import mongoose from 'mongoose';
import { connectDB } from '../src/lib/db';
import Setting from '../src/models/Setting';
import Job from '../src/models/Job';

async function inspect() {
    try {
        console.log('🔄 Connecting...');
        await connectDB();
        console.log('✅ Connected.');

        // 1. Check current DB name
        if (mongoose.connection.db) {
            console.log(`📂 Current Database: ${mongoose.connection.db.databaseName}`);
        }

        // 2. List all databases
        const admin = mongoose.connection.db?.admin();
        if (admin) {
            const dbs = await admin.listDatabases();
            console.log('\n🗄️  All Databases:');
            dbs.databases.forEach((db: any) => console.log(` - ${db.name} (size: ${db.sizeOnDisk})`));
        }

        // 3. List collections in current DB
        if (mongoose.connection.db) {
            const collections = await mongoose.connection.db.listCollections().toArray();
            console.log(`\n📑 Collections in '${mongoose.connection.db.databaseName}':`);

            for (const col of collections) {
                const count = await mongoose.connection.db.collection(col.name).countDocuments();
                console.log(` - ${col.name}: ${count} documents`);
            }
        }

        process.exit(0);
    } catch (error) {
        console.error('❌ Failed:', error);
        process.exit(1);
    }
}

inspect();
