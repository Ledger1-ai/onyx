"use client";

import React, { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Database, Cpu, Activity } from 'lucide-react';
import AfterlifeSwitch from './Dashboard/AfterlifeSwitch';

export default function Header() {
    const [user, setUser] = useState<any>(null);
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [status, setStatus] = useState({ database: false, worker: false });

    useEffect(() => {
        const checkStatus = async () => {
            try {
                const res = await fetch('/api/status');
                if (res.ok) {
                    const data = await res.json();
                    setStatus({
                        database: !!data.database,
                        worker: !!data.worker
                    });
                }
            } catch {
                setStatus({ database: false, worker: false });
            }
        };

        const fetchUser = async () => {
            try {
                const res = await fetch('/api/auth/me');
                if (res.ok) {
                    const data = await res.json();
                    setUser(data.user);
                }
            } catch (e) {
                console.error(e);
            }
        };

        checkStatus();
        fetchUser();
        const interval = setInterval(checkStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleLogout = async () => {
        await fetch('/api/auth/logout', { method: 'POST' });
        window.location.href = '/underworld/gateway';
    };

    return (
        <header className="bg-gray-900/80 backdrop-blur-md border-b border-cyan-500/30 sticky top-0 z-50">
            <div className="w-full px-4 py-3">
                <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-4">
                        <div className="w-14 h-14 rounded-lg flex items-center justify-center p-1 border border-cyan-500/50 shadow-[0_0_15px_rgba(0,255,255,0.2)] bg-white/5 backdrop-blur-sm hover:bg-white/10 transition-colors">
                            {/* Fallback icon if image missing, or use Next Image */}
                            <div className="relative w-full h-full">
                                <Image
                                    src="/bssymbol.png"
                                    alt="BasaltONYX"
                                    fill
                                    className="object-contain brightness-0 invert"
                                    unoptimized
                                />
                            </div>
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-white tracking-widest font-orbitron">BasaltONYX</h1>
                            <p className="text-xs text-cyan-400/70 tracking-wider font-rajdhani uppercase">Autonomous Social Intelligence</p>
                        </div>
                    </div>

                    {/* Center: Afterlife Switch */}
                    <div className="flex-1 flex justify-center">
                        <div className="scale-75 origin-center">
                            <AfterlifeSwitch />
                        </div>
                    </div>

                    <div className="flex items-center space-x-4">
                        {/* User Profile Dropdown */}
                        {user && (
                            <div className="relative">
                                <button
                                    onClick={() => setShowUserMenu(!showUserMenu)}
                                    className="flex items-center space-x-2 px-3 py-1.5 bg-gray-800/50 border border-cyan-500/30 rounded-lg hover:bg-gray-700/50 transition-colors"
                                >
                                    <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center border border-cyan-400/30">
                                        <span className="text-cyan-400 font-bold font-orbitron text-xs">
                                            {user.name.charAt(0).toUpperCase()}
                                        </span>
                                    </div>
                                    <div className="hidden md:block text-left">
                                        <div className="text-xs font-bold text-white font-orbitron">{user.name}</div>
                                        <div className="text-[10px] text-cyan-400/70">{user.role}</div>
                                    </div>
                                </button>

                                {showUserMenu && (
                                    <div className="absolute right-0 mt-2 w-48 bg-gray-900 border border-cyan-500/30 rounded-xl shadow-[0_0_20px_rgba(0,0,0,0.5)] backdrop-blur-xl overflow-hidden animate-in fade-in slide-in-from-top-2">
                                        <Link
                                            href="/underworld/profile"
                                            className="block px-4 py-2 text-sm text-gray-300 hover:bg-cyan-500/10 hover:text-cyan-400 transition-colors"
                                            onClick={() => setShowUserMenu(false)}
                                        >
                                            Profile Settings
                                        </Link>
                                        <button
                                            onClick={handleLogout}
                                            className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                                        >
                                            Logout
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Database Status */}
                        <div className={`hidden md:flex items-center space-x-2 px-3 py-1 bg-gray-800/50 border rounded-full transition-colors duration-300 ${status.database ? 'border-green-500/30' : 'border-red-500/30'}`}>
                            <div className={`w-2 h-2 rounded-full ${status.database ? 'bg-green-500 animate-pulse shadow-[0_0_8px_rgba(0,255,0,0.8)]' : 'bg-red-500'}`}></div>
                            <Database className={`w-3 h-3 ${status.database ? 'text-green-400' : 'text-red-400'} mr-1`} />
                            <span className={`text-xs font-medium tracking-wider ${status.database ? 'text-green-400' : 'text-red-400'}`}>
                                {status.database ? 'DB ONLINE' : 'DB OFFLINE'}
                            </span>
                        </div>

                        <div className="flex items-center text-xs text-cyan-300/60 font-mono pl-2 border-l border-gray-700">
                            <Activity className={`w-3 h-3 mr-2 ${status.worker && status.database ? 'animate-pulse text-cyan-300' : 'text-gray-500'}`} />
                            <span className={status.worker && status.database ? '' : 'text-gray-500'}>
                                {status.worker && status.database ? 'SYSTEM ACTIVE' : 'SYSTEM DEGRADED'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}

