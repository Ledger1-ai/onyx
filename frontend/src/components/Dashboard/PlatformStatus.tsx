"use client";

import React, { useState, useEffect } from 'react';
import { LayoutGrid, Smartphone, Bot, XCircle, Twitter, Linkedin, Facebook } from 'lucide-react';
import Modal from '@/components/ui/Modal';

interface PlatformState {
    api: boolean;
    bot: boolean;
}

interface AuthStatus {
    twitter: PlatformState;
    linkedin: PlatformState;
    facebook: PlatformState;
    instagram: PlatformState;
}

interface PlatformStatusProps {
    activeMode: string;
}

const INITIAL_STATE = {
    twitter: { api: false, bot: false },
    linkedin: { api: false, bot: false },
    facebook: { api: false, bot: false },
    instagram: { api: false, bot: false }
};

export default function PlatformStatus({ activeMode }: PlatformStatusProps) {
    const [status, setStatus] = useState<AuthStatus>(INITIAL_STATE);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoginLoading, setIsLoginLoading] = useState(false);

    // Modal State
    const [modal, setModal] = useState({
        isOpen: false,
        title: '',
        content: '',
        onConfirm: null as (() => void) | null,
        isConfirmType: false
    });

    const closeModal = () => setModal(prev => ({ ...prev, isOpen: false }));
    const showMessage = (title: string, content: string) =>
        setModal({ isOpen: true, title, content, onConfirm: null, isConfirmType: false });

    const showConfirm = (title: string, content: string, onConfirm: () => void) =>
        setModal({ isOpen: true, title, content, onConfirm, isConfirmType: true });

    const fetchStatus = async () => {
        try {
            const res = await fetch('/api/auth/status');
            if (res.ok) {
                const data = await res.json();
                setStatus(data);
            }
        } catch (error) {
            console.error('Failed to fetch auth status:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const connectApp = (platform: 'linkedin' | 'facebook' | 'twitter') => {
        window.location.href = `/api/auth/connect/${platform}`;
    };

    const launchBotLogin = async (platform: string) => {
        try {
            setIsLoginLoading(true);
            const res = await fetch(`/api/auth/${platform}/login`, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                showMessage("Bot Initiated", `Login process launched for ${platform}. Please follow the instructions in the new window.`);
            } else {
                showMessage("Error", `Failed to launch login: ${data.message}`);
            }
        } catch (error) {
            showMessage("System Error", 'Failed to communicate with server.');
        } finally {
            setIsLoginLoading(false);
        }
    };

    const disconnectApi = (platform: string) => {
        showConfirm(
            "Disconnect API?",
            `Are you sure you want to revoke API access for ${platform}? This will stop automated posting via API.`,
            async () => {
                try {
                    const res = await fetch(`/api/auth/disconnect/${platform}`, { method: 'POST' });
                    if (res.ok) {
                        fetchStatus();
                        closeModal();
                    } else {
                        showMessage("Error", "Failed to disconnect API");
                    }
                } catch (e) {
                    showMessage("Error", "Network error disconnecting API");
                }
            }
        );
    };

    const disconnectBot = (platform: string) => {
        showConfirm(
            "Disconnect Agent?",
            `Are you sure you want to disconnect the '${platform}' Agent session? You may need to re-login to perform specific bot tasks.`,
            async () => {
                try {
                    const res = await fetch(`/api/auth/${platform}/disconnect`, { method: 'POST' });
                    if (res.ok) {
                        fetchStatus();
                        closeModal();
                    } else {
                        showMessage("Error", "Failed to disconnect Bot session");
                    }
                } catch (e) {
                    showMessage("Error", "Network error disconnecting Bot");
                }
            }
        );
    };

    const isAfterlife = activeMode === 'afterlife';

    const renderPlatformRow = (
        name: string,
        icon: React.ReactNode,
        statusRaw: PlatformState | undefined,
        platformId: 'linkedin' | 'facebook' | 'twitter',
        botId: string | null,
        colorClass: string
    ) => {
        const status = statusRaw || { api: false, bot: false };

        return (
            <div className={`p-3 rounded-lg border transition-all ${isAfterlife ? 'bg-red-950/20 border-red-500/30' : 'bg-gray-800/50 border-gray-700/50'}`}>
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                        {icon}
                        <span className="text-sm text-gray-300 font-mono">{name}</span>
                    </div>
                </div>

                <div className={`grid ${botId ? 'grid-cols-2' : 'grid-cols-1'} gap-2 mt-2`}>
                    {/* API Channel */}
                    <div className="bg-black/20 p-2 rounded border border-gray-700/30 flex flex-col items-center relative">
                        <span className="text-[10px] uppercase text-gray-500 font-bold mb-1 flex items-center">
                            <Smartphone className="w-3 h-3 mr-1" /> API APP
                        </span>
                        <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${status.api ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : 'bg-gray-600'}`}></div>
                            {status.api ? (
                                <div className="flex items-center">
                                    <span className="text-xs text-green-400 font-mono mr-2">LINKED</span>
                                    <button onClick={() => disconnectApi(platformId)} className="text-gray-500 hover:text-red-400" title="Disconnect">
                                        <XCircle className="w-3 h-3" />
                                    </button>
                                </div>
                            ) : (
                                <button
                                    onClick={() => connectApp(platformId)}
                                    className={`text-[10px] px-2 py-0.5 rounded border ${colorClass} hover:opacity-80 transition-opacity text-white`}
                                >
                                    CONNECT
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Bot Channel (Conditional) */}
                    {botId && (
                        <div className="bg-black/20 p-2 rounded border border-gray-700/30 flex flex-col items-center">
                            <span className="text-[10px] uppercase text-gray-500 font-bold mb-1 flex items-center">
                                <Bot className="w-3 h-3 mr-1" /> AGENT
                            </span>
                            <div className="flex items-center space-x-2">
                                <div className={`w-2 h-2 rounded-full ${status.bot ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : 'bg-gray-600'}`}></div>
                                {status.bot ? (
                                    <div className="flex items-center">
                                        <span className="text-xs text-green-400 font-mono mr-2">ONLINE</span>
                                        <button onClick={() => disconnectBot(platformId)} className="text-gray-500 hover:text-red-400" title="Disconnect">
                                            <XCircle className="w-3 h-3" />
                                        </button>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => launchBotLogin(platformId)}
                                        // Disable launch button if already trying to login
                                        disabled={isLoginLoading}
                                        className={`text-[10px] px-2 py-0.5 rounded border border-red-600 bg-red-600/20 hover:bg-red-500/30 transition-colors text-red-300 ${isLoginLoading ? 'opacity-50 cursor-wait' : ''}`}
                                    >
                                        {isLoginLoading ? 'LAUNCHING...' : 'LAUNCH'}
                                    </button>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="glass-panel p-4">
            <h3 className="text-lg font-bold text-white mb-4 font-orbitron flex items-center">
                <LayoutGrid className="w-5 h-5 mr-2 text-cyan-400" />
                PLATFORM STATUS
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {renderPlatformRow('Twitter / X', <Twitter className="w-5 h-5 text-sky-400" />, status.twitter, 'twitter', 'twitter', 'border-sky-500 bg-sky-500/20')}
                {renderPlatformRow('LinkedIn', <Linkedin className="w-5 h-5 text-blue-400" />, status.linkedin, 'linkedin', 'linkedin', 'border-blue-500 bg-blue-500/20')}
                {renderPlatformRow('Meta', <Facebook className="w-5 h-5 text-blue-600" />, status.facebook, 'facebook', null, 'border-blue-600 bg-blue-600/20')}
            </div>

            <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center text-xs text-gray-500 font-mono">
                <span>IDENTITY LAYER: ACTIVE</span>
                <span className={isLoading ? 'animate-pulse text-cyan-500' : 'text-green-500'}>
                    {isLoading ? 'SYNCING...' : 'SYSTEM READY'}
                </span>
            </div>

            <Modal
                isOpen={modal.isOpen}
                onClose={closeModal}
                title={modal.title}
                footer={
                    modal.isConfirmType ? (
                        <>
                            <button onClick={closeModal} className="px-4 py-2 rounded text-gray-400 hover:text-white hover:bg-white/5 transition-colors text-sm">
                                Cancel
                            </button>
                            <button onClick={modal.onConfirm!} className="px-4 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-bold shadow-lg shadow-cyan-900/20">
                                Confirm
                            </button>
                        </>
                    ) : (
                        <button onClick={closeModal} className="px-4 py-2 rounded bg-gray-700 hover:bg-gray-600 text-white text-sm">
                            Close
                        </button>
                    )
                }
            >
                <p className="text-sm leading-relaxed">{modal.content}</p>
            </Modal>
        </div>
    );
}
