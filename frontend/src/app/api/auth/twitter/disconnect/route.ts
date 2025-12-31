
import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import path from 'path';
import fs from 'fs';
import { logger } from '@/worker/utils/logger';

export async function POST(request: Request) {
    try {
        // 1. Authenticate User
        const user = await getCurrentUser();
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const userId = user._id.toString();
        const profileName = `${userId}_twitter`;

        // Construct path: sibling to 'frontend' folder, i.e., ../browser_profiles
        // Note: verify if process.cwd() is project root
        const browserProfilesDir = path.resolve(process.cwd(), '../browser_profiles');
        const profileDir = path.join(browserProfilesDir, profileName);

        if (fs.existsSync(profileDir)) {
            logger.info(`Disconnecting Twitter for user ${userId}: Removing profile at ${profileDir}`);

            // Retries for file locking issues (common with browser profiles)
            try {
                fs.rmSync(profileDir, { recursive: true, force: true });
            } catch (err: any) {
                // If permission error (EBUSY), maybe browser is still running?
                // Ideally we should ensure browser is closed first, but for MVP just try removing.
                logger.error(`Failed to remove profile directory: ${err.message}`);
                return NextResponse.json({ error: 'Failed to clear session. Browser might be active.' }, { status: 500 });
            }

            return NextResponse.json({ success: true, message: 'Twitter disconnected successfully' });
        } else {
            return NextResponse.json({ success: true, message: 'No active session found to disconnect' });
        }

    } catch (error: any) {
        console.error('Error disconnecting Twitter:', error);
        return NextResponse.json(
            { error: 'Internal Server Error' },
            { status: 500 }
        );
    }
}
