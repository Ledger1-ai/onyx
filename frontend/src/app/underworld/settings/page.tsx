"use client";

import React, { useState } from 'react';
import { User, Shield, Key } from 'lucide-react';
import IdentitySettings from '../../../components/Settings/IdentitySettings';
import UserManagement from '../../../components/Settings/UserManagement';

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<'identity' | 'users'>('identity');

    return (
        <div className="w-full h-full p-4 overflow-y-auto custom-scrollbar">
            <h1 className="text-2xl font-bold text-white mb-6 font-orbitron tracking-wider flex items-center">
                <span className="w-1 h-6 bg-cyan-500 mr-3 shadow-[0_0_10px_#00ffff]"></span>
                SYSTEM CONFIGURATION
            </h1>

            <div className="max-w-7xl mx-auto space-y-6">
                {/* Tabs */}
                <div className="flex space-x-1 bg-gray-900/50 p-1 rounded-lg w-fit border border-gray-800">
                    <button
                        onClick={() => setActiveTab('identity')}
                        className={`flex items-center px-4 py-2 rounded-md font-mono text-sm font-bold transition-all ${activeTab === 'identity'
                                ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.1)] border border-cyan-500/30'
                                : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                            }`}
                    >
                        <Shield className="w-4 h-4 mr-2" />
                        IDENTITY & INTEGRATIONS
                    </button>
                    <button
                        onClick={() => setActiveTab('users')}
                        className={`flex items-center px-4 py-2 rounded-md font-mono text-sm font-bold transition-all ${activeTab === 'users'
                                ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.1)] border border-cyan-500/30'
                                : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                            }`}
                    >
                        <User className="w-4 h-4 mr-2" />
                        USER MANAGEMENT
                    </button>
                </div>

                {/* Content */}
                <div className="transition-all duration-300">
                    {activeTab === 'identity' ? (
                        <IdentitySettings />
                    ) : (
                        <UserManagement />
                    )}
                </div>
            </div>
        </div>
    );
}
