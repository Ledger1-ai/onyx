"use client";

import React, { useState, useEffect } from 'react';
import { Sliders, Save, Zap, Twitter, Linkedin, Facebook, Instagram } from 'lucide-react';

interface TaskFrequencyControlsProps {
    onSave?: (distribution: any, platform: string) => void;
    initialData?: any;
    afterlifeEnabled?: boolean;
}

const presets = [
    { id: 'preset-balanced', label: 'Balanced', color: 'border-cyan-500 text-cyan-500' },
    { id: 'preset-engagement', label: 'Engagement', color: 'border-green-500 text-green-500' },
    { id: 'preset-content', label: 'Content', color: 'border-orange-500 text-orange-500' },
    { id: 'preset-discovery', label: 'Discovery', color: 'border-purple-500 text-purple-500' },
];

const initialTwitterDistribution = {
    tweet: 18,
    image_tweet: 5,
    video_tweet: 2,
    thread: 2,
    scroll_engage: 30,
    search_engage: 10,
    reply: 20,
    content_creation: 10,
    radar_discovery: 3,
    performance_analysis: 0
};

const initialLinkedinDistribution = {
    linkedin_post: 10,
    linkedin_image_post: 5,
    linkedin_video_post: 2,
    linkedin_thread: 3,
    linkedin_engage: 30,
    linkedin_search_engage: 15,
    linkedin_connect: 10,
    linkedin_reply: 20,
    linkedin_content_creation: 5,
    linkedin_monitor: 0,
    linkedin_analytics: 0
};

const twitterPresets: Record<string, any> = {
    'preset-balanced': {
        tweet: 20, image_tweet: 5, video_tweet: 2, thread: 3, scroll_engage: 30, search_engage: 15, reply: 15, content_creation: 5, radar_discovery: 0, performance_analysis: 5
    },
    'preset-engagement': {
        tweet: 10, image_tweet: 5, video_tweet: 0, thread: 0, scroll_engage: 40, search_engage: 25, reply: 20, content_creation: 0, radar_discovery: 0
    },
    'preset-content': {
        tweet: 30, image_tweet: 10, video_tweet: 5, thread: 15, scroll_engage: 10, search_engage: 5, reply: 10, content_creation: 15, radar_discovery: 0
    },
    'preset-discovery': {
        tweet: 10, image_tweet: 5, video_tweet: 0, thread: 0, scroll_engage: 20, search_engage: 30, reply: 10, content_creation: 5, radar_discovery: 20
    }
};

const linkedinPresets: Record<string, any> = {
    'preset-balanced': {
        linkedin_post: 15, linkedin_image_post: 5, linkedin_video_post: 2, linkedin_thread: 3, linkedin_engage: 30, linkedin_search_engage: 15, linkedin_connect: 15, linkedin_reply: 10, linkedin_content_creation: 5, linkedin_monitor: 0, linkedin_analytics: 0
    },
    'preset-engagement': {
        linkedin_post: 5, linkedin_image_post: 0, linkedin_video_post: 0, linkedin_thread: 0, linkedin_engage: 40, linkedin_search_engage: 25, linkedin_connect: 10, linkedin_reply: 20, linkedin_content_creation: 0, linkedin_monitor: 0, linkedin_analytics: 0
    },
    'preset-content': {
        linkedin_post: 20, linkedin_image_post: 10, linkedin_video_post: 5, linkedin_thread: 20, linkedin_engage: 10, linkedin_search_engage: 5, linkedin_connect: 5, linkedin_reply: 10, linkedin_content_creation: 15, linkedin_monitor: 0, linkedin_analytics: 0
    },
    'preset-discovery': {
        linkedin_post: 5, linkedin_image_post: 0, linkedin_video_post: 0, linkedin_thread: 0, linkedin_engage: 20, linkedin_search_engage: 25, linkedin_connect: 40, linkedin_reply: 5, linkedin_content_creation: 5, linkedin_monitor: 0, linkedin_analytics: 0
    }
};

const facebookPresets: Record<string, any> = {
    'preset-balanced': { facebook_post: 30, facebook_story: 20, facebook_engage: 50 },
    'preset-engagement': { facebook_post: 10, facebook_story: 10, facebook_engage: 80 },
    'preset-content': { facebook_post: 60, facebook_story: 30, facebook_engage: 10 },
    'preset-discovery': { facebook_post: 20, facebook_story: 20, facebook_engage: 60 }
};

const instagramPresets: Record<string, any> = {
    'preset-balanced': { instagram_post: 30, instagram_story: 30, instagram_reel: 10, instagram_engage: 30 },
    'preset-engagement': { instagram_post: 10, instagram_story: 10, instagram_reel: 10, instagram_engage: 70 },
    'preset-content': { instagram_post: 40, instagram_story: 40, instagram_reel: 20, instagram_engage: 0 },
    'preset-discovery': { instagram_post: 20, instagram_story: 20, instagram_reel: 0, instagram_engage: 60 }
};

const initialFacebookDistribution = {
    facebook_post: 20,
    facebook_story: 10,
    facebook_engage: 70
};

const initialInstagramDistribution = {
    instagram_post: 20,
    instagram_story: 20,
    instagram_reel: 0,
    instagram_engage: 60
};

export default function TaskFrequencyControls({ onSave, initialData, afterlifeEnabled = false }: TaskFrequencyControlsProps) {
    const [platform, setPlatform] = useState<'twitter' | 'linkedin' | 'facebook' | 'instagram'>('twitter');

    const [twitterDist, setTwitterDist] = useState(initialTwitterDistribution);
    const [linkedinDist, setLinkedinDist] = useState(initialLinkedinDistribution);
    const [facebookDist, setFacebookDist] = useState(initialFacebookDistribution);
    const [instagramDist, setInstagramDist] = useState(initialInstagramDistribution);

    // Derived state
    const currentDist = platform === 'twitter' ? twitterDist :
        platform === 'linkedin' ? linkedinDist :
            platform === 'facebook' ? facebookDist : instagramDist;

    const setCurrentDist = platform === 'twitter' ? setTwitterDist :
        platform === 'linkedin' ? setLinkedinDist :
            platform === 'facebook' ? setFacebookDist : setInstagramDist;

    const [total, setTotal] = useState(100);

    // Sync from initialData
    useEffect(() => {
        if (initialData) {
            // Split initialData into twitter and linkedin buckets
            const newTwitter = { ...initialTwitterDistribution } as any;
            const newLinkedin = { ...initialLinkedinDistribution } as any;
            const newFacebook = { ...initialFacebookDistribution } as any;
            const newInstagram = { ...initialInstagramDistribution } as any;

            Object.entries(initialData).forEach(([k, val]: [string, any]) => {
                let numVal = val;
                if (typeof val === 'number' && val <= 1 && val > 0) numVal = Math.round(val * 100);

                if (k.startsWith('linkedin_')) {
                    if (k in newLinkedin) newLinkedin[k] = numVal;
                } else if (k.startsWith('facebook_')) {
                    if (k in newFacebook) newFacebook[k] = numVal;
                } else if (k.startsWith('instagram_')) {
                    if (k in newInstagram) newInstagram[k] = numVal;
                } else if (k in newTwitter) {
                    newTwitter[k] = numVal;
                }
            });

            setTwitterDist(newTwitter);
            setLinkedinDist(newLinkedin);
            setFacebookDist(newFacebook);
            setInstagramDist(newInstagram);
        }
    }, [initialData]);

    // Recalculate total whenever current distribution changes
    useEffect(() => {
        const sum = Object.values(currentDist).reduce((acc: number, v: any) => acc + (v || 0), 0);
        setTotal(Math.round(sum));
    }, [currentDist]);

    const handleSliderChange = (changedKey: string, newValue: number) => {
        // Enforce limits
        if (newValue > 100) newValue = 100;
        if (newValue < 0) newValue = 0;

        const dist = { ...currentDist } as any;
        const otherKeys = Object.keys(dist).filter(k => k !== changedKey);

        // Classic remaining slider logic
        // For simplicity: We just update the value and let user fix the total
        // Or we enable the complex balancing logic. 
        // Let's stick to the complex balancing logic for better UX

        const currentOtherSum = otherKeys.reduce((sum, k) => sum + dist[k], 0);
        const targetOtherSum = 100 - newValue;

        dist[changedKey] = newValue;

        if (currentOtherSum === 0) {
            if (targetOtherSum > 0) {
                const part = Math.floor(targetOtherSum / otherKeys.length);
                let remainder = targetOtherSum % otherKeys.length;
                otherKeys.forEach(k => {
                    dist[k] = part + (remainder > 0 ? 1 : 0);
                    remainder--;
                });
            }
        } else {
            const ratio = targetOtherSum / currentOtherSum;
            let runningSum = newValue;
            otherKeys.forEach((k, index) => {
                if (index === otherKeys.length - 1) {
                    dist[k] = Math.max(0, 100 - runningSum);
                } else {
                    const scaled = Math.round(dist[k] * ratio);
                    dist[k] = scaled;
                    runningSum += scaled;
                }
            });
        }

        setCurrentDist(dist);
    };

    const activityLabels: Record<string, string> = {
        tweet: 'Tweet',
        image_tweet: 'Image Tweet',
        video_tweet: 'Video Tweet',
        thread: 'Thread',
        scroll_engage: 'Scroll & Engage',
        search_engage: 'Search & Engage',
        reply: 'Reply',
        content_creation: 'Content Creation',
        radar_discovery: 'Radar Discovery',
        performance_analysis: 'Analytics Check',

        linkedin_post: 'Post (Text)',
        linkedin_image_post: 'Post (Image)',
        linkedin_video_post: 'Post (Video)',
        linkedin_thread: 'Article',
        linkedin_engage: 'Feed Engagement',
        linkedin_search_engage: 'Search Engagement',
        linkedin_connect: 'Connections',
        linkedin_reply: 'Replies',
        linkedin_content_creation: 'Content Planning',
        linkedin_monitor: 'Monitoring',
        linkedin_analytics: 'Analytics',

        facebook_post: 'Page Post',
        facebook_story: 'Story',
        facebook_engage: 'Community Engagement',

        instagram_post: 'Feed Post',
        instagram_story: 'Story',
        instagram_reel: 'Reel',
        instagram_engage: 'Engagement'
    };

    const riskyKeys = [
        'scroll_engage',
        'search_engage',
        'radar_discovery',
        // 'linkedin_engage', // These are now conditionally locked in the map function logic
        // 'linkedin_search_engage',
        // 'linkedin_connect'
    ];

    return (
        <div className="glass-panel p-4 widget-fluid h-full flex flex-col">
            <h3 className="text-lg font-bold text-white mb-4 font-orbitron flex items-center justify-between">
                <div className="flex items-center">
                    <Sliders className="w-5 h-5 mr-2 text-cyan-500" />
                    TASK FREQUENCY
                </div>
            </h3>

            {/* Platform Toggle */}
            <div className="flex bg-black/40 p-1 rounded-lg mb-4">
                <button
                    onClick={() => setPlatform('twitter')}
                    className={`flex-1 flex items-center justify-center py-2 rounded text-xs font-bold transition-all ${platform === 'twitter' ? 'bg-cyan-500 text-black shadow-[0_0_10px_rgba(6,182,212,0.5)]' : 'text-gray-400 hover:text-white'}`}
                >
                    <Twitter className="w-3 h-3 mr-2" />
                    TWITTER
                </button>
                <button
                    onClick={() => setPlatform('linkedin')}
                    className={`flex-1 flex items-center justify-center py-2 rounded text-xs font-bold transition-all ${platform === 'linkedin' ? 'bg-blue-600 text-white shadow-[0_0_10px_rgba(37,99,235,0.5)]' : 'text-gray-400 hover:text-white'}`}
                >
                    <Linkedin className="w-3 h-3 mr-2" />
                    LINKEDIN
                </button>
                <button
                    onClick={() => setPlatform('facebook')}
                    className={`flex-1 flex items-center justify-center py-2 rounded text-xs font-bold transition-all ${platform === 'facebook' ? 'bg-blue-700 text-white shadow-[0_0_10px_rgba(29,78,216,0.5)]' : 'text-gray-400 hover:text-white'}`}
                >
                    <Facebook className="w-3 h-3 mr-2" />
                    FACEBOOK
                </button>
                <button
                    onClick={() => setPlatform('instagram')}
                    className={`flex-1 flex items-center justify-center py-2 rounded text-xs font-bold transition-all ${platform === 'instagram' ? 'bg-pink-600 text-white shadow-[0_0_10px_rgba(219,39,119,0.5)]' : 'text-gray-400 hover:text-white'}`}
                >
                    <Instagram className="w-3 h-3 mr-2" />
                    INSTAGRAM
                </button>
            </div>

            <div className="mb-6">
                <h4 className="text-xs text-gray-400 mb-2 uppercase tracking-widest font-mono">Quick Presets</h4>
                <div className="grid grid-cols-4 gap-2">
                    {presets.map((preset) => (
                        <button
                            key={preset.id}
                            // Engagement: FB/IG always available, Twitter blocked globally, LinkedIn only in Afterlife
                            disabled={!afterlifeEnabled && preset.id === 'preset-engagement' && platform === 'linkedin'}
                            onClick={() => {
                                if (platform === 'twitter') {
                                    const newPreset = twitterPresets[preset.id];
                                    if (newPreset) {
                                        setTwitterDist({ ...twitterDist, ...newPreset });
                                    }
                                } else if (platform === 'linkedin') {
                                    const newPreset = linkedinPresets[preset.id];
                                    if (newPreset) {
                                        setLinkedinDist({ ...linkedinDist, ...newPreset });
                                    }
                                } else if (platform === 'facebook') {
                                    const newPreset = facebookPresets[preset.id];
                                    if (newPreset) {
                                        setFacebookDist({ ...facebookDist, ...newPreset });
                                    }
                                } else if (platform === 'instagram') {
                                    const newPreset = instagramPresets[preset.id];
                                    if (newPreset) {
                                        setInstagramDist({ ...instagramDist, ...newPreset });
                                    }
                                }
                            }}
                            className={`glass-mini-button flex flex-col items-center justify-center py-2 ${preset.color} hover:bg-white/5 transition-colors 
                                ${!afterlifeEnabled && preset.id === 'preset-engagement' && platform === 'linkedin' ? 'opacity-30 cursor-not-allowed' : ''}
                            `}
                        >
                            <Zap className="w-3 h-3 mb-1" />
                            <span className="text-[10px] uppercase">{preset.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="space-y-4 overflow-y-auto flex-1 pr-2 custom-scrollbar relative">
                {/* GLOBAL LOCK OVERLAY FOR TWITTER IN SAFE MODE */}
                {!afterlifeEnabled && platform === 'twitter' && (
                    <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-black/80 backdrop-blur-sm rounded-lg border border-red-900/50">
                        <div className="p-4 text-center">
                            <h4 className="text-red-500 font-bold mb-2 font-orbitron tracking-wider">RESTRICTED ACCESS</h4>
                            <p className="text-xs text-gray-400 max-w-[200px] leading-relaxed">
                                Twitter/X operations require <span className="text-red-400 font-bold">AFTERLIFE MODE</span> (Hybrid Rogue) to be active.
                            </p>
                            <div className="mt-3 px-3 py-1 bg-red-900/20 rounded border border-red-900/50 text-[10px] text-red-400 uppercase font-mono inline-block">
                                Safe Mode: Offline
                            </div>
                        </div>
                    </div>
                )}

                {Object.entries(currentDist).map(([key, value]) => {
                    const isRisky = riskyKeys.includes(key);
                    const isLinkedInRisky = ['linkedin_engage', 'linkedin_search_engage', 'linkedin_connect'].includes(key);

                    // Twitter: Locked if !afterlifeEnabled (handled by overlay, but also lock inputs)
                    // LinkedIn: Locked if !afterlifeEnabled AND key is one of the risky ones
                    const isLocked = (!afterlifeEnabled && platform === 'twitter') ||
                        (!afterlifeEnabled && platform === 'linkedin' && isLinkedInRisky) ||
                        (isRisky && !afterlifeEnabled);

                    return (
                        <div key={key} className={`group ${isLocked ? 'opacity-20 grayscale pointer-events-none' : ''}`}>
                            <div className="flex justify-between items-center mb-1">
                                <label className="text-xs text-gray-300 font-mono uppercase flex items-center">
                                    {activityLabels[key] || key}
                                    {isLocked && <span className="ml-2 text-[8px] text-red-500 border border-red-500/50 px-1 rounded bg-red-900/20">LOCKED</span>}
                                </label>
                                <span className={`text-xs font-bold ${isLocked ? 'text-gray-500' : 'text-cyan-400'}`}>
                                    {isLocked ? 'DISABLED' : `${value}%`}
                                </span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={value as number}
                                disabled={isLocked}
                                onChange={(e) => handleSliderChange(key, parseInt(e.target.value))}
                                className={`w-full h-1.5 rounded-lg appearance-none cursor-pointer 
                                    ${isLocked ? 'bg-gray-800 cursor-not-allowed' : 'bg-gray-800 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-cyan-500 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:transition-all hover:[&::-webkit-slider-thumb]:scale-125'}
                                `}
                            />
                        </div>
                    );
                })}
            </div>

            <div className="mt-4 pt-4 border-t border-cyan-500/20">
                <div className="flex justify-between items-center mb-4">
                    <span className="text-xs text-gray-400 font-mono uppercase">Total {platform === 'twitter' ? 'X' : 'LN'} Distribution</span>
                    <span className={`text-lg font-bold ${Math.abs(total - 100) <= 1 ? 'text-green-500' : 'text-red-500'}`}>{total}%</span>
                </div>
                <button
                    className="w-full glass-button glass-button-primary flex items-center justify-center p-2 rounded-lg"
                    onClick={() => onSave?.(currentDist, platform)}
                >
                    <Save className="w-4 h-4 mr-2" />
                    SAVE {platform === 'twitter' ? 'TWITTER' : platform === 'linkedin' ? 'LINKEDIN' : platform === 'facebook' ? 'FACEBOOK' : 'INSTAGRAM'} DISTRIBUTION
                </button>
            </div>
        </div >
    );
}
