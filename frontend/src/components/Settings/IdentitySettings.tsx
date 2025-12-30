"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Save, RefreshCw, Plus, X, Building2, Megaphone, Target, Layers, ArrowLeft } from 'lucide-react';

interface CompanyConfig {
    name: string;
    industry: string;
    mission: string;
    brand_colors: Record<string, string>;
    twitter_username: string;
    company_logo_path: string;
    values: string[];
    focus_areas: string[];
    brand_voice: string;
    target_audience: string;
    key_products: string[];
    competitive_advantages: string[];
    location: string;
    contact_info: Record<string, string>;
    business_model: string;
    core_philosophy: string;
    subsidiaries: string[];
    partner_categories: string[];
}

interface PersonalityConfig {
    tone: string;
    engagement_style: string;
    communication_style: string;
    hashtag_strategy: string;
    content_themes: string[];
    posting_frequency: string;
}

interface SystemIdentity {
    user_id: string;
    company_logo_path: string;
    company_config: CompanyConfig;
    personality_config: PersonalityConfig;
}

const DEFAULT_IDENTITY: SystemIdentity = {
    user_id: 'default_tenant',
    company_logo_path: '',
    company_config: {
        name: '',
        industry: '',
        mission: '',
        brand_colors: { primary: '#000000', secondary: '#ffffff' },
        twitter_username: '',
        company_logo_path: '',
        values: [],
        focus_areas: [],
        brand_voice: '',
        target_audience: '',
        key_products: [],
        competitive_advantages: [],
        location: '',
        contact_info: {},
        business_model: '',
        core_philosophy: '',
        subsidiaries: [],
        partner_categories: []
    },
    personality_config: {
        tone: '',
        engagement_style: '',
        communication_style: '',
        hashtag_strategy: '',
        content_themes: [],
        posting_frequency: ''
    }
};

const PERSONA_PRESETS: Record<string, Partial<PersonalityConfig>> = {
    professional: {
        tone: "Professional, informative, and authoritative",
        engagement_style: "Helpful, clear, and value-driven",
        communication_style: "Formal, precise, and well-structured",
        hashtag_strategy: "Industry-specific, branded hashtags",
        content_themes: ["Industry Insights", "Company Updates", "Thought Leadership"]
    },
    humorous: {
        tone: "Witty, lighthearted, and relatable",
        engagement_style: "Fun, engaging, and meme-friendly",
        communication_style: "Casual, punchy, and humorous",
        hashtag_strategy: "Trending topics, viral hashtags, dry humor",
        content_themes: ["Memes", "Relatable Content", "Behind the Scenes"]
    },
    snarky: {
        tone: "Sarcastic, edgy, and bold",
        engagement_style: "Provocative, challenging, and sharp",
        communication_style: "Direct, witty, and fast-paced",
        hashtag_strategy: "Ironic, bold, cutting-edge",
        content_themes: ["Hot Takes", "Satire", "Controversial Opinions"]
    }
};

export default function IdentitySettings() {
    const router = useRouter();
    const [activeTab, setActiveTab] = useState('identity');
    const [identity, setIdentity] = useState<SystemIdentity>(DEFAULT_IDENTITY);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    // Initial load
    useEffect(() => {
        fetchConfig();
    }, []);

    const fetchConfig = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/config/identity?user_id=default_tenant');
            const data = await res.json();
            if (data.identity) {
                setIdentity(data.identity);
            }
        } catch (error) {
            console.error("Failed to load identity:", error);
            setMessage({ type: 'error', text: 'Failed to load configuration' });
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setMessage(null);
        try {
            const res = await fetch('/api/config/identity', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: 'default_tenant',
                    identity: identity
                })
            });
            const data = await res.json();
            if (data.success) {
                setMessage({ type: 'success', text: 'Configuration saved successfully' });
            } else {
                setMessage({ type: 'error', text: data.error || 'Failed to save' });
            }
        } catch (error) {
            console.error("Failed to save:", error);
            setMessage({ type: 'error', text: 'Network error saving configuration' });
        } finally {
            setSaving(false);
        }
    };

    const updateCompany = <K extends keyof CompanyConfig>(field: K, value: CompanyConfig[K]) => {
        setIdentity(prev => ({
            ...prev,
            company_config: { ...prev.company_config, [field]: value }
        }));
    };

    const updatePersonality = <K extends keyof PersonalityConfig>(field: K, value: PersonalityConfig[K]) => {
        setIdentity(prev => ({
            ...prev,
            personality_config: { ...prev.personality_config, [field]: value }
        }));
    };

    const applyPreset = (presetName: string) => {
        const preset = PERSONA_PRESETS[presetName];
        if (preset) {
            setIdentity(prev => ({
                ...prev,
                personality_config: {
                    ...prev.personality_config,
                    ...preset
                }
            }));
            setMessage({ type: 'success', text: `Applied ${presetName} persona preset` });
        }
    };

    // Helper for array inputs (tags)
    const ArrayInput = ({
        label,
        values,
        onChange
    }: {
        label: string,
        values: string[],
        onChange: (newValues: string[]) => void
    }) => {
        const [input, setInput] = useState('');

        const add = () => {
            if (input.trim() && !values.includes(input.trim())) {
                onChange([...values, input.trim()]);
                setInput('');
            }
        };

        const remove = (idx: number) => {
            onChange(values.filter((_, i) => i !== idx));
        };

        return (
            <div className="mb-4">
                <label className="block text-cyan-400 text-sm font-mono tracking-wider mb-2">{label}</label>
                <div className="flex gap-2 mb-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && add()}
                        className="bg-gray-900 border border-gray-700 text-white px-3 py-2 rounded flex-1 focus:border-cyan-500 focus:outline-none"
                        placeholder="Add new item..."
                    />
                    <button onClick={add} type="button" className="bg-cyan-900/40 border border-cyan-500/50 text-cyan-300 px-3 rounded hover:bg-cyan-800/50">
                        <Plus className="w-4 h-4" />
                    </button>
                </div>
                <div className="flex flex-wrap gap-2">
                    {values.map((v, i) => (
                        <span key={i} className="bg-gray-800 border border-gray-600 text-gray-300 px-2 py-1 rounded text-xs flex items-center">
                            {v}
                            <button onClick={() => remove(i)} className="ml-2 hover:text-red-400"><X className="w-3 h-3" /></button>
                        </span>
                    ))}
                </div>
            </div>
        );
    };

    if (loading) return <div className="text-cyan-500 animate-pulse font-mono p-8">INITIALIZING SYSTEM IDENTITY PROTOCOLS...</div>;

    return (
        <div className="glass-panel p-6 border border-cyan-500/20 bg-black/60 backdrop-blur-md min-h-[80vh]">
            {/* Header / Tabs */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 border-b border-gray-800 pb-4 gap-4">
                <div className="flex items-center gap-4 w-full md:w-auto overflow-x-auto">
                    <button
                        onClick={() => router.push('/underworld/dashboard')}
                        className="p-2 rounded text-gray-400 hover:text-cyan-400 hover:bg-gray-800 transition-colors"
                        title="Back to Dashboard"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div className="h-6 w-px bg-gray-700 mx-2" />
                    {[
                        { id: 'identity', label: 'IDENTITY', icon: Building2 },
                        { id: 'brand', label: 'BRAND PILLARS', icon: Target },
                        { id: 'personality', label: 'PERSONA', icon: Megaphone },
                        { id: 'structure', label: 'ECOSYSTEM', icon: Layers },
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center space-x-2 px-4 py-2 rounded transition-all duration-300 font-orbitron text-sm tracking-wider whitespace-nowrap
                                ${activeTab === tab.id
                                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                                    : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/50 border border-transparent'}`}
                        >
                            <tab.icon className="w-4 h-4" />
                            <span>{tab.label}</span>
                        </button>
                    ))}
                </div>

                <div className="flex items-center gap-3">
                    {message && (
                        <span className={`text-sm font-mono px-3 py-1 rounded border ${message.type === 'success' ? 'bg-green-900/20 border-green-500/30 text-green-400' : 'bg-red-900/20 border-red-500/30 text-red-400'}`}>
                            {message.text}
                        </span>
                    )}
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="glass-button glass-button-primary flex items-center px-6 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-black font-bold transition-all disabled:opacity-50"
                    >
                        {saving ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                        SAVE CONFIG
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 animate-in fade-in duration-500">

                {/* ---------- ID: IDENTITY ---------- */}
                {activeTab === 'identity' && (
                    <>
                        <div className="space-y-4">
                            <h3 className="text-cyan-400 font-bold border-b border-gray-800 pb-2 mb-4">Core Information</h3>

                            <div>
                                <label className="label-text">Company Name</label>
                                <input
                                    type="text"
                                    value={identity.company_config.name}
                                    onChange={(e) => updateCompany('name', e.target.value)}
                                    className="input-field w-full bg-gray-900/50 border border-gray-700 p-2 text-white"
                                />
                            </div>

                            <div>
                                <label className="label-text">Industry</label>
                                <input
                                    type="text"
                                    value={identity.company_config.industry}
                                    onChange={(e) => updateCompany('industry', e.target.value)}
                                    className="input-field w-full bg-gray-900/50 border border-gray-700 p-2 text-white"
                                />
                            </div>

                            <div>
                                <label className="label-text">Location</label>
                                <input
                                    type="text"
                                    value={identity.company_config.location}
                                    onChange={(e) => updateCompany('location', e.target.value)}
                                    className="input-field w-full bg-gray-900/50 border border-gray-700 p-2 text-white"
                                />
                            </div>

                            <div>
                                <label className="label-text">Twitter Handle</label>
                                <input
                                    type="text"
                                    value={identity.company_config.twitter_username}
                                    onChange={(e) => updateCompany('twitter_username', e.target.value)}
                                    className="input-field w-full bg-gray-900/50 border border-gray-700 p-2 text-white"
                                />
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-cyan-400 font-bold border-b border-gray-800 pb-2 mb-4">Strategic Vision</h3>

                            <div>
                                <label className="label-text">Mission Statement</label>
                                <textarea
                                    value={identity.company_config.mission}
                                    onChange={(e) => updateCompany('mission', e.target.value)}
                                    className="input-field w-full h-32 bg-gray-900/50 border border-gray-700 p-2 text-white resize-none"
                                />
                            </div>

                            <div>
                                <label className="label-text">Core Philosophy</label>
                                <textarea
                                    value={identity.company_config.core_philosophy}
                                    onChange={(e) => updateCompany('core_philosophy', e.target.value)}
                                    className="input-field w-full h-32 bg-gray-900/50 border border-gray-700 p-2 text-white resize-none"
                                />
                            </div>
                        </div>
                    </>
                )}


                {/* ---------- ID: BRAND ---------- */}
                {activeTab === 'brand' && (
                    <>
                        <div className="space-y-4">
                            <h3 className="text-cyan-400 font-bold border-b border-gray-800 pb-2 mb-4">Strategic Pillars</h3>
                            <ArrayInput
                                label="Core Values"
                                values={identity.company_config.values}
                                onChange={(vals) => updateCompany('values', vals)}
                            />
                            <ArrayInput
                                label="Strategic Focus Areas"
                                values={identity.company_config.focus_areas}
                                onChange={(vals) => updateCompany('focus_areas', vals)}
                            />
                            <ArrayInput
                                label="Competitive Advantages"
                                values={identity.company_config.competitive_advantages}
                                onChange={(vals) => updateCompany('competitive_advantages', vals)}
                            />
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-cyan-400 font-bold border-b border-gray-800 pb-2 mb-4">Target Audience</h3>
                            <div>
                                <label className="label-text">Audience Description</label>
                                <textarea
                                    value={identity.company_config.target_audience}
                                    onChange={(e) => updateCompany('target_audience', e.target.value)}
                                    className="input-field w-full h-32 bg-gray-900/50 border border-gray-700 p-2 text-white resize-none"
                                />
                            </div>
                            <div>
                                <label className="label-text">Business Model Summary</label>
                                <textarea
                                    value={identity.company_config.business_model}
                                    onChange={(e) => updateCompany('business_model', e.target.value)}
                                    className="input-field w-full h-32 bg-gray-900/50 border border-gray-700 p-2 text-white resize-none"
                                />
                            </div>
                        </div>
                    </>
                )}


                {/* ---------- ID: PERSONA ---------- */}
                {activeTab === 'personality' && (
                    <>
                        <div className="space-y-4">
                            <h3 className="text-cyan-400 font-bold border-b border-gray-800 pb-2 mb-4">Voice & Tone</h3>

                            <div className="mb-6 bg-cyan-900/10 border border-cyan-500/20 p-4 rounded-lg">
                                <label className="label-text mb-2 block text-cyan-300">Choose a Persona Preset</label>
                                <div className="flex gap-2">
                                    {Object.keys(PERSONA_PRESETS).map((preset) => (
                                        <button
                                            key={preset}
                                            onClick={() => applyPreset(preset)}
                                            className="px-3 py-1 bg-gray-800 hover:bg-cyan-700 hover:text-white text-gray-300 rounded text-sm transition-colors border border-gray-700 uppercase tracking-wider"
                                        >
                                            {preset}
                                        </button>
                                    ))}
                                </div>
                                <p className="text-xs text-gray-500 mt-2">Selecting a preset will overwrite the fields below.</p>
                            </div>

                            <div>
                                <label className="label-text">Brand Voice (Company)</label>
                                <input
                                    type="text"
                                    value={identity.company_config.brand_voice}
                                    onChange={(e) => updateCompany('brand_voice', e.target.value)}
                                    className="input-field w-full bg-gray-900/50 border border-gray-700 p-2 text-white"
                                />
                            </div>
                            <div>
                                <label className="label-text">Agent Tone</label>
                                <input
                                    type="text"
                                    value={identity.personality_config.tone}
                                    onChange={(e) => updatePersonality('tone', e.target.value)}
                                    className="input-field w-full bg-gray-900/50 border border-gray-700 p-2 text-white"
                                />
                            </div>
                            <div>
                                <label className="label-text">Communication Style</label>
                                <input
                                    type="text"
                                    value={identity.personality_config.communication_style}
                                    onChange={(e) => updatePersonality('communication_style', e.target.value)}
                                    className="input-field w-full bg-gray-900/50 border border-gray-700 p-2 text-white"
                                />
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-cyan-400 font-bold border-b border-gray-800 pb-2 mb-4">Content Strategy</h3>
                            <div>
                                <label className="label-text">Engagement Style</label>
                                <textarea
                                    value={identity.personality_config.engagement_style}
                                    onChange={(e) => updatePersonality('engagement_style', e.target.value)}
                                    className="input-field w-full h-24 bg-gray-900/50 border border-gray-700 p-2 text-white resize-none"
                                />
                            </div>
                            <div>
                                <label className="label-text">Hashtag Strategy</label>
                                <textarea
                                    value={identity.personality_config.hashtag_strategy}
                                    onChange={(e) => updatePersonality('hashtag_strategy', e.target.value)}
                                    className="input-field w-full h-24 bg-gray-900/50 border border-gray-700 p-2 text-white resize-none"
                                />
                            </div>
                            <ArrayInput
                                label="Content Themes"
                                values={identity.personality_config.content_themes}
                                onChange={(vals) => updatePersonality('content_themes', vals)}
                            />
                        </div>
                    </>
                )}


                {/* ---------- ID: STRUCTURE ---------- */}
                {activeTab === 'structure' && (
                    <>
                        <div className="space-y-4">
                            <h3 className="text-cyan-400 font-bold border-b border-gray-800 pb-2 mb-4">Products & Services</h3>
                            <ArrayInput
                                label="Key Products"
                                values={identity.company_config.key_products}
                                onChange={(vals) => updateCompany('key_products', vals)}
                            />
                            <ArrayInput
                                label="Subsidiaries"
                                values={identity.company_config.subsidiaries}
                                onChange={(vals) => updateCompany('subsidiaries', vals)}
                            />
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-cyan-400 font-bold border-b border-gray-800 pb-2 mb-4">Partnership Network</h3>
                            <ArrayInput
                                label="Partner Categories"
                                values={identity.company_config.partner_categories}
                                onChange={(vals) => updateCompany('partner_categories', vals)}
                            />
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
