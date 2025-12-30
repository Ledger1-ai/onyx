"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lock, ArrowRight, ShieldAlert } from 'lucide-react';
import Link from 'next/link';

export default function LoginPage() {
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const router = useRouter();

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        // Simple gate for now - can be replaced with real auth later
        if (password === 'anubis' || password === 'admin') {
            router.push('/underworld/dashboard');
        } else {
            setError('ACCESS DENIED: Invalid Credentials');
        }
    };

    return (
        <div className="min-h-screen bg-black flex items-center justify-center relative overflow-hidden">
            {/* Background Effects */}

            <div className="absolute inset-0 bg-linear-to-t from-cyan-900/10 to-transparent" />

            <div className="relative z-10 w-full max-w-md p-8">
                <div className="mb-8 text-center">
                    <div className="w-16 h-16 bg-cyan-500/10 border border-cyan-500/30 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
                        <Lock className="w-8 h-8 text-cyan-400" />
                    </div>
                    <h1 className="text-3xl font-orbitron font-bold text-white tracking-widest mb-2">SECURE LOGIN</h1>
                    <p className="text-gray-400 font-rajdhani">Restricted Access Area</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-6">
                    <div className="relative group">
                        <div className="absolute -inset-0.5 bg-linear-to-r from-cyan-500 to-purple-600 rounded-lg blur opacity-25 group-hover:opacity-50 transition duration-200"></div>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="ENTER PASSCODE"
                            className="relative w-full bg-black/80 border border-white/10 text-white px-6 py-4 rounded-lg focus:outline-none focus:border-cyan-500 font-orbitron tracking-widest placeholder-gray-600"
                            autoFocus
                        />
                    </div>

                    {error && (
                        <div className="flex items-center gap-2 text-red-500 bg-red-500/10 p-3 rounded border border-red-500/20 animate-shake">
                            <ShieldAlert className="w-4 h-4" />
                            <span className="text-sm font-rajdhani font-bold">{error}</span>
                        </div>
                    )}

                    <button
                        type="submit"
                        className="w-full bg-cyan-500 hover:bg-cyan-400 text-black font-orbitron font-bold py-4 rounded-lg shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all flex items-center justify-center gap-2 group"
                    >
                        AUTHENTICATE
                        <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>
                </form>

                <div className="mt-8 text-center">
                    <Link href="/" className="text-gray-500 hover:text-cyan-400 text-sm font-rajdhani transition-colors">
                        ← RETURN TO SURFACE
                    </Link>
                </div>
            </div>
        </div>
    );
}
