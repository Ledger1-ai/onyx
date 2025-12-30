"use client";

import React, { useState } from 'react';
import { Users, BarChart2, Eye, Share2, Calendar, Filter } from 'lucide-react';
import { GrowthLineChart, EngagementBarChart, ActivityPieChart } from '@/components/Analytics/AnalyticsCharts';

// Mock Data for Visualization - To be replaced with real API calls later
const MOCK_DATA = {
    twitter: {
        growth: { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], followers: [1200, 1205, 1215, 1230, 1245, 1250, 1265] },
        engagement: { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], likes: [45, 52, 38, 65, 48, 60, 75], replies: [12, 15, 8, 22, 14, 18, 25] },
        activity: { labels: ['Tweets', 'Replies', 'Likes', 'Retweets'], values: [15, 45, 120, 10] },
        stats: { followers: 1265, engagementRate: '4.2%', reach: '12.5k', impressions: '45k' }
    },
    meta: {
        growth: { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], followers: [800, 802, 805, 810, 812, 815, 820] },
        engagement: { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], likes: [20, 25, 22, 30, 28, 35, 40], replies: [5, 8, 6, 10, 7, 12, 15] },
        activity: { labels: ['Posts', 'Stories', 'Reels', 'Comments'], values: [5, 12, 3, 25] },
        stats: { followers: 820, engagementRate: '3.8%', reach: '5.2k', impressions: '18k' }
    },
    linkedin: {
        growth: { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], followers: [450, 452, 455, 458, 460, 462, 465] },
        engagement: { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], likes: [10, 12, 15, 18, 20, 15, 22], replies: [2, 4, 3, 5, 6, 4, 8] },
        activity: { labels: ['Posts', 'Comments', 'Connections'], values: [3, 20, 15] },
        stats: { followers: 465, engagementRate: '2.5%', reach: '1.8k', impressions: '5.5k' }
    }
};

export default function AnalyticsPage() {
    const [platform, setPlatform] = useState<'twitter' | 'meta' | 'linkedin'>('twitter');
    const data = MOCK_DATA[platform];

    return (
        <div className="min-h-screen p-6 pb-32">
            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-2xl font-bold font-orbitron text-white glitch-text">ANALYTICS // DEEP DIVE</h1>
                    <p className="text-gray-400 text-sm">Historical performance and strategic insights.</p>
                </div>

                <div className="flex gap-2">
                    <div className="glass-panel px-3 py-1.5 flex items-center gap-2 rounded text-sm text-cyan-400">
                        <Calendar className="w-4 h-4" />
                        <span>Last 7 Days</span>
                    </div>

                    {/* Platform Filter */}
                    <div className="glass-panel p-1 flex rounded">
                        {(['twitter', 'meta', 'linkedin'] as const).map((p) => (
                            <button
                                key={p}
                                onClick={() => setPlatform(p)}
                                className={`px-3 py-1.5 rounded text-xs font-bold uppercase transition-all ${platform === p
                                        ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
                                        : 'text-gray-500 hover:text-white'
                                    }`}
                            >
                                {p}
                            </button>
                        ))}
                    </div>
                </div>
            </header>

            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <StatsCard title="Total Followers" value={data.stats.followers.toString()} icon={<Users className="w-5 h-5 text-cyan-400" />} />
                <StatsCard title="Engagement Rate" value={data.stats.engagementRate} icon={<BarChart2 className="w-5 h-5 text-purple-400" />} />
                <StatsCard title="Est. Reach" value={data.stats.reach} icon={<Share2 className="w-5 h-5 text-green-400" />} />
                <StatsCard title="Impressions" value={data.stats.impressions} icon={<Eye className="w-5 h-5 text-yellow-400" />} />
            </div>

            {/* Main Charts Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <div className="lg:col-span-2 glass-card p-4 min-h-[300px]">
                    <h3 className="text-sm font-bold text-gray-400 mb-4 font-orbitron">AUDIENCE GROWTH</h3>
                    <div className="h-[250px]">
                        <GrowthLineChart data={data.growth} />
                    </div>
                </div>
                <div className="glass-card p-4 min-h-[300px]">
                    <h3 className="text-sm font-bold text-gray-400 mb-4 font-orbitron">ACTIVITY BREAKDOWN</h3>
                    <div className="h-[250px] flex items-center justify-center">
                        <ActivityPieChart data={data.activity} />
                    </div>
                </div>
            </div>

            {/* Secondary Charts */}
            <div className="glass-card p-4 mb-8">
                <h3 className="text-sm font-bold text-gray-400 mb-4 font-orbitron">ENGAGEMENT VELOCITY</h3>
                <div className="h-[250px]">
                    <EngagementBarChart data={data.engagement} />
                </div>
            </div>

            {/* Top Content Table */}
            <div className="glass-card p-4">
                <h3 className="text-sm font-bold text-gray-400 mb-4 font-orbitron">TOP PERFORMING CONTENT</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-400">
                        <thead className="bg-white/5 text-xs uppercase font-bold text-gray-300">
                            <tr>
                                <th className="p-3">Content</th>
                                <th className="p-3">Type</th>
                                <th className="p-3">Likes</th>
                                <th className="p-3">Replies</th>
                                <th className="p-3">Score</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {[1, 2, 3].map((i) => (
                                <tr key={i} className="hover:bg-white/5 transition-colors">
                                    <td className="p-3 truncate max-w-[200px]">
                                        {platform === 'twitter' ? 'Thoughts on AI agents in 2025...' : 'New product launch video...'}
                                    </td>
                                    <td className="p-3">
                                        <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-[10px] uppercase">
                                            Post
                                        </span>
                                    </td>
                                    <td className="p-3">45</td>
                                    <td className="p-3">12</td>
                                    <td className="p-3 text-green-400 font-bold">98/100</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

function StatsCard({ title, value, icon }: { title: string, value: string, icon: React.ReactNode }) {
    return (
        <div className="glass-card p-4 flex items-center justify-between group hover:border-cyan-500/30 transition-colors">
            <div>
                <p className="text-xs text-gray-500 font-orbitron uppercase mb-1">{title}</p>
                <p className="text-2xl font-bold text-white group-hover:text-cyan-400 transition-colors">{value}</p>
            </div>
            <div className="p-3 rounded-lg bg-white/5 group-hover:bg-cyan-500/10 transition-colors">
                {icon}
            </div>
        </div>
    );
}
