import { NextResponse } from 'next/server';
import { redisConnection } from '@/lib/queue';

const DEFAULT_IDENTITY = {
    user_id: 'default_tenant',
    company_logo_path: '',
    company_config: {
        name: 'My Company',
        industry: 'Tech',
        mission: 'To innovate.',
        brand_colors: { primary: '#000000', secondary: '#ffffff' },
        twitter_username: '@mycompany',
        company_logo_path: '',
        values: ['Innovation', 'Integrity'],
        focus_areas: ['AI', 'Automation'],
        brand_voice: 'Professional',
        target_audience: 'Developers',
        key_products: ['Anubis'],
        competitive_advantages: ['Speed'],
        location: 'Global',
        contact_info: {},
        business_model: 'SaaS',
        core_philosophy: 'Code is law.',
        subsidiaries: [],
        partner_categories: []
    },
    personality_config: {
        tone: 'Helpful',
        engagement_style: 'Proactive',
        communication_style: 'Clear',
        hashtag_strategy: 'Minimal',
        content_themes: ['Tech', 'Coding'],
        posting_frequency: 'Daily'
    }
};

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('user_id') || 'default_tenant';

    try {
        const data = await redisConnection.get(`identity:${userId}`);
        if (data) {
            return NextResponse.json({ identity: JSON.parse(data) });
        } else {
            return NextResponse.json({ identity: DEFAULT_IDENTITY });
        }
    } catch (error) {
        return NextResponse.json({ identity: DEFAULT_IDENTITY }); // Fallback
    }
}

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const userId = body.user_id || 'default_tenant';

        await redisConnection.set(`identity:${userId}`, JSON.stringify(body.identity));

        return NextResponse.json({ success: true });
    } catch (error) {
        return NextResponse.json({ success: false, error: 'Failed to save identity' }, { status: 500 });
    }
}
