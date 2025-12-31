import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Setting from '@/models/Setting';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
    const { searchParams } = new URL(req.url);
    const code = searchParams.get('code');
    const error = searchParams.get('error');

    if (error || !code) {
        return NextResponse.json({ error: error || "No code provided" }, { status: 400 });
    }

    const META_APP_ID = process.env.META_APP_ID;
    const META_APP_SECRET = process.env.META_APP_SECRET;
    const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
    const REDIRECT_URI = `${BASE_URL}/api/auth/callback/facebook`;

    if (!META_APP_ID || !META_APP_SECRET) {
        return NextResponse.json({ error: "Missing Meta Configuration" }, { status: 500 });
    }

    try {
        // 1. Exchange Code for Short-Lived Token
        const tokenRes = await fetch(`https://graph.facebook.com/v19.0/oauth/access_token?client_id=${META_APP_ID}&redirect_uri=${REDIRECT_URI}&client_secret=${META_APP_SECRET}&code=${code}`);
        const tokenData = await tokenRes.json();

        if (tokenData.error) {
            throw new Error(tokenData.error.message);
        }

        const shortToken = tokenData.access_token;

        // 2. Exchange Short-Lived Token for Long-Lived Token
        const exchangeRes = await fetch(`https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id=${META_APP_ID}&client_secret=${META_APP_SECRET}&fb_exchange_token=${shortToken}`);
        const exchangeData = await exchangeRes.json();

        const longToken = exchangeData.access_token || shortToken;

        // 3. Get User Details
        const meRes = await fetch(`https://graph.facebook.com/me?access_token=${longToken}`);
        const meData = await meRes.json();

        // 4. Save to MongoDB
        await connectDB();
        await Setting.findOneAndUpdate(
            { key: 'auth:meta' },
            {
                value: {
                    access_token: longToken,
                    user_id: meData.id,
                    name: meData.name,
                    updated_at: new Date().toISOString()
                }
            },
            { upsert: true, new: true }
        );

        // Also update legacy format if needed, but 'task:configuration' drives generation.
        // We might want to set a flag that 'meta' is active.
        // For now, redirect to dashboard.

        return NextResponse.redirect(`${BASE_URL}/underworld/dashboard`); // Or wherever the dashboard is

    } catch (e: any) {
        console.error("Meta Auth Error:", e);
        return NextResponse.json({ error: e.message }, { status: 500 });
    }
}
