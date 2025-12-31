"use client";

import React, { useState } from 'react';
import { Calendar, ChevronLeft, ChevronRight, Clock, CheckCircle, XCircle, AlertCircle, Lock, Facebook, Instagram, Linkedin, Twitter } from 'lucide-react';
import { format } from 'date-fns';

interface MissionScheduleProps {
    schedule: any;
    onDateChange?: (date: string) => void;
    afterlifeEnabled?: boolean;
    authStatus?: any;
}

export default function MissionSchedule({ schedule, onDateChange, afterlifeEnabled = false, authStatus }: MissionScheduleProps) {
    const [selectedDate, setSelectedDate] = useState(new Date());

    const handleDateChange = (days: number) => {
        const newDate = new Date(selectedDate);
        newDate.setDate(selectedDate.getDate() + days);
        setSelectedDate(newDate);
        if (onDateChange) {
            onDateChange(format(newDate, 'yyyy-MM-dd'));
        }
    };

    const slots = schedule?.slots || [];

    return (
        <div className="glass-panel p-0 h-[calc(100vh-200px)] flex flex-col widget-fluid">
            {/* Header */}
            <div className="p-4 border-b border-cyan-500/20 sticky top-0 bg-gray-900/90 z-10 backdrop-blur-md">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-bold text-white font-orbitron flex items-center">
                        <Calendar className="w-5 h-5 mr-2 text-cyan-500" />
                        MISSION SCHEDULE
                    </h3>
                    <span className="text-xs font-mono text-cyan-400/70">{format(selectedDate, 'yyyy-MM-dd')}</span>
                </div>

                <div className="flex items-center justify-between bg-gray-800/50 p-1 rounded-lg">
                    <button onClick={() => handleDateChange(-1)} className="p-1 hover:bg-cyan-500/10 rounded text-cyan-400">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <span className="text-sm font-bold text-white">{format(selectedDate, 'MMMM d, yyyy')}</span>
                    <button onClick={() => handleDateChange(1)} className="p-1 hover:bg-cyan-500/10 rounded text-cyan-400">
                        <ChevronRight className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Timeline */}
            <div className="flex-1 overflow-y-auto p-4 pr-6 nice-scroll">
                <div className="relative pl-4 border-l border-cyan-500/20 space-y-6">
                    {slots.length === 0 ? (
                        <div className="text-center text-gray-500 py-10 font-mono text-xs">NO MISSIONS SCHEDULED</div>
                    ) : (
                        slots.map((slot: any) => {
                            // Identify Platform & Risk
                            let platform = 'GENERIC';
                            const typeRaw = slot.activity_type || '';
                            const type = typeRaw.toString().toUpperCase();

                            if (slot.platform) {
                                platform = slot.platform === 'TWITTER' ? 'TWITTER/X' : slot.platform;
                            } else {
                                // Fallback Heuristics
                                if (type.includes('LINKEDIN')) platform = 'LINKEDIN';
                                else if (type.includes('TWEET') || type === 'THREAD' || type.includes('REPLY') || type.includes('SCROLL') || type.includes('SEARCH')) platform = 'TWITTER/X';
                                else if (type.includes('FACEBOOK')) platform = 'FACEBOOK';
                                else if (type.includes('INSTAGRAM')) platform = 'INSTAGRAM';
                                else if (type.includes('CONTENT') || type.includes('RADAR') || type.includes('ANALYTICS') || type.includes('MONITOR') || type.includes('PERFORMANCE') || type.includes('STRATEGY')) platform = 'SYSTEM';
                            }

                            // Risk Logic (Task Type Analysis)
                            const isTwitter = platform === 'TWITTER/X';
                            const riskyKeywords = ['ENGAGE', 'SEARCH', 'FOLLOW', 'CONNECT', 'RADAR'];
                            const isRiskyAction = riskyKeywords.some(k => type.includes(k));

                            // CHECK 1: Is the required subsystem connected?
                            const isConnectionReady = (() => {
                                if (!authStatus) return true; // Loading assumption
                                // Access directly by platform key as per new API structure
                                const tw = authStatus.twitter || {};
                                const li = authStatus.linkedin || {};
                                const fb = authStatus.facebook || {};
                                const ig = authStatus.instagram || {};

                                if (platform === 'TWITTER/X') {
                                    if (isRiskyAction) return tw.bot; // Risky needs Bot
                                    return tw.api || tw.bot; // Content can be either
                                }
                                if (platform === 'LINKEDIN') {
                                    if (isRiskyAction) return li.bot; // Risky needs Bot
                                    return li.api || li.bot; // Content can be either
                                }
                                if (platform === 'FACEBOOK') return fb.api;
                                if (platform === 'INSTAGRAM') return ig.api;
                                return true; // System tasks
                            })();

                            // CHECK 2: Is the required mode enabled (i.e. Afterlife/Agent Mode for Bot tasks)?
                            const isModeReady = (() => {
                                // SYSTEM
                                if (platform === 'SYSTEM') return true;

                                // META (Facebook/Instagram)
                                if (platform === 'FACEBOOK' || platform === 'INSTAGRAM') {
                                    // Viewing Stories/Reels implies Browser/Bot -> Requires Afterlife
                                    if (type.includes('VIEW')) return afterlifeEnabled;
                                    return true; // Posts/Analytics are API -> Safe
                                }

                                // LINKEDIN (Hybrid)
                                if (platform === 'LINKEDIN') {
                                    // Posts/Articles -> API -> Safe
                                    if (type.includes('ARTICLE') || type.includes('CONTENT') || type.includes('POST')) return true;
                                    // Engage/Connect/Monitor -> Bot -> Requires Afterlife
                                    return afterlifeEnabled;
                                }

                                // TWITTER (Bot/Agent Only as per user)
                                if (platform === 'TWITTER/X') {
                                    return afterlifeEnabled;
                                }

                                return true;
                            })();

                            // Combined Lock
                            const isLocked = !isConnectionReady || !isModeReady;

                            // Conditional Styling or Status Overrides
                            let statusColor =
                                slot.status === 'completed' ? 'text-green-400 border-green-500/50 bg-green-500/10' :
                                    slot.status === 'in_progress' ? 'text-cyan-400 border-cyan-500/50 bg-cyan-500/10' :
                                        slot.status === 'failed' ? 'text-red-400 border-red-500/50 bg-red-500/10' :
                                            'text-gray-400 border-gray-600/50 bg-gray-800/30';

                            // Make visual lock more distinct but legible
                            if (isLocked) {
                                statusColor = 'text-gray-500 border-red-900/30 bg-red-950/20 grayscale-[0.5]';
                            }

                            const icon =
                                isLocked ? <Lock className="w-4 h-4 text-red-500" /> :
                                    platform === 'FACEBOOK' ? <Facebook className="w-4 h-4 text-blue-600" /> :
                                        platform === 'INSTAGRAM' ? <Instagram className="w-4 h-4 text-pink-500" /> :
                                            platform === 'LINKEDIN' ? <Linkedin className="w-4 h-4 text-blue-400" /> :
                                                platform === 'TWITTER/X' ? <Twitter className="w-4 h-4 text-sky-400" /> :
                                                    slot.status === 'completed' ? <CheckCircle className="w-4 h-4 text-green-500" /> :
                                                        slot.status === 'in_progress' ? <Clock className="w-4 h-4 text-cyan-500 animate-spin-slow" /> :
                                                            slot.status === 'failed' ? <XCircle className="w-4 h-4 text-red-500" /> :
                                                                <AlertCircle className="w-4 h-4 text-gray-500" />;

                            const platformColor =
                                platform === 'LINKEDIN' ? 'text-blue-400' :
                                    platform === 'TWITTER/X' ? 'text-sky-400' :
                                        platform === 'FACEBOOK' ? 'text-blue-600' :
                                            platform === 'INSTAGRAM' ? 'text-pink-500' :
                                                platform === 'SYSTEM' ? 'text-purple-400' : 'text-gray-400';

                            return (
                                <div key={slot.slot_id} className={`relative pl-4 group ${isLocked ? 'pointer-events-none' : ''}`}>
                                    {/* Connector Dot - Centered Vertically */}
                                    <div className={`absolute -left-[21px] top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 bg-gray-900 z-10 ${isLocked ? 'border-red-900' :
                                        slot.status === 'completed' ? 'border-green-500 shadow-[0_0_10px_#00ff00]' :
                                            slot.status === 'in_progress' ? 'border-cyan-500 shadow-[0_0_10px_#00ffff] animate-pulse' :
                                                'border-gray-600'
                                        }`}></div>

                                    <div className={`glass-card p-3 rounded-lg border ${statusColor} transition-all duration-300 ${!isLocked && 'hover:translate-x-1'}`}>
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <div className="flex items-center space-x-2 mb-1">
                                                    {icon}
                                                    <span className={`text-sm font-bold uppercase font-orbitron tracking-wide ${isLocked ? 'decoration-red-500/50 line-through text-gray-500' : ''}`}>
                                                        {slot.activity_type.replace(/_/g, ' ')}
                                                    </span>
                                                    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border border-current font-bold ${isLocked ? 'text-red-500 border-red-500 bg-red-950/50 opacity-100' : platformColor + ' opacity-70'}`}>
                                                        {platform} {isLocked ? '- DISABLED' : ''}
                                                    </span>
                                                </div>
                                                <div className="text-xs opacity-70 font-mono flex items-center">
                                                    <Clock className="w-3 h-3 mr-1" />
                                                    {format(new Date(slot.start_time), 'HH:mm')} - {format(new Date(slot.end_time), 'HH:mm')}
                                                </div>
                                            </div>
                                            <div className="text-xs font-bold opacity-50 px-2 py-1 rounded bg-black/20">
                                                P{slot.priority}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>
        </div>
    );
}
