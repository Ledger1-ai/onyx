"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { User, Lock, Mail, Shield, Users, Save, AlertCircle, ArrowLeft } from 'lucide-react';

export default function ProfilePage() {
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const res = await fetch('/api/auth/me');
                if (res.ok) {
                    const data = await res.json();
                    setUser(data.user);
                }
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchUser();
    }, []);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setSaving(true);

        if (password && password !== confirmPassword) {
            setError("Passwords do not match");
            setSaving(false);
            return;
        }

        try {
            const payload: any = {
                id: user.id,
                name: user.name, // Allow name edit
            };
            if (password) payload.password = password;

            const res = await fetch('/api/users', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (data.success) {
                setSuccess('Profile updated successfully');
                setPassword('');
                setConfirmPassword('');
                setUser({ ...user, name: data.user.name }); // Update local state
            } else {
                setError(data.error || 'Failed to update profile');
            }
        } catch (err) {
            setError('An error occurred');
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="p-8 text-cyan-400 font-orbitron animate-pulse">Loading Identity...</div>;
    if (!user) return <div className="p-8 text-red-400 font-orbitron">Identity Not Found.</div>;

    return (
        <div className="p-8 max-w-4xl mx-auto space-y-8 pb-24">
            <div>
                <Link href="/underworld/dashboard" className="inline-flex items-center text-cyan-400/60 hover:text-cyan-400 transition-colors mb-4 font-orbitron text-sm">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Dashboard
                </Link>
                <h1 className="text-3xl font-bold text-white font-orbitron tracking-widest text-shadow-glow">
                    OPERATIVE PROFILE
                </h1>
            </div>

            <div className="glass-panel p-8 border border-white/10 rounded-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                    <User className="w-64 h-64 text-cyan-400" />
                </div>

                <form onSubmit={handleSave} className="relative z-10 space-y-6 max-w-lg">
                    {/* Read Only Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-xs text-cyan-400/70 uppercase tracking-wider font-bold">Role Clearance</label>
                            <div className="flex items-center space-x-2 text-gray-300 bg-black/40 p-3 rounded-lg border border-white/5">
                                <Shield className="w-4 h-4 text-purple-400" />
                                <span>{user.role}</span>
                            </div>
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs text-cyan-400/70 uppercase tracking-wider font-bold">Team Affiliation</label>
                            <div className="flex items-center space-x-2 text-gray-300 bg-black/40 p-3 rounded-lg border border-white/5">
                                <Users className="w-4 h-4 text-blue-400" />
                                <span>{user.teamId ? 'Assigned Operative' : 'Freelancer / Global'}</span>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs text-cyan-400/70 uppercase tracking-wider font-bold">Email Identity</label>
                        <div className="flex items-center space-x-2 text-gray-400 bg-black/40 p-3 rounded-lg border border-white/5 cursor-not-allowed">
                            <Mail className="w-4 h-4" />
                            <span>{user.email}</span>
                        </div>
                        <p className="text-[10px] text-gray-600 pl-1">Identity cannot be changed here.</p>
                    </div>

                    {/* Editable Fields */}
                    <div className="space-y-1 pt-4 border-t border-white/5">
                        <label className="text-xs text-cyan-400 uppercase tracking-wider font-bold">Operative Name</label>
                        <div className="relative group">
                            <input
                                type="text"
                                value={user.name}
                                onChange={(e) => setUser({ ...user, name: e.target.value })}
                                className="w-full bg-black/60 border border-white/10 rounded-lg py-3 pl-10 pr-4 text-white focus:outline-none focus:border-cyan-500/50 focus:shadow-[0_0_15px_rgba(6,182,212,0.2)] transition-all font-rajdhani text-lg"
                                placeholder="Enter Name"
                            />
                            <User className="w-5 h-5 text-gray-500 absolute left-3 top-3.5 group-focus-within:text-cyan-400 transition-colors" />
                        </div>
                    </div>

                    <div className="space-y-4 pt-4 border-t border-white/5">
                        <h3 className="text-sm font-bold text-white font-orbitron flex items-center">
                            <Lock className="w-4 h-4 mr-2 text-cyan-400" />
                            Update Credentials
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-xs text-gray-500 uppercase tracking-wider">New Password</label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-black/60 border border-white/10 rounded-lg py-2 px-4 text-white focus:outline-none focus:border-cyan-500/50 transition-all"
                                    placeholder="••••••••"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs text-gray-500 uppercase tracking-wider">Confirm Password</label>
                                <input
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full bg-black/60 border border-white/10 rounded-lg py-2 px-4 text-white focus:outline-none focus:border-cyan-500/50 transition-all"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>
                    </div>

                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center text-red-400 text-sm">
                            <AlertCircle className="w-4 h-4 mr-2" />
                            {error}
                        </div>
                    )}

                    {success && (
                        <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center text-green-400 text-sm animate-pulse">
                            <Shield className="w-4 h-4 mr-2" />
                            {success}
                        </div>
                    )}

                    <div className="pt-4 flex justify-end items-center space-x-4">
                        <Link
                            href="/underworld/dashboard"
                            className="px-4 py-3 text-sm font-bold font-orbitron text-gray-500 hover:text-white transition-colors"
                        >
                            Cancel
                        </Link>
                        <button
                            type="submit"
                            disabled={saving}
                            className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-bold font-orbitron tracking-wide transition-all ${saving
                                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                    : 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:scale-105'
                                }`}
                        >
                            <Save className="w-5 h-5" />
                            <span>{saving ? 'Updating...' : 'Save Changes'}</span>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
