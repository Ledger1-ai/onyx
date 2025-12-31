
import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import User from '@/models/User';
import { cookies } from 'next/headers';
import bcrypt from 'bcryptjs';

export async function POST(req: Request) {
    try {
        await connectDB();
        const body = await req.json();
        const { email, password } = body;

        if (!email || !password) {
            return NextResponse.json({ success: false, error: 'Identity and Key required.' }, { status: 400 });
        }

        const user = await User.findOne({ email });

        // Secure bcrypt check
        // Check if user exists AND if password matches
        const isValid = user && await bcrypt.compare(password, user.passwordHash);

        if (!isValid) {
            return NextResponse.json({ success: false, error: 'Invalid credentials.' }, { status: 401 });
        }

        // Create Session Cookie
        // Simple JSON payload for now, typically this would be a signed JWT
        const sessionPayload = JSON.stringify({
            id: user._id,
            email: user.email,
            role: user.role,
            name: user.name
        });

        // Set Cookie
        (await cookies()).set({
            name: 'auth_token',
            value: Buffer.from(sessionPayload).toString('base64'),
            httpOnly: true,
            path: '/',
            secure: process.env.NODE_ENV === 'production',
            maxAge: 60 * 60 * 24 * 7 // 7 Days
        });

        return NextResponse.json({
            success: true,
            user: {
                name: user.name,
                role: user.role,
                teamId: user.teamId
            }
        });

    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}
