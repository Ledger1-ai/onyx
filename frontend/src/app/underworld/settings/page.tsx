import React from 'react';
import IdentitySettings from '../../../components/Settings/IdentitySettings';

export default function SettingsPage() {
    return (
        <div className="w-full h-full p-4 overflow-y-auto custom-scrollbar">
            <h1 className="text-2xl font-bold text-white mb-6 font-orbitron tracking-wider flex items-center">
                <span className="w-1 h-6 bg-cyan-500 mr-3 shadow-[0_0_10px_#00ffff]"></span>
                SYSTEM CONFIGURATION
            </h1>

            <div className="max-w-7xl mx-auto">
                <IdentitySettings />
            </div>
        </div>
    );
}
