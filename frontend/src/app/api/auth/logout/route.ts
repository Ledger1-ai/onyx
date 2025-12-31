
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function POST() {
    try {
        const cookieStore = await cookies();
        cookieStore.delete('auth_token');
        return NextResponse.json({ success: true, message: 'Logged out' });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: 'Failed to logout' }, { status: 500 });
    }
}
