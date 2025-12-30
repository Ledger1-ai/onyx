"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Terminal as TerminalIcon, Loader2, Trash2 } from 'lucide-react';

interface ChatMessage {
    id: string;
    text: string;
    sender: 'user' | 'agent' | 'system';
    timestamp: Date;
    type?: 'info' | 'success' | 'warning' | 'error';
}

export default function ChatTerminal() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);

    // Initialize welcome messages on client side to avoid hydration mismatch
    useEffect(() => {
        setMessages([
            {
                id: '1',
                text: 'ANUBIS Agent Verified. Secure Connection Established.',
                sender: 'system',
                timestamp: new Date(),
                type: 'success'
            },
            {
                id: '2',
                text: 'I am ready to receive commands. Type "help" for a list of available operations.',
                sender: 'agent',
                timestamp: new Date()
            }
        ]);
    }, []);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [pid, setPid] = useState<number | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        setPid(Math.floor(Math.random() * 9000) + 1000);
    }, []);

    const handleSendMessage = async (e?: React.FormEvent) => {
        e?.preventDefault();

        if (!inputValue.trim() || isLoading) return;

        const userCommand = inputValue.trim();
        setInputValue('');

        // Add user message
        const userMsg: ChatMessage = {
            id: Date.now().toString(),
            text: userCommand,
            sender: 'user',
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMsg]);
        setIsLoading(true);

        try {
            const response = await fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: userCommand })
            });

            const data = await response.json();

            // Add agent response
            const agentMsg: ChatMessage = {
                id: (Date.now() + 1).toString(),
                text: typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2),
                sender: 'agent',
                timestamp: new Date(),
                type: response.ok ? 'success' : 'error'
            };

            setMessages(prev => [...prev, agentMsg]);

        } catch (error) {
            const errorMsg: ChatMessage = {
                id: (Date.now() + 1).toString(),
                text: `Error connecting to agent: ${error}`,
                sender: 'system',
                timestamp: new Date(),
                type: 'error'
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsLoading(false);
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    };

    const clearChat = () => {
        setMessages([
            {
                id: Date.now().toString(),
                text: 'Terminal cleared.',
                sender: 'system',
                timestamp: new Date(),
                type: 'info'
            }
        ]);
    };

    return (
        <div className="glass-panel p-0 flex flex-col h-[calc(100vh-140px)] relative overflow-hidden group">
            <div className="absolute inset-0 bg-black/40 -z-10" />

            {/* Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/20">
                <div className="flex items-center">
                    <TerminalIcon className="w-5 h-5 text-purple-400 mr-2" />
                    <h2 className="text-lg font-bold text-white font-orbitron tracking-wider">
                        SECURE TERMINAL UPLINK
                    </h2>
                </div>
                <div className="flex items-center space-x-2">
                    <button
                        onClick={clearChat}
                        className="p-1.5 rounded-md hover:bg-white/10 text-white/50 hover:text-red-400 transition-colors"
                        title="Clear Terminal"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                    <div className="text-xs text-white/30 font-mono hidden md:block">
                        PID: {pid || '....'} | ENCRYPTED
                    </div>
                </div>
            </div>

            {/* Terminal Output */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-sm scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[85%] rounded-lg p-3 ${msg.sender === 'user'
                                ? 'bg-purple-500/20 border border-purple-500/30 text-purple-100 rounded-br-none'
                                : msg.sender === 'system'
                                    ? 'bg-gray-800/40 border-l-2 border-gray-500 text-gray-400 w-full'
                                    : 'bg-cyan-500/10 border border-cyan-500/20 text-cyan-100 rounded-bl-none'
                                } ${msg.type === 'error' ? 'border-red-500/50 text-red-200 bg-red-900/10' : ''}`}
                        >
                            {msg.sender !== 'user' && (
                                <div className="text-[10px] uppercase tracking-wider opacity-50 mb-1 font-bold flex items-center">
                                    {msg.sender === 'system' ? 'SYSTEM ADVISORY' : 'ANUBIS AGENT'}
                                    <span className="ml-2 font-normal normal-case opacity-70">
                                        {msg.timestamp.toLocaleTimeString()}
                                    </span>
                                </div>
                            )}
                            <div className="whitespace-pre-wrap wrap-break-word leading-relaxed">
                                {msg.sender === 'agent' && (
                                    <span className="text-cyan-500 mr-2">{'>'}</span>
                                )}
                                {msg.text}
                            </div>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-cyan-500/5 border border-cyan-500/10 text-cyan-100 rounded-lg p-3 rounded-bl-none flex items-center">
                            <Loader2 className="w-4 h-4 mr-2 animate-spin text-cyan-400" />
                            <span className="animate-pulse">Processing command...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-black/30 border-t border-white/10">
                <form onSubmit={handleSendMessage} className="relative flex items-center">
                    <div className="absolute left-4 text-cyan-500 font-mono">{'>'}</div>
                    <input
                        ref={inputRef}
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        className="w-full bg-black/40 border border-white/10 rounded-lg py-3 pl-10 pr-12 text-white font-mono focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 transition-all placeholder:text-white/20"
                        placeholder="Enter command..."
                        autoFocus
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!inputValue.trim() || isLoading}
                        className="absolute right-2 p-1.5 bg-cyan-500/20 hover:bg-cyan-500/40 text-cyan-400 rounded-md transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </form>
                <div className="text-center mt-2 text-[10px] text-white/20">
                    ANUBIS COMMAND INTERFACE v2.0 // AUTHORIZED PERSONNEL ONLY
                </div>
            </div>
        </div>
    );
}
