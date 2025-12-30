"use client";

import React from 'react';
import { Brain, Rocket, Activity, Trophy } from 'lucide-react';

interface StatusData {
    current_activity?: {
        activity: string;
        progress: number;
        end_time?: string;
    };
    next_activity?: {
        activity: string;
        time_until: string;
    };
    daily_progress: number;
    completed_activities: number;
    total_activities: number;
    performance_metrics?: {
        summary?: {
            overall_score?: number;
        }
    }
}

interface StatusOverviewProps {
    data: StatusData | null;
}

export default function StatusOverview({ data }: StatusOverviewProps) {
    const currentActivity = data?.current_activity?.activity || "IDLE";
    const progress = data?.current_activity?.progress || 0;
    const nextActivity = data?.next_activity?.activity || "--";
    const timeUntil = data?.next_activity?.time_until || "--";
    const dailyProgress = data?.daily_progress || 0;
    const completed = data?.completed_activities || 0;
    const total = data?.total_activities || 0;
    const score = data?.performance_metrics?.summary?.overall_score || 0;

    return (
        <div className="grid grid-cols-2 gap-3 mb-3 widget-fixed">
            {/* Active Process */}
            <div className="glass-card p-3 relative group hover:border-cyan-500/50 transition-colors">
                <div className="flex justify-between items-start mb-2">
                    <div className="glass-icon-container glass-icon-blue w-8 h-8 rounded flex items-center justify-center">
                        <Brain className="w-4 h-4" />
                    </div>
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_#00ff00]"></div>
                </div>
                <p className="text-xs text-gray-400 font-orbitron uppercase tracking-wider mb-1">Active Process</p>
                <p className="text-sm font-bold text-white truncate mb-2">{currentActivity.replace('_', ' ')}</p>
                <div className="glass-progress-bar h-1.5 bg-gray-800 rounded-full overflow-hidden border border-cyan-500/20">
                    <div
                        className="h-full bg-linear-to-r from-cyan-500 to-blue-500 transition-all duration-500 relative"
                        style={{ width: `${progress}%` }}
                    >
                        <div className="absolute inset-0 bg-white/20 animate-[shimmer_2s_infinite]"></div>
                    </div>
                </div>
            </div>

            {/* Next Protocol */}
            <div className="glass-card p-3 relative group hover:border-green-500/50 transition-colors">
                <div className="flex justify-between items-start mb-2">
                    <div className="glass-icon-container glass-icon-green w-8 h-8 rounded flex items-center justify-center">
                        <Rocket className="w-4 h-4" />
                    </div>
                    <div className="text-xs text-green-400 font-mono">{timeUntil}</div>
                </div>
                <p className="text-xs text-gray-400 font-orbitron uppercase tracking-wider mb-1">Next Protocol</p>
                <p className="text-sm font-bold text-white truncate">{nextActivity.replace('_', ' ')}</p>
            </div>

            {/* Daily Progress */}
            <div className="glass-card p-3 relative group hover:border-purple-500/50 transition-colors">
                <div className="flex justify-between items-start mb-2">
                    <div className="glass-icon-container glass-icon-purple w-8 h-8 rounded flex items-center justify-center">
                        <Activity className="w-4 h-4" />
                    </div>
                    <div className="text-lg font-bold text-purple-400">{Math.round(dailyProgress)}%</div>
                </div>
                <p className="text-xs text-gray-400 font-orbitron uppercase tracking-wider mb-1">Mission Status</p>
                <p className="text-xs text-gray-300">{completed}/{total} Completed</p>
            </div>

            {/* Efficiency Score */}
            <div className="glass-card p-3 relative group hover:border-yellow-500/50 transition-colors">
                <div className="flex justify-between items-start mb-2">
                    <div className="glass-icon-container glass-icon-yellow w-8 h-8 rounded flex items-center justify-center">
                        <Trophy className="w-4 h-4" />
                    </div>
                    <div className="text-lg font-bold text-yellow-400">{score}</div>
                </div>
                <p className="text-xs text-gray-400 font-orbitron uppercase tracking-wider mb-1">Efficiency</p>
                <p className="text-xs text-yellow-500/70">OPTIMAL</p>
            </div>
        </div>
    );
}
