import React from 'react';
import { Clock } from 'lucide-react';

interface StrategyProps {
    data: {
        name: string;
        description: string;
        activity_distribution: Record<string, number>;
        optimal_posting_times: string[];
    } | null;
}

export default function StrategyOverview({ data }: StrategyProps) {
    if (!data) return null;

    const { name, description, activity_distribution, optimal_posting_times } = data;

    // Helper to format activity keys to readable text
    const formatActivity = (key: string) => {
        return key
            .replace('LINKEDIN_', '')
            .replace('FACEBOOK_', '')
            .replace('INSTAGRAM_', '')
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    const getPlatformActivities = (platform_prefix: string[]) => {
        return Object.entries(activity_distribution || {})
            .filter(([key]) => {
                const upperKey = key.toUpperCase();
                // Check if it matches any prefix
                const isMatch = platform_prefix.some(p => upperKey.includes(p));
                // Special case for Twitter which has no prefix usually vs others
                if (platform_prefix.includes('TWITTER_CORE')) {
                    return !upperKey.includes('LINKEDIN') &&
                        !upperKey.includes('FACEBOOK') &&
                        !upperKey.includes('INSTAGRAM') &&
                        !upperKey.includes('IG_') &&
                        !upperKey.includes('FB_');
                }
                return isMatch;
            })
            .sort(([, a], [, b]) => b - a);
    };

    const twitterActivities = getPlatformActivities(['TWITTER_CORE']);
    const linkedinActivities = getPlatformActivities(['LINKEDIN']);
    const facebookActivities = getPlatformActivities(['FACEBOOK', 'FB_']);
    const instagramActivities = getPlatformActivities(['INSTAGRAM', 'IG_']);

    const renderActivityColumn = (title: string, activities: [string, number][], colorClass: string) => (
        <div className="flex flex-col space-y-2">
            <h5 className={`text-[10px] font-bold ${colorClass} uppercase tracking-wider border-b border-gray-700/50 pb-1 mb-1`}>
                {title}
            </h5>
            {activities.length > 0 ? (
                activities.map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center text-[10px] group hover:bg-white/5 p-1 rounded transition-colors">
                        <span className="text-gray-400 truncate pr-2 max-w-20" title={formatActivity(key)}>{formatActivity(key)}</span>
                        <span className="text-gray-500 font-mono">{Math.round(value * 100)}%</span>
                    </div>
                ))
            ) : (
                <span className="text-[10px] text-gray-600 italic p-1">No active tasks</span>
            )}
        </div>
    );

    return (
        <div className="glass-panel p-4 mb-3 widget-fixed">
            <h3 className="text-lg font-bold text-white mb-2 font-orbitron flex items-center uppercase glow-text-white">
                Strategy Overview
            </h3>

            <div className="mb-4">
                <h4 className="text-sm font-bold text-cyan-400 uppercase tracking-wider mb-1">
                    {name || "BALANCED GROWTH"}
                </h4>
                <p className="text-xs text-gray-400">
                    {description || "A balanced approach focusing on engagement and content quality"}
                </p>
            </div>

            <div className="mb-4">
                {/* 4-column layout for platform distributions */}
                <div className="grid grid-cols-4 gap-2">
                    {renderActivityColumn('Twitter/X', twitterActivities, 'text-cyan-400')}
                    {renderActivityColumn('LinkedIn', linkedinActivities, 'text-blue-400')}
                    {renderActivityColumn('Facebook', facebookActivities, 'text-indigo-400')}
                    {renderActivityColumn('Instagram', instagramActivities, 'text-pink-400')}
                </div>
            </div>

            <div className="mt-auto pt-3 border-t border-gray-800/50">
                <div className="flex items-center mb-2">
                    <Clock className="w-3 h-3 text-gray-500 mr-2" />
                    <h5 className="text-xs text-gray-500 font-orbitron uppercase tracking-wider">Optimal Posting Times</h5>
                </div>
                <div className="flex flex-wrap gap-2">
                    {(optimal_posting_times || []).map((time) => (
                        <div key={time} className="px-3 py-1.5 rounded-lg bg-black/40 border border-gray-800 text-xs text-brand-cyan/80 font-mono shadow-[0_0_10px_rgba(0,0,0,0.3)]">
                            {time}
                        </div>
                    ))}
                    {(optimal_posting_times || []).length === 0 && (
                        <span className="text-xs text-gray-600 italic">AI analyzing best times...</span>
                    )}
                </div>
            </div>
        </div>
    );
}
