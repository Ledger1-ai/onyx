"use client";

import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Twitter, BarChart, Linkedin, FileText, Activity } from 'lucide-react';

interface AccountStatsProps {
    platform?: string;
}

export default function AccountStats({ platform = 'twitter' }: AccountStatsProps) {
    const [stats, setStats] = useState({
        followers: 0,
        following: 0,
        posts: 0,
        impressions: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            setLoading(true);
            try {
                const response = await fetch(`/api/performance?days=7&platform=${platform}`);
                const data = await response.json();
                const summary = data.summary || {};

                setStats({
                    followers: summary.total_followers || 0,
                    following: summary.follows || 0,
                    posts: summary.posts_count || 0,
                    impressions: summary.total_impressions || 0
                });
            } catch (error) {
                console.error("Error fetching account stats:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, [platform]);

    // Platform-specific configuration
    let config;
    let extraStats: { label: string; value: string; icon: any; color: string; border: string }[] = [];

    switch (platform) {
        case 'linkedin':
            config = {
                followersLabel: 'Connections',
                postsLabel: 'Posts',
                postsIcon: FileText,
                mainIcon: Linkedin,
                mainColor: 'text-blue-500',
                mainBorder: 'border-blue-500/50'
            };
            break;
        case 'facebook':
            config = {
                followersLabel: 'Followers',
                postsLabel: 'Posts',
                postsIcon: FileText, // Or specific FB icon
                mainIcon: Users, // Or FB Icon
                mainColor: 'text-blue-600',
                mainBorder: 'border-blue-600/50'
            };
            // Add FB Specifics (Stories, Reels) matching IG
            extraStats = [
                {
                    label: 'Stories',
                    value: '0', // TODO: Fetch from backend
                    icon: Activity, // Placeholder
                    color: 'text-blue-400',
                    border: 'border-blue-500/50'
                },
                {
                    label: 'Reels',
                    value: '0', // TODO: Fetch from backend
                    icon: Activity, // Placeholder
                    color: 'text-indigo-400',
                    border: 'border-indigo-500/50'
                }
            ];
            break;
        case 'instagram':
            config = {
                followersLabel: 'Followers',
                postsLabel: 'Posts',
                postsIcon: FileText, // Or Camera
                mainIcon: Users, // Or IG Icon
                mainColor: 'text-pink-500',
                mainBorder: 'border-pink-500/50'
            };
            // Add IG Specifics (Stories, Reels)
            // Note: Backend summary might not have these yet, defaulting to 0
            extraStats = [
                {
                    label: 'Stories',
                    value: '0', // TODO: Fetch from backend
                    icon: Activity, // Placeholder
                    color: 'text-orange-400',
                    border: 'border-orange-500/50'
                },
                {
                    label: 'Reels',
                    value: '0', // TODO: Fetch from backend
                    icon: Activity, // Placeholder
                    color: 'text-pink-400',
                    border: 'border-pink-500/50'
                }
            ];
            break;
        default: // Twitter
            config = {
                followersLabel: 'Followers',
                postsLabel: 'Tweets',
                postsIcon: Twitter,
                mainIcon: Users,
                mainColor: 'text-cyan-400',
                mainBorder: 'border-cyan-500/50'
            };
    }

    const baseStats = [
        {
            label: config.followersLabel,
            value: stats.followers.toLocaleString(),
            icon: Users,
            color: config.mainColor,
            border: config.mainBorder
        },
        {
            label: 'Following',
            value: stats.following.toLocaleString(),
            icon: UserPlus,
            color: 'text-purple-400',
            border: 'border-purple-500/50'
        },
        {
            label: config.postsLabel,
            value: stats.posts.toLocaleString(),
            icon: config.postsIcon,
            color: 'text-blue-400',
            border: 'border-blue-500/50'
        },
        {
            label: 'Impressions',
            value: stats.impressions >= 1000 ? `${(stats.impressions / 1000).toFixed(1)}K` : stats.impressions.toLocaleString(),
            icon: BarChart,
            color: 'text-green-400',
            border: 'border-green-500/50'
        },
    ];

    // Combine base stats and extra stats (Stories/Reels for IG)
    // If IG, we might want to insert Stories/Reels after Posts?
    // Current User Request: "Swap out Tweets with Posts, Stories, and Reels".
    // This implies removing "Tweets" and adding those 3.
    // Base stats has "Posts" (mapped from Tweets slot).
    // So we just append Stories/Reels? 
    // Or if "Swap out Tweets..." implies that singular slot becomes 3 slots?
    // Resulting list: Followers, Following, Posts, Stories, Reels, Impressions.

    // Let's insert extraStats before Impressions
    const statItems = [...baseStats];
    if (extraStats.length > 0) {
        // Insert at index 3 (before Impressions which is last)
        statItems.splice(3, 0, ...extraStats);
    }

    // Dynamic grid columns: 6 items -> 3 cols (2 rows), 4 items -> 4 cols (1 row)
    const gridCols = statItems.length > 4 ? 'md:grid-cols-3' : 'md:grid-cols-4';

    return (
        <div className={`grid grid-cols-2 ${gridCols} gap-3 mb-3`}>
            {statItems.map((stat, index) => (
                <div key={index} className={`glass-card p-3 flex flex-col items-center justify-center text-center group hover:bg-white/5 relative overflow-hidden`}>
                    {loading && <div className="absolute inset-0 bg-black/50 z-10 animate-pulse" />}
                    <stat.icon className={`w-5 h-5 mb-1 ${stat.color} opacity-80 group-hover:opacity-100 group-hover:scale-110 transition-all`} />
                    <span className="text-lg font-bold text-white font-orbitron">{stat.value}</span>
                    <span className="text-[10px] text-gray-500 uppercase tracking-widest">{stat.label}</span>
                </div>
            ))}
        </div>
    );
}
