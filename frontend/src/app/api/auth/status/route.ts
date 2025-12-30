import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({
        twitter: true,
        linkedin: false,
        meta: false
    });
}
