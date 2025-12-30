"use client";

import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import Header from '../../components/Header';
import ChatTerminal from '../../components/Dashboard/ChatTerminal';

export default function ChatPage() {
    return (
        <div className="min-h-screen bg-black text-white font-sans selection:bg-purple-500/30">
            {/* Background Elements */}
            <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(76,29,149,0.1),rgba(0,0,0,1))] pointer-events-none" />
            <div className="fixed inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))] opacity-20 pointer-events-none" />

            <div className="relative z-10 p-6 max-w-[1600px] mx-auto space-y-6">
                <Header />

                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    {/* Left Sidebar - Menu Placeholders or Context info */}
                    <div className="space-y-6 hidden md:block">
                        <Link
                            href="/"
                            className="glass-button glass-button-secondary w-full flex items-center justify-center p-3 rounded-lg group transition-all hover:bg-white/5"
                        >
                            <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
                            <span>Back to Dashboard</span>
                        </Link>

                        <div className="glass-panel p-6 border-l-4 border-l-purple-500">
                            <h3 className="text-lg font-bold mb-2 text-purple-200">System Link</h3>
                            <div className="space-y-2 text-sm text-gray-400">
                                <p>Status: <span className="text-green-400">ONLINE</span></p>
                                <p>Encryption: <span className="text-blue-400">AES-256</span></p>
                                <p>Latency: <span className="text-green-400">12ms</span></p>
                            </div>
                        </div>

                        <div className="glass-panel p-6">
                            <h3 className="text-lg font-bold mb-4 text-cyan-200">Available Commands</h3>
                            <ul className="space-y-2 text-xs font-mono text-gray-400">
                                <li className="p-2 hover:bg-white/5 rounded cursor-pointer transition-colors border border-transparent hover:border-white/10">
                                    <span className="text-cyan-400">status</span> - Check agent status
                                </li>
                                <li className="p-2 hover:bg-white/5 rounded cursor-pointer transition-colors border border-transparent hover:border-white/10">
                                    <span className="text-cyan-400">start</span> - Initialize agent
                                </li>
                                <li className="p-2 hover:bg-white/5 rounded cursor-pointer transition-colors border border-transparent hover:border-white/10">
                                    <span className="text-cyan-400">stop</span> - Emergency stop
                                </li>
                                <li className="p-2 hover:bg-white/5 rounded cursor-pointer transition-colors border border-transparent hover:border-white/10">
                                    <span className="text-cyan-400">optimize</span> - Run optimization
                                </li>
                                <li className="p-2 hover:bg-white/5 rounded cursor-pointer transition-colors border border-transparent hover:border-white/10">
                                    <span className="text-cyan-400">schedule</span> - View schedule
                                </li>
                            </ul>
                        </div>
                    </div>

                    {/* Main Chat Area */}
                    <div className="md:col-span-3">
                        <ChatTerminal />
                    </div>
                </div>
            </div>
        </div>
    );
}
