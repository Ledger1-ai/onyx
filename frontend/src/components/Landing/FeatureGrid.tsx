"use client";

import React from 'react';
import { Cpu, Globe, Shield, Zap, BarChart3, Users } from 'lucide-react';

const features = [
    {
        title: "Autonomous Scheduling",
        description: "AI-driven algorithms determine optimal engagement times across global timezones.",
        icon: Globe,
        color: "from-blue-500 to-cyan-500"
    },
    {
        title: "Neural Engine",
        description: "Advanced LLM integration for context-aware content generation and replies.",
        icon: Cpu,
        color: "from-purple-500 to-pink-500"
    },
    {
        title: "Stealth Protocol",
        description: "Enterprise-grade browser fingerprinting protection and proxy management.",
        icon: Shield,
        color: "from-green-500 to-emerald-500"
    },
    {
        title: "Vibe Analysis",
        description: "Real-time sentiment tracking and engagement matrix visualization.",
        icon: BarChart3,
        color: "from-orange-500 to-red-500"
    },
    {
        title: "Swarm Intelligence",
        description: "Coordinate multiple agent personas to amplify reach and narrative control.",
        icon: Users,
        color: "from-indigo-500 to-violet-500"
    },
    {
        title: "Instant Execution",
        description: "Zero-latency command dispatch from the central command terminal.",
        icon: Zap,
        color: "from-yellow-400 to-orange-500"
    }
];

export default function FeatureGrid() {
    return (
        <section id="features" className="py-24 bg-black/50 relative">
            <div className="max-w-7xl mx-auto px-6">
                <div className="text-center mb-16">
                    <h2 className="text-4xl md:text-5xl font-orbitron font-bold text-white mb-4">
                        SYSTEM <span className="text-cyan-500">CAPABILITIES</span>
                    </h2>
                    <p className="text-gray-400 font-rajdhani text-xl max-w-2xl mx-auto">
                        Explore the core modules that power the BasaltOnyx autonomous ecosystem.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {features.map((feature, idx) => (
                        <div
                            key={idx}
                            className="group relative p-8 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition-all duration-300 hover:-translate-y-2"
                        >
                            <div className={`w-12 h-12 rounded-lg bg-linear-to-br ${feature.color} flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform`}>
                                <feature.icon className="w-6 h-6 text-white" />
                            </div>

                            <h3 className="text-2xl font-orbitron font-bold text-white mb-4 group-hover:text-cyan-400 transition-colors">
                                {feature.title}
                            </h3>

                            <p className="text-gray-400 font-rajdhani leading-relaxed">
                                {feature.description}
                            </p>

                            <div className="absolute inset-0 rounded-2xl bg-linear-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
