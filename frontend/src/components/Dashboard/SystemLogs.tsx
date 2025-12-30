"use client";

import React, { useRef, useEffect } from 'react';
import { Terminal } from 'lucide-react';

interface SystemLogsProps {
    logs: any[];
}

export default function SystemLogs({ logs }: SystemLogsProps) {
    const logContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (logContainerRef.current) {
            logContainerRef.current.scrollTop = 0;
        }
    }, [logs]);

    return (
        <div className="glass-panel p-0 h-[300px] flex flex-col widget-fluid relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 bg-gray-900/90 p-2 border-b border-cyan-500/30 z-10 flex items-center">
                <Terminal className="w-4 h-4 text-cyan-500 mr-2" />
                <span className="text-xs font-bold text-white font-orbitron tracking-widest">SYSTEM LOGS</span>
                <div className="ml-auto flex space-x-1">
                    <div className="w-2 h-2 rounded-full bg-red-500"></div>
                    <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 pt-10 font-mono text-xs space-y-1 bg-black/80 nice-scroll" ref={logContainerRef}>
                {logs.map((log, index) => {
                    const isError = log.status === 'error' || log.level === 'ERROR';
                    const isWarning = log.status === 'warning' || log.level === 'WARNING';
                    const isSuccess = log.status === 'success' || log.level === 'INFO';

                    const colorClass = isError ? 'text-red-500 border-l-2 border-red-500 pl-2' :
                        isWarning ? 'text-yellow-500 border-l-2 border-yellow-500 pl-2' :
                            isSuccess ? 'text-green-400 border-l-2 border-green-500 pl-2' :
                                'text-blue-400 border-l-2 border-blue-500 pl-2';

                    return (
                        <div key={index} className={`py-0.5 hover:bg-white/5 ${colorClass} flex items-start`}>
                            <span className="opacity-50 mr-2 shrink-0">[{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}]</span>
                            <span className="break-all">{log.message || (typeof log === 'string' ? log : JSON.stringify(log))}</span>
                        </div>
                    );
                })}
                {logs.length === 0 && (
                    <div className="text-gray-600 italic">No logs available...</div>
                )}
            </div>
        </div>
    );
}
