"use client";

import React, { useState, useEffect } from 'react';
import { User, Plus, Trash2, Users, Briefcase, Shield, CheckSquare, Square } from 'lucide-react';

interface UserData {
    _id: string;
    email: string;
    name: string;
    role: string; // Now refers to Role ID
    teamId?: string;
}

interface TeamData {
    _id: string;
    name: string;
    description: string;
}

interface RoleData {
    _id: string;
    name: string;
    description: string;
    permissions: string[];
    isSystem: boolean;
}

export default function UserManagement() {
    const [viewMode, setViewMode] = useState<'users' | 'teams' | 'roles'>('users');
    const [users, setUsers] = useState<UserData[]>([]);
    const [teams, setTeams] = useState<TeamData[]>([]);
    const [roles, setRoles] = useState<RoleData[]>([]);
    const [availablePermissions, setAvailablePermissions] = useState<Record<string, string>>({});
    const [loading, setLoading] = useState(true);

    // Modals
    const [showUserModal, setShowUserModal] = useState(false);
    const [showTeamModal, setShowTeamModal] = useState(false);
    const [showRoleModal, setShowRoleModal] = useState(false);

    const [editingUser, setEditingUser] = useState<UserData | null>(null);
    const [editingRole, setEditingRole] = useState<RoleData | null>(null);

    // Create User Form State
    const [newName, setNewName] = useState('');
    const [newEmail, setNewEmail] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [newRole, setNewRole] = useState('');
    const [selectedTeam, setSelectedTeam] = useState('');

    // Create Team Form State
    const [newTeamName, setNewTeamName] = useState('');
    const [newTeamDesc, setNewTeamDesc] = useState('');

    // Edit User Form State
    const [editName, setEditName] = useState('');
    const [editEmail, setEditEmail] = useState('');
    const [editPassword, setEditPassword] = useState('');
    const [editRole, setEditRole] = useState('');
    const [editTeam, setEditTeam] = useState('');

    // Role Form State
    const [roleName, setRoleName] = useState('');
    const [roleDesc, setRoleDesc] = useState('');
    const [rolePerms, setRolePerms] = useState<string[]>([]);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [uRes, tRes, rRes] = await Promise.all([
                fetch('/api/users'),
                fetch('/api/teams'),
                fetch('/api/roles')
            ]);
            const uData = await uRes.json();
            const tData = await tRes.json();
            const rData = await rRes.json();

            if (uData.success) setUsers(uData.users);
            if (tData.success) setTeams(tData.teams);
            if (rData.success) {
                setRoles(rData.roles);
                setAvailablePermissions(rData.permissions);
                // Set default newRole if available
                if (rData.roles.length > 0 && !newRole) {
                    const defaultRole = rData.roles.find((r: any) => r.name === 'User') || rData.roles[0];
                    setNewRole(defaultRole._id);
                }
            }
        } catch (error) {
            console.error('Failed to fetch data', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await fetch('/api/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newName,
                    email: newEmail,
                    password: newPassword,
                    role: newRole,
                    teamId: selectedTeam || null
                })
            });
            const data = await res.json();
            if (data.success) {
                setShowUserModal(false);
                setNewName(''); setNewEmail(''); setNewPassword(''); setSelectedTeam('');
                fetchData();
            } else {
                alert(data.error);
            }
        } catch (error) {
            alert('Failed to create user');
        }
    };

    const handleUpdateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingUser) return;

        try {
            const res = await fetch('/api/users', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: editingUser._id,
                    name: editName,
                    email: editEmail,
                    password: editPassword || undefined,
                    role: editRole,
                    teamId: editTeam || null
                })
            });
            const data = await res.json();
            if (data.success) {
                setEditingUser(null);
                setEditName(''); setEditEmail(''); setEditPassword('');
                fetchData();
            } else {
                alert(data.error);
            }
        } catch (error) {
            alert('Failed to update user');
        }
    };

    const handleDeleteUser = async (id: string) => {
        if (!confirm('Are you sure you want to delete this user? This cannot be undone.')) return;
        try {
            const res = await fetch(`/api/users?id=${id}`, {
                method: 'DELETE'
            });
            const data = await res.json();
            if (data.success) {
                fetchData();
            } else {
                alert(data.error);
            }
        } catch (error) {
            alert('Failed to delete user');
        }
    };

    const handleCreateTeam = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await fetch('/api/teams', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newTeamName,
                    description: newTeamDesc
                })
            });
            const data = await res.json();
            if (data.success) {
                setShowTeamModal(false);
                setNewTeamName(''); setNewTeamDesc('');
                fetchData();
            } else {
                alert(data.error);
            }
        } catch (error) {
            alert('Failed to create team');
        }
    };

    const handleSaveRole = async (e: React.FormEvent) => {
        e.preventDefault();
        const isEdit = !!editingRole;
        const method = isEdit ? 'PUT' : 'POST';
        const body: any = {
            name: roleName,
            description: roleDesc,
            permissions: rolePerms
        };
        if (isEdit && editingRole) body.id = editingRole._id;

        try {
            const res = await fetch('/api/roles', {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await res.json();
            if (data.success) {
                setShowRoleModal(false);
                setEditingRole(null);
                setRoleName(''); setRoleDesc(''); setRolePerms([]);
                fetchData();
            } else {
                alert(data.error);
            }
        } catch (error) {
            alert('Failed to save role');
        }
    };

    const handleDeleteRole = async (id: string) => {
        if (!confirm('Are you sure? Users assigned this role may lose access.')) return;
        try {
            const res = await fetch(`/api/roles?id=${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) fetchData();
            else alert(data.error);
        } catch (error) {
            alert('Failed');
        }
    };

    const togglePermission = (perm: string) => {
        setRolePerms(prev =>
            prev.includes(perm) ? prev.filter(p => p !== perm) : [...prev, perm]
        );
    };

    const openEditModal = (user: UserData) => {
        setEditingUser(user);
        setEditName(user.name);
        setEditEmail(user.email);
        setEditRole(user.role); // Role ID
        setEditTeam(user.teamId || '');
        setEditPassword('');
    };

    const openRoleModal = (role?: RoleData) => {
        if (role) {
            setEditingRole(role);
            setRoleName(role.name);
            setRoleDesc(role.description);
            setRolePerms(role.permissions);
        } else {
            setEditingRole(null);
            setRoleName('');
            setRoleDesc('');
            setRolePerms([]);
        }
        setShowRoleModal(true);
    };

    const getTeamName = (id?: string) => {
        if (!id) return 'Unassigned';
        return teams.find(t => t._id === id)?.name || 'Unknown';
    };

    const getRoleName = (id: string) => {
        const role = roles.find(r => r._id === id);
        // Fallback for legacy string roles if migration didn't happen yet (though we should assume new system)
        if (!role) {
            if (id === 'admin') return 'Legacy Admin';
            if (id === 'user') return 'Legacy User';
            if (id === 'super_admin') return 'Legacy Super';
            return 'Unknown Role';
        }
        return role.name;
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header Controls */}
            <div className="flex justify-between items-center">
                <div className="flex bg-gray-900/50 p-1 rounded-lg border border-gray-800">
                    <button
                        onClick={() => setViewMode('users')}
                        className={`px-4 py-1.5 rounded text-sm font-bold font-mono transition-all ${viewMode === 'users' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'text-gray-500 hover:text-white'}`}
                    >
                        USERS
                    </button>
                    <button
                        onClick={() => setViewMode('teams')}
                        className={`px-4 py-1.5 rounded text-sm font-bold font-mono transition-all ${viewMode === 'teams' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'text-gray-500 hover:text-white'}`}
                    >
                        TEAMS
                    </button>
                    <button
                        onClick={() => setViewMode('roles')}
                        className={`px-4 py-1.5 rounded text-sm font-bold font-mono transition-all ${viewMode === 'roles' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'text-gray-500 hover:text-white'}`}
                    >
                        ROLES & PERMISSIONS
                    </button>
                </div>

                <button
                    onClick={() => {
                        if (viewMode === 'users') setShowUserModal(true);
                        else if (viewMode === 'teams') setShowTeamModal(true);
                        else openRoleModal();
                    }}
                    className="flex items-center px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md font-bold transition-colors shadow-[0_0_15px_rgba(6,182,212,0.3)] text-sm"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    CREATE {viewMode === 'users' ? 'USER' : viewMode === 'teams' ? 'TEAM' : 'ROLE'}
                </button>
            </div>

            {/* Content Views */}
            <div className="space-y-3">
                {loading ? (
                    <div className="text-center py-10 text-gray-500 animate-pulse">Loading data...</div>
                ) : viewMode === 'users' ? (
                    users.length === 0 ? <div className="text-center py-10 text-gray-500">No users found.</div> :
                        users.map(user => (
                            <div key={user._id} className="glass-card p-4 rounded-lg border border-gray-800 flex justify-between items-center hover:border-gray-700 transition-all bg-gray-900/40 group">
                                <div className="flex items-center space-x-4 cursor-pointer" onClick={() => openEditModal(user)}>
                                    <div className="w-10 h-10 rounded-full bg-linear-to-br from-gray-700 to-gray-800 flex items-center justify-center text-white font-bold border border-gray-600">
                                        {user.name.charAt(0).toUpperCase()}
                                    </div>
                                    <div>
                                        <h4 className="text-white font-bold text-sm group-hover:text-cyan-400 transition-colors">{user.name}</h4>
                                        <div className="flex items-center space-x-3 text-xs text-gray-400 font-mono">
                                            <span>{user.email}</span>
                                            <span className="px-1.5 py-0.5 rounded border border-purple-500/30 text-purple-400">
                                                {getRoleName(user.role).toUpperCase()}
                                            </span>
                                            <span className="flex items-center text-cyan-600">
                                                <Briefcase className="w-3 h-3 mr-1" />
                                                {getTeamName(user.teamId)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button onClick={() => openEditModal(user)} className="p-2 hover:bg-white/10 text-gray-400 hover:text-cyan-400 rounded transition-colors">Edit</button>
                                    <button onClick={() => handleDeleteUser(user._id)} className="p-2 hover:bg-red-500/20 text-gray-600 hover:text-red-400 rounded transition-colors"><Trash2 className="w-4 h-4" /></button>
                                </div>
                            </div>
                        ))
                ) : viewMode === 'teams' ? (
                    teams.length === 0 ? <div className="text-center py-10 text-gray-500">No teams found.</div> :
                        teams.map(team => (
                            <div key={team._id} className="glass-card p-4 rounded-lg border border-gray-800 flex justify-between items-center hover:border-gray-700 transition-all bg-gray-900/40">
                                <div className="flex items-center space-x-4">
                                    <div className="p-2 rounded bg-cyan-900/20 border border-cyan-500/20 text-cyan-400"><Users className="w-5 h-5" /></div>
                                    <div>
                                        <h4 className="text-white font-bold text-sm">{team.name}</h4>
                                        <p className="text-xs text-gray-400">{team.description || 'No description'}</p>
                                    </div>
                                </div>
                                <div className="text-xs font-mono text-gray-500">{users.filter(u => u.teamId === team._id).length} Members</div>
                            </div>
                        ))
                ) : (
                    // ROLES VIEW
                    roles.length === 0 ? <div className="text-center py-10 text-gray-500">No roles found.</div> :
                        roles.map(role => (
                            <div key={role._id} className="glass-card p-4 rounded-lg border border-gray-800 flex justify-between items-center hover:border-gray-700 transition-all bg-gray-900/40 group">
                                <div className="flex items-center space-x-4 cursor-pointer" onClick={() => openRoleModal(role)}>
                                    <div className="p-2 rounded bg-purple-900/20 border border-purple-500/20 text-purple-400"><Shield className="w-5 h-5" /></div>
                                    <div>
                                        <h4 className="text-white font-bold text-sm group-hover:text-cyan-400 transition-colors">{role.name}</h4>
                                        <p className="text-xs text-gray-400">{role.description || 'No description'}</p>
                                        <div className="mt-1 flex flex-wrap gap-1">
                                            {role.permissions.slice(0, 5).map(p => (
                                                <span key={p} className="text-[10px] px-1 bg-gray-800 rounded text-gray-400">{p}</span>
                                            ))}
                                            {role.permissions.length > 5 && <span className="text-[10px] px-1 text-gray-500">+{role.permissions.length - 5} more</span>}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button onClick={() => openRoleModal(role)} className="p-2 hover:bg-white/10 text-gray-400 hover:text-cyan-400 rounded transition-colors">Edit</button>
                                    {!role.isSystem && (
                                        <button onClick={() => handleDeleteRole(role._id)} className="p-2 hover:bg-red-500/20 text-gray-600 hover:text-red-400 rounded transition-colors"><Trash2 className="w-4 h-4" /></button>
                                    )}
                                </div>
                            </div>
                        ))
                )}
            </div>

            {/* Create/Edit User Modals (Simplified for brevity, similar to before but with Dynamic Role Select) */}
            {(showUserModal || editingUser) && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-gray-900 w-full max-w-md p-6 rounded-xl border border-gray-700 shadow-2xl relative animate-in zoom-in-95 duration-200">
                        <h3 className="text-lg font-bold text-white mb-6">{editingUser ? 'Edit User' : 'Create User'}</h3>
                        <form onSubmit={editingUser ? handleUpdateUser : handleCreateUser} className="space-y-4">
                            {/* ... Name/Email/Pass fields same as before ... */}
                            <div>
                                <label className="block text-xs font-bold text-gray-400 mb-1 ml-1">FULL NAME</label>
                                <input type="text" required value={editingUser ? editName : newName} onChange={e => editingUser ? setEditName(e.target.value) : setNewName(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:border-cyan-500 focus:outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-gray-400 mb-1 ml-1">EMAIL ADDRESS</label>
                                <input type="email" required value={editingUser ? editEmail : newEmail} onChange={e => editingUser ? setEditEmail(e.target.value) : setNewEmail(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:border-cyan-500 focus:outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-gray-400 mb-1 ml-1">PASSWORD {editingUser && '(Optional)'}</label>
                                <input type="password" required={!editingUser} value={editingUser ? editPassword : newPassword} onChange={e => editingUser ? setEditPassword(e.target.value) : setNewPassword(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:border-cyan-500 focus:outline-none" />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-bold text-gray-400 mb-1 ml-1">ROLE</label>
                                    <select
                                        value={editingUser ? editRole : newRole}
                                        onChange={e => editingUser ? setEditRole(e.target.value) : setNewRole(e.target.value)}
                                        className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:border-cyan-500 focus:outline-none appearance-none"
                                    >
                                        <option value="">Select Role</option>
                                        {roles.map(r => <option key={r._id} value={r._id}>{r.name}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-gray-400 mb-1 ml-1">TEAM</label>
                                    <select
                                        value={editingUser ? editTeam : selectedTeam}
                                        onChange={e => editingUser ? setEditTeam(e.target.value) : setSelectedTeam(e.target.value)}
                                        className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:border-cyan-500 focus:outline-none appearance-none"
                                    >
                                        <option value="">Unassigned</option>
                                        {teams.map(t => <option key={t._id} value={t._id}>{t.name}</option>)}
                                    </select>
                                </div>
                            </div>

                            <div className="flex space-x-3 mt-8 pt-4 border-t border-gray-800">
                                <button type="button" onClick={() => { setShowUserModal(false); setEditingUser(null); }} className="flex-1 py-2.5 bg-gray-800 hover:bg-gray-700 text-white rounded-lg font-bold">Cancel</button>
                                <button type="submit" className="flex-1 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-bold">{editingUser ? 'Save' : 'Create'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Role Modal */}
            {showRoleModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-gray-900 w-full max-w-2xl p-6 rounded-xl border border-gray-700 shadow-2xl relative animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto">
                        <h3 className="text-lg font-bold text-white mb-6">{editingRole ? 'Edit Role' : 'Create Role'}</h3>
                        <form onSubmit={handleSaveRole} className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-gray-400 mb-1 ml-1">ROLE NAME</label>
                                <input type="text" required value={roleName} onChange={e => setRoleName(e.target.value)} disabled={editingRole?.isSystem} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:border-cyan-500 focus:outline-none disabled:opacity-50" />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-gray-400 mb-1 ml-1">DESCRIPTION</label>
                                <textarea value={roleDesc} onChange={e => setRoleDesc(e.target.value)} rows={2} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:border-cyan-500 focus:outline-none" />
                            </div>

                            <div className="mt-6">
                                <label className="block text-xs font-bold text-cyan-400 mb-3 ml-1 uppercase tracking-wider">System Permissions</label>
                                <div className="grid grid-cols-2 gap-3 p-4 bg-black/40 rounded-xl border border-gray-800/50">
                                    {Object.entries(availablePermissions).map(([key, value]) => (
                                        <div key={value} onClick={() => togglePermission(value)} className={`flex items-center p-3 rounded cursor-pointer border transition-all ${rolePerms.includes(value) ? 'bg-cyan-500/10 border-cyan-500/50 text-white' : 'bg-transparent border-transparent hover:bg-gray-800 text-gray-400'}`}>
                                            {rolePerms.includes(value) ? <CheckSquare className="w-4 h-4 mr-3 text-cyan-400" /> : <Square className="w-4 h-4 mr-3 text-gray-600" />}
                                            <span className="text-sm font-mono">{value}</span>
                                            {value.includes('access_all') && <span className="ml-2 px-1.5 py-0.5 bg-red-500/20 text-red-400 text-[10px] rounded border border-red-500/30">GLOBAL</span>}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="flex space-x-3 mt-8 pt-4 border-t border-gray-800">
                                <button type="button" onClick={() => setShowRoleModal(false)} className="flex-1 py-2.5 bg-gray-800 hover:bg-gray-700 text-white rounded-lg font-bold">Cancel</button>
                                <button type="submit" className="flex-1 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-bold">Save Role</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Team Modal (Simplified) */}
            {showTeamModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-gray-900 w-full max-w-md p-6 rounded-xl border border-gray-700 shadow-2xl relative">
                        <h3 className="text-lg font-bold text-white mb-6">Create New Team</h3>
                        <form onSubmit={handleCreateTeam} className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-gray-400 mb-1 ml-1">TEAM NAME</label>
                                <input type="text" required value={newTeamName} onChange={e => setNewTeamName(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white focus:border-cyan-500 focus:outline-none" />
                            </div>
                            <div className="flex space-x-3 mt-8 pt-4 border-t border-gray-800">
                                <button type="button" onClick={() => setShowTeamModal(false)} className="flex-1 py-2.5 bg-gray-800 hover:bg-gray-700 text-white rounded-lg font-bold">Cancel</button>
                                <button type="submit" className="flex-1 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-bold">Create</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
