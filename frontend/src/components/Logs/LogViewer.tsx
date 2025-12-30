"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Terminal, AlertCircle, Info, AlertTriangle } from 'lucide-react';

interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
    status: 'success' | 'warning' | 'error';
}

export default function LogViewer() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [filter, setFilter] = useState<'ALL' | 'INFO' | 'WARNING' | 'ERROR'>('ALL');
    const [autoScroll, setAutoScroll] = useState(false); // Default to false
    const logsEndRef = useRef<HTMLDivElement>(null);

    const fetchLogs = async () => {
        try {
            const res = await fetch('/api/logs');
            const data = await res.json();
            if (data.recent_sessions) {
                // Backend returns 'recent_sessions' based on current API structure
                setLogs(data.recent_sessions);
            }
        } catch (err) {
            console.error('Error fetching logs:', err);
        }
    };

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 3000); // Poll every 3 seconds
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (autoScroll && logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [logs, autoScroll]);

    const filteredLogs = logs.filter(log => {
        if (filter === 'ALL') return true;
        return log.level === filter;
    });

    const getLevelColor = (level: string) => {
        switch (level) {
            case 'ERROR': return 'text-red-400';
            case 'WARNING': return 'text-yellow-400';
            case 'INFO': return 'text-blue-400';
            default: return 'text-gray-400';
        }
    };

    const getLevelIcon = (level: string) => {
        switch (level) {
            case 'ERROR': return <AlertCircle className="w-3 h-3" />;
            case 'WARNING': return <AlertTriangle className="w-3 h-3" />;
            default: return <Info className="w-3 h-3" />;
        }
    };

    return (
        <div className="flex flex-col h-full bg-black/80 rounded-2xl border border-white/10 overflow-hidden shadow-2xl backdrop-blur-md font-mono text-sm max-h-[80vh]">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/10">
                <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-green-400" />
                    <span className="font-orbitron font-bold text-gray-300">SYSTEM LOGS</span>
                </div>

                <div className="flex items-center gap-2">
                    {/* Auto Scroll Toggle */}
                    <button
                        onClick={() => setAutoScroll(!autoScroll)}
                        className={`mr-3 px-2 py-1 text-[10px] rounded transition-all border ${autoScroll
                                ? 'bg-green-500/10 text-green-400 border-green-500/20'
                                : 'bg-transparent text-gray-500 border-white/5 hover:border-white/20'
                            }`}
                    >
                        {autoScroll ? 'SCROLL LOCK: ON' : 'SCROLL LOCK: OFF'}
                    </button>

                    <div className="flex bg-black/50 rounded-lg p-1">
                        {(['ALL', 'INFO', 'WARNING', 'ERROR'] as const).map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                className={`px-2 py-1 text-[10px] rounded transition-all ${filter === f
                                    ? 'bg-white/10 text-white'
                                    : 'text-gray-500 hover:text-gray-300'
                                    }`}
                            >
                                {f}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Log Output */}
            <div className="flex-1 overflow-y-auto p-4 space-y-1 font-mono hover:overflow-y-auto custom-scrollbar">
                {filteredLogs.length === 0 ? (
                    <div className="text-gray-600 text-center py-10 italic">No logs found...</div>
                ) : (
                    filteredLogs.map((log, i) => (
                        <div key={i} className="flex gap-3 hover:bg-white/5 p-1 rounded transition-colors group">
                            <span className="text-gray-600 w-32 shrink-0 text-[10px] pt-0.5">{new Date(log.timestamp).toLocaleTimeString()}</span>
                            <div className={`flex items-start gap-2 ${getLevelColor(log.level)}`}>
                                <span className="pt-1 opacity-70 group-hover:opacity-100 transition-opacity">
                                    {getLevelIcon(log.level)}
                                </span>
                                <span className="break-all">{log.message}</span>
                            </div>
                        </div>
                    ))
                )}
                <div ref={logsEndRef} />
            </div>

            {/* Status Bar */}
            <div className="px-4 py-2 bg-white/5 border-t border-white/10 flex justify-between text-[10px] text-gray-500 font-orbitron">
                <span className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
                    LIVE CONNECTION
                </span>
                <span>{logs.length} EVENTS CAPTURED</span>
            </div>
        </div>
    );
}
