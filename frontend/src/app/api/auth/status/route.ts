import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Setting from '@/models/Setting';
import { getCurrentUser } from '@/lib/auth';
import path from 'path';
import fs from 'fs';

export async function GET() {
    try {
        await connectDB();
        const user = await getCurrentUser();

        // Default state if no user logged in
        if (!user) {
            return NextResponse.json({
                twitter: { api: false, bot: false },
                linkedin: { api: false, bot: false },
                facebook: { api: false },
                instagram: { api: false },
                system: true
            });
        }

        const userId = user._id.toString();
        const browserProfilesDir = path.resolve(process.cwd(), '../browser_profiles');

        // Check for physical existence of browser profiles for this user
        const twitterProfilePath = path.join(browserProfilesDir, `${userId}_twitter`);
        const linkedinProfilePath = path.join(browserProfilesDir, `${userId}_linkedin`);

        const twitterBotActive = fs.existsSync(twitterProfilePath);
        const linkedinBotActive = fs.existsSync(linkedinProfilePath);

        // Fetch specific auth settings (Legacy/Global - eventually verify per-user if we move API tokens to User model)
        // For now, API tokens might still be global or we need to decide. 
        // Assuming API tokens are still global for MVP until we migrate them to User model too.
        const [twitterAuth, linkedinAuth, metaAuth] = await Promise.all([
            Setting.findOne({ key: 'auth:twitter' }),
            Setting.findOne({ key: 'auth:linkedin' }),
            Setting.findOne({ key: 'auth:meta' })
        ]);

        return NextResponse.json({
            twitter: {
                api: !!twitterAuth?.value?.access_token,
                bot: twitterBotActive
            },
            linkedin: {
                api: !!linkedinAuth?.value?.access_token,
                bot: linkedinBotActive
            },
            facebook: {
                api: !!metaAuth?.value?.access_token
            },
            instagram: {
                api: !!metaAuth?.value?.access_token
            },
            system: true
        });
    } catch (error) {
        // Fallback for UI to not crash, but everything disabled
        return NextResponse.json({
            twitter: { api: false, bot: false },
            linkedin: { api: false, bot: false },
            meta: { api: false },
            system: true
        });
    }
}
