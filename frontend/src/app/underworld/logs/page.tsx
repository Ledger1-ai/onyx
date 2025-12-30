"use client";

import React from 'react';
import LogViewer from '@/components/Logs/LogViewer';

export default function LogsPage() {
    return (
        <div className="min-h-screen p-6 pb-32 flex flex-col">
             <header className="mb-6">
                <h1 className="text-2xl font-bold font-orbitron text-white glitch-text">SYSTEM LOGS // TERMINAL</h1>
                <p className="text-gray-400 text-sm">Real-time system diagnostics and event stream.</p>
            </header>
            
            <div className="flex-1">
                <LogViewer />
            </div>
        </div>
    );
}
