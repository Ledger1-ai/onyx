"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Rocket, Activity, Terminal, Settings } from 'lucide-react';

const navItems = [
    { name: 'Command', path: '/underworld/dashboard', icon: Rocket },
    { name: 'Analytics', path: '/underworld/analytics', icon: Activity },
    { name: 'Logs', path: '/underworld/logs', icon: Terminal },
    { name: 'Settings', path: '/underworld/settings', icon: Settings },
];

export default function NavigationDock() {
    const pathname = usePathname();

    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-md px-4 sm:px-0">
            <nav className="glass-panel px-6 py-3 rounded-2xl border border-white/10 flex items-center justify-between shadow-[0_0_20px_rgba(0,0,0,0.5)] bg-black/60 backdrop-blur-xl">
                {navItems.map((item) => {
                    const isActive = pathname === item.path;
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.path}
                            href={item.path}
                            className={`group relative flex flex-col items-center justify-center transition-all duration-300 ${isActive ? 'text-cyan-400 scale-110' : 'text-gray-400 hover:text-white'
                                }`}
                        >
                            {isActive && (
                                <div className="absolute -top-10 px-2 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded text-[10px] font-orbitron text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                                    {item.name}
                                </div>
                            )}

                            <div className={`p-2 rounded-xl transition-all duration-300 ${isActive ? 'bg-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.3)]' : 'hover:bg-white/5'
                                }`}>
                                <Icon className={`w-6 h-6 ${isActive ? 'animate-pulse-slow' : ''}`} />
                            </div>

                            {/* Mobile Label (Hidden on Desktop usually, but good for accessibility/clarity on this compact dock) */}
                            <span className="text-[10px] mt-1 font-orbitron opacity-0 group-hover:opacity-100 transition-opacity absolute -bottom-6 sm:hidden">
                                {item.name}
                            </span>

                            {/* Active Indicator Dot */}
                            {isActive && (
                                <div className="absolute -bottom-1 w-1 h-1 bg-cyan-400 rounded-full shadow-[0_0_5px_#22d3ee]" />
                            )}
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
}
