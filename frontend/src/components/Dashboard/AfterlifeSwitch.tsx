"use client";

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { Activity, AlertTriangle } from 'lucide-react';

interface AfterlifeSwitchProps {
    onToggle?: () => void;
}

export default function AfterlifeSwitch({ onToggle }: AfterlifeSwitchProps) {
    const [enabled, setEnabled] = useState(false);
    const [loading, setLoading] = useState(false);

    // Initial check
    useEffect(() => {
        checkStatus();
    }, []);

    const checkStatus = async () => {
        try {
            const res = await fetch('/api/control/afterlife-mode');
            const data = await res.json();
            if (data.status === 'success' || data.enabled !== undefined) {
                setEnabled(data.enabled);
                // Apply visual theme if enabled initially
                if (data.enabled) {
                    document.documentElement.classList.add('afterlife-active');
                } else {
                    document.documentElement.classList.remove('afterlife-active');
                }
            }
        } catch (error) {
            console.error("Failed to fetch Afterlife status", error);
        }
    };

    const toggleMode = async () => {
        if (loading) return;
        setLoading(true);

        try {
            // Mock system status data
            const newState = !enabled;
            const res = await fetch('/api/control/afterlife-mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: newState })
            });

            await res.json();
            if (res.ok) {
                setEnabled(newState);

                // Toggle global theme class
                if (newState) {
                    document.documentElement.classList.add('afterlife-active');
                } else {
                    document.documentElement.classList.remove('afterlife-active');
                }

                if (onToggle) onToggle();
            }
        } catch (error) {
            console.error("Failed to toggle mode", error);
            // Revert on error or handle it
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={`relative p-1 rounded-full transition-all duration-700 ease-in-out ${enabled ? 'bg-red-950/80 shadow-[0_0_30px_rgba(220,38,38,0.5)]' : 'bg-gray-900 border border-gray-700'}`}>
            <button
                onClick={toggleMode}
                disabled={loading}
                className={`
                    relative flex items-center w-64 h-16 rounded-full transition-all duration-700 ease-in-out
                    ${enabled ? 'bg-black' : 'bg-gray-800'}
                `}
            >
                {/* Background Glitch/Noise (Active Only) */}
                {enabled && (
                    <div className="absolute inset-0 rounded-full overflow-hidden opacity-20 pointer-events-none">
                        <div className="absolute inset-0 bg-[url('/tech-texture.png')] mix-blend-overlay" />
                    </div>
                )}

                {/* Text Container - Absolute Layer for perfect centering */}

                {/* AFTERLIFE Text (Visible on LEFT when Active) -> Padding Right to account for Knob */}
                <div
                    className={`
                        absolute inset-0 flex items-center justify-center pr-16 pointer-events-none z-10
                        transition-all duration-500 ease-out
                        ${enabled
                            ? 'opacity-100 translate-x-0 scale-100'
                            : 'opacity-0 -translate-x-10 scale-90'}
                    `}
                >
                    <span className="text-2xl font-black font-orbitron tracking-widest text-red-500 whitespace-nowrap filter drop-shadow-[0_0_5px_rgba(220,38,38,0.5)]">
                        AFTERLIFE
                    </span>
                </div>

                {/* SYSTEM SAFE Text (Visible on RIGHT when Safe) -> Padding Left to account for Knob */}
                <div
                    className={`
                        absolute inset-0 flex items-center justify-center pl-16 pointer-events-none z-10
                        transition-all duration-500 ease-out
                        ${!enabled
                            ? 'opacity-100 translate-x-0 scale-100'
                            : 'opacity-0 translate-x-10 scale-90'}
                    `}
                >
                    <span className="text-2xl font-black font-orbitron tracking-widest text-cyan-400 whitespace-nowrap filter drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]">
                        SYSTEM SAFE
                    </span>
                </div>


                <div
                    className={`
                        absolute top-1 bottom-1 w-14 rounded-full flex items-center justify-center shadow-lg z-20
                        transition-all duration-700 cubic-bezier(0.34, 1.56, 0.64, 1)
                        ${enabled
                            ? 'translate-x-[calc(16rem-3.75rem)] bg-red-600 text-black rotate-360 shadow-[0_0_20px_rgba(220,38,38,0.8)]'
                            : 'translate-x-1 bg-cyan-500 text-white rotate-0 shadow-[0_0_15px_rgba(34,211,238,0.5)]'}
                    `}
                    style={{ transitionTimingFunction: "cubic-bezier(0.34, 1.56, 0.64, 1)" }}
                >
                    {loading ? (
                        <Activity className="w-6 h-6 animate-spin" />
                    ) : enabled ? (
                        <div className="relative w-8 h-8">
                            <Image
                                src="/anubislogo.png"
                                alt="Anubis"
                                fill
                                sizes="32px"
                                className="object-contain brightness-0" // Black logo on Red
                            />
                        </div>
                    ) : (
                        <div className="w-3 h-3 rounded-full bg-white shadow-[0_0_10px_white]" />
                    )}
                </div>
            </button>


            {/* Tooltip / Warning */}
            <div className="absolute -bottom-6 left-0 w-full text-center">
                {enabled && (
                    <span className="text-[10px] text-red-500 font-mono tracking-wider animate-pulse flex items-center justify-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> PROTOCOL MYTHOS ACTIVE
                    </span>
                )}
            </div>
        </div>
    );
}
