
"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lock, ScanFace, ChevronRight, AlertTriangle } from 'lucide-react';
import Image from 'next/image';

export default function GatewayPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();

            if (data.success) {
                // Determine redirect based on role or default
                router.push('/underworld/dashboard');
            } else {
                setError(data.error || 'Access Denied');
            }
        } catch (err) {
            setError('System Connection Error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="w-full h-screen bg-black flex items-center justify-center relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 z-0">
                <div className="absolute top-0 left-0 w-full h-[1px] bg-cyan-500/20 shadow-[0_0_20px_#00ffff]" />
                <div className="absolute bottom-0 right-0 w-full h-[1px] bg-cyan-500/20 shadow-[0_0_20px_#00ffff]" />
                {/* Grid Effect */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(6,182,212,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(6,182,212,0.03)_1px,transparent_1px)] bg-[length:40px_40px]" />
                {/* Radial Glow */}
                <div className="absolute inset-0 bg-radial-gradient from-cyan-900/10 via-black to-black" />
            </div>

            {/* Login Container */}
            <div className="relative z-10 w-full max-w-md p-8">
                {/* Logo / Header */}
                <div className="text-center mb-10">
                    <div className="w-20 h-20 mx-auto mb-6 relative animate-pulse-slow">
                        <div className="absolute inset-0 border border-cyan-500/30 rounded-lg rotate-45" />
                        <div className="absolute inset-0 border border-cyan-500/30 rounded-lg -rotate-12" />
                        <div className="absolute inset-2 bg-black flex items-center justify-center rounded border border-cyan-500/50 shadow-[0_0_30px_rgba(6,182,212,0.3)]">
                            <Image
                                src="/bssymbol.png"
                                alt="Logo"
                                width={40}
                                height={40}
                                className="object-contain brightness-0 invert opacity-90"
                            />
                        </div>
                    </div>
                    <h1 className="text-4xl font-bold text-white font-orbitron tracking-[0.2em] mb-2">GATEWAY</h1>
                    <p className="text-xs text-cyan-500/70 font-mono tracking-widest uppercase">Restricted Access // Authorized Personnel Only</p>
                </div>

                {/* Form */}
                <div className="backdrop-blur-md bg-white/5 border border-white/10 p-8 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] relative group">
                    {/* Corner Accents */}
                    <div className="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-cyan-500/50" />
                    <div className="absolute -top-1 -right-1 w-4 h-4 border-t-2 border-r-2 border-cyan-500/50" />
                    <div className="absolute -bottom-1 -left-1 w-4 h-4 border-b-2 border-l-2 border-cyan-500/50" />
                    <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-cyan-500/50" />

                    <form onSubmit={handleLogin} className="space-y-6">
                        {error && (
                            <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-3 rounded font-mono text-xs flex items-center animate-shake">
                                <AlertTriangle className="w-4 h-4 mr-2" />
                                {error}
                            </div>
                        )}

                        <div className="space-y-1">
                            <label className="text-[10px] font-bold text-cyan-400/80 font-mono uppercase tracking-wider ml-1">Identity</label>
                            <div className="relative group/input">
                                <div className="absolute left-3 top-3 text-gray-500 group-focus-within/input:text-cyan-400 transition-colors">
                                    <ScanFace className="w-5 h-5" />
                                </div>
                                <input
                                    type="email" required
                                    value={email} onChange={e => setEmail(e.target.value)}
                                    placeholder="Enter your credentials"
                                    className="w-full bg-black/40 border border-gray-700 rounded-lg py-3 pl-10 pr-4 text-white placeholder-gray-600 focus:border-cyan-500 focus:bg-black/60 focus:outline-none transition-all font-mono text-sm"
                                />
                            </div>
                        </div>

                        <div className="space-y-1">
                            <label className="text-[10px] font-bold text-cyan-400/80 font-mono uppercase tracking-wider ml-1">Key</label>
                            <div className="relative group/input">
                                <div className="absolute left-3 top-3 text-gray-500 group-focus-within/input:text-cyan-400 transition-colors">
                                    <Lock className="w-5 h-5" />
                                </div>
                                <input
                                    type="password" required
                                    value={password} onChange={e => setPassword(e.target.value)}
                                    placeholder="Enter access key"
                                    className="w-full bg-black/40 border border-gray-700 rounded-lg py-3 pl-10 pr-4 text-white placeholder-gray-600 focus:border-cyan-500 focus:bg-black/60 focus:outline-none transition-all font-mono text-sm"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/50 text-cyan-400 hover:text-cyan-300 py-3 rounded-lg font-bold font-orbitron tracking-widest uppercase transition-all flex items-center justify-center group/btn relative overflow-hidden"
                        >
                            <span className="relative z-10 flex items-center">
                                {loading ? 'Authenticating...' : 'Initialize Session'}
                                {!loading && <ChevronRight className="w-4 h-4 ml-2 group-hover/btn:translate-x-1 transition-transform" />}
                            </span>
                            <div className="absolute inset-0 bg-cyan-500/10 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                        </button>
                    </form>
                </div>

                <div className="mt-8 text-center text-[10px] text-gray-600 font-mono">
                    SECURE CONNECTION ESTABLISHED // V.2.4.0
                </div>
            </div>
        </div>
    );
}
