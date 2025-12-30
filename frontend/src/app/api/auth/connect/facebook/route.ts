import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
    const META_APP_ID = process.env.META_APP_ID;
    const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

    if (!META_APP_ID) {
        return NextResponse.json({ error: "Missing META_APP_ID" }, { status: 500 });
    }

    const params = new URLSearchParams({
        client_id: META_APP_ID,
        redirect_uri: `${BASE_URL}/api/auth/callback/facebook`,
        scope: "pages_show_list,pages_read_engagement,pages_manage_posts,pages_manage_engagement,pages_messaging,instagram_basic,instagram_content_publish,instagram_manage_comments,instagram_manage_messages",
        state: "random_state_string_TODO_secure", // In production use a secure random string tied to session
        response_type: "code"
    });

    const url = `https://www.facebook.com/v19.0/dialog/oauth?${params.toString()}`;

    return NextResponse.redirect(url);
}
