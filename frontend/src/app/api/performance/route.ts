import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    // Mock data for charts
    return NextResponse.json({
        chart_data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: {
                engagement: [4.2, 4.5, 4.8, 5.1, 4.9, 5.3, 5.8],
                growth: [10, 15, 12, 20, 25, 30, 45]
            }
        },
        summary: {
            likes: 1250,
            replies: 340,
            reposts: 85,
            follows: 45,
            profile_visits: 890
        }
    });
}
