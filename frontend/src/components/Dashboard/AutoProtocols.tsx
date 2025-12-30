"use client";

import React, { useState } from 'react';
import { Bot, MessageCircle, Mic2, Send } from 'lucide-react';

export default function AutoProtocols() {
    const [shoutoutsEnabled, setShoutoutsEnabled] = useState(true);
    const [repliesEnabled, setRepliesEnabled] = useState(true);
    const [shoutoutUser, setShoutoutUser] = useState("");
    const [maxShoutouts, setMaxShoutouts] = useState(3);
    const [maxReplies, setMaxReplies] = useState(10);
    const [isLoading, setIsLoading] = useState<string | null>(null);

    React.useEffect(() => {
        // Load initial status
        fetch('/api/notifications/status')
            .then(res => res.json())
            .then(data => {
                if (data.shoutouts_enabled !== undefined) setShoutoutsEnabled(data.shoutouts_enabled);
                if (data.replies_enabled !== undefined) setRepliesEnabled(data.replies_enabled);
                if (data.max_shoutouts !== undefined) setMaxShoutouts(data.max_shoutouts);
                if (data.max_replies !== undefined) setMaxReplies(data.max_replies);
            })
            .catch(console.error);
    }, []);

    const handleShoutout = async () => {
        if (!shoutoutUser) return;
        try {
            await fetch('/api/notifications/shoutout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: shoutoutUser })
            });
            setShoutoutUser("");
        } catch (e) {
            console.error(e);
        }
    };

    const handleAutoMode = async () => {
        try {
            setIsLoading('auto_mode');
            const res = await fetch('/api/notifications/manage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    enable_follower_shoutouts: shoutoutsEnabled,
                    enable_auto_replies: repliesEnabled,
                    max_shoutouts_per_session: maxShoutouts,
                    max_auto_replies_per_session: maxReplies
                })
            });
            const data = await res.json();
            console.log('Auto Mode Result:', data);
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(null);
        }
    };

    const handleAutoReply = async () => {
        try {
            setIsLoading('auto_reply');
            const res = await fetch('/api/notifications/auto-reply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    max_replies: maxReplies,
                    filter_keywords: []
                })
            });
            const data = await res.json();
            console.log('Auto Reply Result:', data);
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(null);
        }
    };

    return (
        <div className="glass-panel p-4 mb-3 widget-fixed compact">
            <h3 className="text-lg font-bold text-white mb-3 font-orbitron flex items-center">
                <Bot className="w-5 h-5 mr-2 text-purple-500" />
                AUTO PROTOCOLS
            </h3>

            <div className="bg-black/40 rounded-lg p-3 border border-purple-500/20">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Left Column: Configuration */}
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <label className="flex items-center space-x-2 cursor-pointer group">
                                <div className="relative">
                                    <input
                                        type="checkbox"
                                        checked={shoutoutsEnabled}
                                        onChange={(e) => setShoutoutsEnabled(e.target.checked)}
                                        className="sr-only"
                                    />
                                    <div className={`w-10 h-5 rounded-full shadow-inner transition-colors duration-300 ${shoutoutsEnabled ? 'bg-purple-600' : 'bg-gray-700'}`}></div>
                                    <div className={`absolute w-3 h-3 bg-white rounded-full top-1 left-1 transform transition-transform duration-300 ${shoutoutsEnabled ? 'translate-x-5' : ''}`}></div>
                                </div>
                                <span className="text-xs text-gray-300 font-mono group-hover:text-purple-400 transition-colors">Follower Protocol</span>
                            </label>

                            <label className="flex items-center space-x-2 cursor-pointer group">
                                <div className="relative">
                                    <input
                                        type="checkbox"
                                        checked={repliesEnabled}
                                        onChange={(e) => setRepliesEnabled(e.target.checked)}
                                        className="sr-only"
                                    />
                                    <div className={`w-10 h-5 rounded-full shadow-inner transition-colors duration-300 ${repliesEnabled ? 'bg-purple-600' : 'bg-gray-700'}`}></div>
                                    <div className={`absolute w-3 h-3 bg-white rounded-full top-1 left-1 transform transition-transform duration-300 ${repliesEnabled ? 'translate-x-5' : ''}`}></div>
                                </div>
                                <span className="text-xs text-gray-300 font-mono group-hover:text-purple-400 transition-colors">Auto Response</span>
                            </label>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div className="glass-input-container">
                                <label className="text-[10px] text-gray-500 mb-1 block uppercase">Max Shoutouts</label>
                                <input
                                    type="number"
                                    value={maxShoutouts}
                                    onChange={(e) => setMaxShoutouts(parseInt(e.target.value) || 0)}
                                    className="glass-input text-xs w-full bg-gray-900 border border-gray-700 rounded p-1 text-white"
                                />
                            </div>
                            <div className="glass-input-container">
                                <label className="text-[10px] text-gray-500 mb-1 block uppercase">Max Replies</label>
                                <input
                                    type="number"
                                    value={maxReplies}
                                    onChange={(e) => setMaxReplies(parseInt(e.target.value) || 0)}
                                    className="glass-input text-xs w-full bg-gray-900 border border-gray-700 rounded p-1 text-white"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Actions */}
                    <div className="space-y-4 flex flex-col justify-between">
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                onClick={handleAutoMode}
                                disabled={isLoading === 'auto_mode'}
                                className="glass-button glass-button-accent text-xs py-1.5 rounded flex items-center justify-center hover:bg-purple-600 transition-colors disabled:opacity-50"
                            >
                                <Bot className={`w-3 h-3 mr-1 ${isLoading === 'auto_mode' ? 'animate-spin' : ''}`} />
                                {isLoading === 'auto_mode' ? 'Starting...' : 'Auto Mode'}
                            </button>
                            <button
                                onClick={handleAutoReply}
                                disabled={isLoading === 'auto_reply'}
                                className="glass-button glass-button-success text-xs py-1.5 rounded flex items-center justify-center hover:bg-green-600 transition-colors disabled:opacity-50"
                            >
                                <MessageCircle className={`w-3 h-3 mr-1 ${isLoading === 'auto_reply' ? 'animate-spin' : ''}`} />
                                {isLoading === 'auto_reply' ? 'Replying...' : 'Auto-Reply'}
                            </button>
                        </div>

                        <div className="flex space-x-2">
                            <input
                                type="text"
                                placeholder="@USERNAME"
                                value={shoutoutUser}
                                onChange={(e) => setShoutoutUser(e.target.value)}
                                className="flex-1 bg-gray-900/50 border border-gray-700 rounded text-xs px-2 text-white placeholder-gray-600 focus:border-purple-500 focus:outline-none transition-colors"
                            />
                            <button
                                onClick={handleShoutout}
                                className="bg-purple-600 hover:bg-purple-700 text-white rounded px-3 py-1 flex items-center transition-colors"
                            >
                                <Mic2 className="w-3 h-3" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
