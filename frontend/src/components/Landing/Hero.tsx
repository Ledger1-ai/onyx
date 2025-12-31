"use client";

import React from 'react';
import Link from 'next/link';
import { Sparkles, Bot, Zap } from 'lucide-react';

export default function Hero() {
    return (
        <section className="relative min-h-[90vh] flex items-center justify-center pt-30 overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,var(--tw-gradient-stops))] from-cyan-900/20 via-black to-black" />
            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20" />

            <div className="relative max-w-7xl mx-auto px-6 text-center z-10">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8 animate-fade-in-up">
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    <span className="text-sm font-rajdhani text-gray-300 tracking-wider">NEXT GEN AGENTIC INTELLIGENCE</span>
                </div>

                <h1 className="text-6xl md:text-8xl font-orbitron font-bold text-white mb-6 leading-tight tracking-tight">
                    AUTOMATE THE <br />
                    <span className="text-transparent bg-clip-text bg-linear-to-r from-cyan-400 via-purple-500 to-pink-500 animate-gradient-x">
                        IMPOSSIBLE
                    </span>
                </h1>

                <p className="text-xl md:text-2xl font-rajdhani text-gray-400 mb-10 max-w-3xl mx-auto leading-relaxed">
                    Unleash the power of BasaltOnyx. An autonomous social intelligence platform designed to scale your digital presence through advanced algorithmic strategies.
                </p>

                <div className="flex flex-col md:flex-row items-center justify-center gap-6">
                    <Link
                        href="/underworld/gateway"
                        className="px-8 py-4 bg-cyan-500 hover:bg-cyan-400 text-black font-orbitron font-bold rounded-lg shadow-[0_0_30px_rgba(6,182,212,0.4)] hover:shadow-[0_0_50px_rgba(6,182,212,0.6)] transition-all transform hover:-translate-y-1"
                    >
                        DEPLOY AGENTS
                    </Link>
                    <button className="px-8 py-4 bg-white/5 border border-white/10 hover:bg-white/10 text-white font-orbitron font-bold rounded-lg backdrop-blur-sm transition-all">
                        VIEW DOCUMENTATION
                    </button>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-20 border-t border-white/10 pt-10">
                    {[
                        { label: 'Active Agents', value: '250+', icon: Bot },
                        { label: 'Ops / Sec', value: '1.2M', icon: Zap },
                        { label: 'Uptime', value: '99.9%', icon: Sparkles },
                        { label: 'Networks', value: '12', icon: Bot },
                    ].map((stat, i) => (
                        <div key={i} className="flex flex-col items-center">
                            <stat.icon className="w-6 h-6 text-cyan-500 mb-2" />
                            <span className="text-3xl font-orbitron font-bold text-white">{stat.value}</span>
                            <span className="text-sm font-rajdhani text-gray-500 uppercase tracking-widest">{stat.label}</span>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
