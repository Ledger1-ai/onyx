"use client";

import React, { useState } from 'react';
import { Power, Ban, Settings, RefreshCw, MessageSquare } from 'lucide-react';
import Link from 'next/link';

import ConfigModal from './ConfigModal';

interface CommandCenterProps {
    onRefresh?: () => void;
}

export default function CommandCenter({ onRefresh }: CommandCenterProps) {
    const [isLoading, setIsLoading] = useState<string | null>(null);
    const [isConfigOpen, setIsConfigOpen] = useState(false);

    const handleAction = async (action: string, endpoint: string) => {
        try {
            setIsLoading(action);
            const res = await fetch(endpoint, { method: 'POST' });

            // Handle non-200 responses specifically
            if (!res.ok) {
                const text = await res.text();
                console.error(`${action} failed with status ${res.status}:`, text);
                return;
            }

            const data = await res.json();
            console.log(`${action} result:`, data);
            // Optional: Toast notification here
        } catch (error) {
            console.error(`${action} failed:`, error);
        } finally {
            setIsLoading(null);
        }
    };

    return (
        <div className="glass-panel p-4 mb-3 widget-fixed relative group">
            <div className="absolute inset-0 bg-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
            <h2 className="text-lg font-bold text-white mb-3 font-orbitron tracking-wider flex items-center">
                <span className="w-1 h-4 bg-cyan-500 mr-2 shadow-[0_0_10px_#00ffff]"></span>
                COMMAND CENTER
            </h2>

            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
                <button
                    onClick={() => handleAction('init', '/api/control/start')}
                    disabled={isLoading === 'init'}
                    className="glass-button glass-button-success flex items-center justify-center p-3 rounded-lg group/btn relative overflow-hidden"
                >
                    <div className="absolute inset-0 bg-green-500/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                    <Power className="w-4 h-4 mr-2" />
                    <span>INIT</span>
                </button>

                <button
                    onClick={() => handleAction('stop', '/api/control/stop')}
                    disabled={isLoading === 'stop'}
                    className="glass-button glass-button-danger flex items-center justify-center p-3 rounded-lg group/btn relative overflow-hidden"
                >
                    <div className="absolute inset-0 bg-red-500/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                    <Ban className="w-4 h-4 mr-2" />
                    <span>STOP</span>
                </button>

                <button
                    onClick={() => handleAction('optimize', '/api/control/optimize')}
                    disabled={isLoading === 'optimize'}
                    className="glass-button glass-button-primary flex items-center justify-center p-3 rounded-lg group/btn relative overflow-hidden"
                >
                    <div className="absolute inset-0 bg-cyan-500/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                    <Settings className="w-4 h-4 mr-2" />
                    <span>OPTIMIZE</span>
                </button>

                <button
                    onClick={onRefresh}
                    className="glass-button glass-button-secondary flex items-center justify-center p-3 rounded-lg group/btn relative overflow-hidden"
                >
                    <div className="absolute inset-0 bg-blue-500/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                    <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                    <span>REFRESH</span>
                </button>

                <Link
                    href="/chat"
                    className="glass-button glass-button-accent flex items-center justify-center p-3 rounded-lg group/btn relative overflow-hidden text-center"
                >
                    <div className="absolute inset-0 bg-purple-500/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                    <MessageSquare className="w-4 h-4 mr-2" />
                    <span>CHAT</span>
                </Link>



                <button
                    onClick={() => setIsConfigOpen(true)}
                    className="glass-button glass-button-secondary flex items-center justify-center p-3 rounded-lg group/btn relative overflow-hidden"
                >
                    <div className="absolute inset-0 bg-gray-500/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                    <Settings className="w-4 h-4 mr-2" />
                    <span>CONFIG</span>
                </button>
            </div>

            <ConfigModal
                isOpen={isConfigOpen}
                onClose={() => setIsConfigOpen(false)}
                onRefreshSchedule={onRefresh}
            />
        </div>
    );
}
