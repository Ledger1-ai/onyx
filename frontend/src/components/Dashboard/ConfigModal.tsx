"use client";

import React, { useEffect, useState } from 'react';
import { X, RefreshCw, Sparkles, AlertTriangle, Linkedin, Twitter, Server } from 'lucide-react';

interface TaskConfig {
    id: string;
    name: string;
    enabled: boolean;
}

interface ConfigModalProps {
    isOpen: boolean;
    onClose: () => void;
    onRefreshSchedule?: () => void;
}

type Tab = 'twitter' | 'linkedin' | 'meta' | 'system';

export default function ConfigModal({ isOpen, onClose, onRefreshSchedule }: ConfigModalProps) {
    const [tasks, setTasks] = useState<TaskConfig[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<Tab>('twitter');

    useEffect(() => {
        if (isOpen) {
            loadConfiguration();
        }
    }, [isOpen]);

    const loadConfiguration = async () => {
        setIsLoading(true);
        try {
            const res = await fetch('/api/tasks/configuration');
            const data = await res.json();
            if (data.success && Array.isArray(data.tasks)) {
                setTasks(data.tasks);
            }
        } catch (error) {
            console.error('Failed to load task configuration:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleToggleTask = async (taskId: string) => {
        try {
            // Optimistic update
            setTasks(prev => prev.map(t =>
                t.id === taskId ? { ...t, enabled: !t.enabled } : t
            ));

            const res = await fetch('/api/tasks/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ taskId })
            });

            const data = await res.json();
            if (!data.success) {
                // Revert on failure
                setTasks(prev => prev.map(t =>
                    t.id === taskId ? { ...t, enabled: !t.enabled } : t
                ));
                console.error('Failed to toggle task:', data.error);
            }
        } catch (error) {
            console.error('Error toggling task:', error);
            // Revert on error
            setTasks(prev => prev.map(t =>
                t.id === taskId ? { ...t, enabled: !t.enabled } : t
            ));
        }
    };

    const handleRegenerate = async () => {
        setActionLoading('regenerate');
        try {
            const res = await fetch('/api/tasks/regenerate', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                if (onRefreshSchedule) onRefreshSchedule();
                onClose();
            }
        } catch (error) {
            console.error('Error regenerating schedule:', error);
        } finally {
            setActionLoading(null);
        }
    };

    const handleFreshStart = async () => {
        setActionLoading('fresh');
        try {
            const res = await fetch('/api/tasks/create-fresh', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                if (onRefreshSchedule) onRefreshSchedule();
                onClose();
            }
        } catch (error) {
            console.error('Error creating fresh schedule:', error);
        } finally {
            setActionLoading(null);
        }
    };

    const filteredTasks = tasks.filter(task => {
        const id = task.id.toUpperCase();

        if (activeTab === 'linkedin') {
            return id.includes('LINKEDIN');
        } else if (activeTab === 'meta') {
            return id.includes('FACEBOOK') || id.includes('INSTAGRAM') || id.includes('FB_') || id.includes('IG_') || id.includes('META');
        } else if (activeTab === 'twitter') {
            // Broaden capture for Twitter related tasks - simplify to just check for TWITTER
            return id.includes('TWITTER') || (
                id.includes('TWEET') ||
                id.includes('REPLY') ||
                id.includes('THREAD') ||
                id.includes('ENGAGE') ||
                id.includes('RADAR') ||
                id.includes('CONTENT') ||
                id.includes('MONITOR') ||
                id.includes('STRATEGY') ||
                id.includes('PERFORMANCE')
            ) && !id.includes('LINKEDIN') && !id.includes('FACEBOOK') && !id.includes('INSTAGRAM') && !id.includes('META');
        } else {
            // System/Other - anything not matched above
            const isLinkedin = id.includes('LINKEDIN');
            const isMeta = id.includes('FACEBOOK') || id.includes('INSTAGRAM') || id.includes('FB_') || id.includes('IG_') || id.includes('META');
            const isTwitter = id.includes('TWITTER') || (
                id.includes('TWEET') ||
                id.includes('REPLY') ||
                id.includes('THREAD') ||
                id.includes('ENGAGE') ||
                id.includes('RADAR') ||
                id.includes('CONTENT') ||
                id.includes('MONITOR') ||
                id.includes('STRATEGY') ||
                id.includes('PERFORMANCE')
            );
            return !isLinkedin && !isTwitter && !isMeta;
        }
    });

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 backdrop-blur-sm p-4">
            <div className="bg-gray-800 glass-panel rounded-lg p-6 w-full max-w-md border border-gray-700 shadow-2xl relative animate-in fade-in zoom-in duration-200">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>

                <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                    <SettingsIcon className="w-6 h-6 mr-2 text-cyan-400" />
                    Task Configuration
                </h3>

                {/* Tabs */}
                <div className="flex space-x-2 mb-4 border-b border-gray-700 pb-1">
                    <button
                        onClick={() => setActiveTab('twitter')}
                        className={`flex items-center px-3 py-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'twitter'
                            ? 'border-cyan-400 text-cyan-400'
                            : 'border-transparent text-gray-400 hover:text-white'
                            }`}
                    >
                        <Twitter className="w-4 h-4 mr-2" />
                        Twitter
                    </button>
                    <button
                        onClick={() => setActiveTab('linkedin')}
                        className={`flex items-center px-3 py-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'linkedin'
                            ? 'border-blue-400 text-blue-400'
                            : 'border-transparent text-gray-400 hover:text-white'
                            }`}
                    >
                        <Linkedin className="w-4 h-4 mr-2" />
                        LinkedIn
                    </button>
                    <button
                        onClick={() => setActiveTab('meta')}
                        className={`flex items-center px-3 py-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'meta'
                            ? 'border-pink-400 text-pink-400'
                            : 'border-transparent text-gray-400 hover:text-white'
                            }`}
                    >
                        <span className="font-bold mr-2">∞</span>
                        Meta
                    </button>
                    <button
                        onClick={() => setActiveTab('system')}
                        className={`flex items-center px-3 py-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'system'
                            ? 'border-gray-400 text-gray-200'
                            : 'border-transparent text-gray-400 hover:text-white'
                            }`}
                    >
                        <Server className="w-4 h-4 mr-2" />
                        System
                    </button>
                </div>

                <div className="mb-6">
                    <p className="text-gray-300 text-sm mb-4">
                        Manage enabled tasks for {activeTab === 'system' ? 'system processes' : `${activeTab} automation`}.
                    </p>

                    <div className="space-y-2 max-h-60 overflow-y-auto pr-2 custom-scrollbar min-h-[150px]">
                        {isLoading ? (
                            <div className="text-center py-4 text-gray-500">Loading tasks...</div>
                        ) : filteredTasks.length === 0 ? (
                            <div className="text-center py-8 text-gray-500 italic">
                                No {activeTab} tasks available.
                            </div>
                        ) : (
                            filteredTasks.map(task => (
                                <label
                                    key={task.id}
                                    className="flex items-center space-x-3 p-3 bg-gray-700/50 hover:bg-gray-700 rounded-lg cursor-pointer transition-colors border border-transparent hover:border-gray-600"
                                >
                                    <input
                                        type="checkbox"
                                        checked={task.enabled}
                                        onChange={() => handleToggleTask(task.id)}
                                        className={`w-5 h-5 rounded border-gray-500 bg-gray-800 ${activeTab === 'linkedin' ? 'text-blue-500 focus:ring-blue-500/50' :
                                            activeTab === 'meta' ? 'text-pink-500 focus:ring-pink-500/50' :
                                                'text-cyan-500 focus:ring-cyan-500/50'
                                            }`}
                                    />
                                    <span className="text-gray-200 text-sm font-medium">{task.name}</span>
                                </label>
                            ))
                        )}
                    </div>
                </div>

                <div className="bg-yellow-900/20 border border-yellow-600/30 rounded-lg p-3 mb-6 flex items-start">
                    <AlertTriangle className="w-4 h-4 text-yellow-500 mr-2 shrink-0 mt-0.5" />
                    <p className="text-yellow-200/60 text-xs">
                        Changes apply to next generation.
                    </p>
                </div>


                <div className="flex justify-between gap-3 pt-4 border-t border-gray-700">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                    >
                        Close
                    </button>

                    <div className="flex gap-2">
                        <button
                            onClick={handleFreshStart}
                            disabled={!!actionLoading}
                            className="px-3 py-2 rounded-lg text-xs font-bold text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center shadow-lg shadow-green-900/20"
                            title="Clear all future tasks and regenerate from scratch"
                        >
                            {actionLoading === 'fresh' ? (
                                <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                            ) : (
                                <Sparkles className="w-3 h-3 mr-1" />
                            )}
                            Reset
                        </button>

                        <button
                            onClick={handleRegenerate}
                            disabled={!!actionLoading}
                            className="px-3 py-2 rounded-lg text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center shadow-lg shadow-blue-900/20"
                            title="Regenerate missing tasks for today"
                        >
                            {actionLoading === 'regenerate' ? (
                                <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                            ) : (
                                <RefreshCw className="w-3 h-3 mr-1" />
                            )}
                            Regenerate Tasks
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function SettingsIcon({ className }: { className?: string }) {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.74v-.47a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path>
            <circle cx="12" cy="12" r="3"></circle>
        </svg>
    )
}
