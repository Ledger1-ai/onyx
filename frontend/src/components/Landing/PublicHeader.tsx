"use client";

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ArrowRight } from 'lucide-react';

export default function PublicHeader() {
    return (
        <header className="fixed top-0 w-full z-50 bg-black/50 backdrop-blur-lg border-b border-white/10">
            <div className="max-w-7xl mx-auto px-6 h-24 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="relative w-64 h-16 flex items-center justify-center">
                        <Image
                            src="/BasaltOnyxWide.png"
                            alt="BasaltONYX Logo"
                            width={250}
                            height={64}
                            className="object-contain drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                        />
                    </div>
                    {/* <span className="font-orbitron font-bold text-2xl text-white tracking-widest">
                        LEDGER<span className="text-cyan-400">1</span>.AI
                    </span> */}
                </div>

                <nav className="hidden md:flex items-center gap-8">
                    {['Features', 'Intelligence', 'Ecosystem', 'Roadmap'].map((item) => (
                        <a key={item} href={`#${item.toLowerCase()}`} className="text-gray-300 hover:text-cyan-400 font-rajdhani font-medium tracking-wide transition-colors">
                            {item.toUpperCase()}
                        </a>
                    ))}
                </nav>

                <Link
                    href="/underworld/gateway"
                    className="group relative px-6 py-2 bg-white/5 border border-white/20 hover:border-cyan-500/50 rounded-full transition-all overflow-hidden"
                >
                    <div className="absolute inset-0 bg-cyan-500/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                    <span className="relative flex items-center gap-2 font-rajdhani font-bold text-cyan-400 group-hover:text-white uppercase tracking-wider">
                        Enter Underworld
                        <ArrowRight className="w-4 h-4" />
                    </span>
                </Link>
            </div>
        </header>
    );
}
