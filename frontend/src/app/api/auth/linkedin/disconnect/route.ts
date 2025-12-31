
import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import path from 'path';
import fs from 'fs';
import { logger } from '@/worker/utils/logger';

export async function POST(request: Request) {
    try {
        const user = await getCurrentUser();
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const userId = user._id.toString();
        const profileName = `${userId}_linkedin`;

        // Correct path relative to frontend/src/app/api/auth/linkedin/disconnect/
        // Actually process.cwd() is project root if run via Next.
        // Assuming standard layout: frontend/../browser_profiles
        const browserProfilesDir = path.resolve(process.cwd(), '../browser_profiles');
        const profileDir = path.join(browserProfilesDir, profileName);

        if (fs.existsSync(profileDir)) {
            logger.info(`Disconnecting LinkedIn for user ${userId}: Removing profile at ${profileDir}`);

            try {
                fs.rmSync(profileDir, { recursive: true, force: true });
            } catch (err: any) {
                logger.error(`Failed to remove LinkedIn profile directory: ${err.message}`);
                return NextResponse.json({ error: 'Failed to clear session. Browser might be active.' }, { status: 500 });
            }

            return NextResponse.json({ success: true, message: 'LinkedIn disconnected successfully' });
        } else {
            return NextResponse.json({ success: true, message: 'No active session found to disconnect' });
        }

    } catch (error: any) {
        console.error('Error disconnecting LinkedIn:', error);
        return NextResponse.json(
            { error: 'Internal Server Error' },
            { status: 500 }
        );
    }
}
