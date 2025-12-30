"use client";

import { useState, useEffect, useCallback } from 'react';
import { useSocket } from './useSocket';

interface DashboardStatus {
    active_mode: string;
    daily_progress?: number;
    completed_activities?: number;
    total_activities?: number;
}

interface ScheduleSlot {
    id: string;
    time: string;
    activity: string;
    status: 'pending' | 'completed' | 'failed' | 'in_progress';
}

interface ScheduleData {
    slots: ScheduleSlot[];
    date?: string;
}

interface Strategy {
    name: string;
    description: string;
}

interface StrategyData {
    current_strategy: Strategy;
    activity_distribution: Record<string, number>;
}

interface SystemLog {
    timestamp: string;
    message: string;
    level: 'info' | 'warning' | 'error' | 'success';
}

interface AuthStatus {
    twitter: boolean;
    linkedin: boolean;
}

export const useDashboardData = () => {
    const { socket, isConnected } = useSocket();
    const [status, setStatus] = useState<DashboardStatus | null>(null);
    const [schedule, setSchedule] = useState<ScheduleData | null>(null);
    const [strategy, setStrategy] = useState<StrategyData | null>(null);
    const [logs, setLogs] = useState<SystemLog[]>([]);

    const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);

    // Initial fetch
    const fetchData = useCallback(async () => {
        try {
            const [statusRes, scheduleRes, logsRes, strategyRes, authRes] = await Promise.all([
                fetch('/api/status'),
                fetch('/api/schedule'),
                fetch('/api/logs?limit=50'),
                fetch('/api/optimization'),
                fetch('/api/auth/status')
            ]);

            if (statusRes.ok) setStatus(await statusRes.json());
            if (scheduleRes.ok) setSchedule(await scheduleRes.json());
            if (logsRes.ok) {
                const logsData = await logsRes.json();
                setLogs(logsData.recent_sessions || []);
            }
            if (strategyRes.ok) setStrategy(await strategyRes.json());
            if (authRes.ok) setAuthStatus(await authRes.json());
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        }
    }, []);

    useEffect(() => {
        // Initial load
        fetchData();

        // Polling interval (5 seconds)
        const interval = setInterval(() => {
            fetchData();
        }, 5000);

        return () => clearInterval(interval);
    }, [fetchData]);

    return { status, schedule, logs, strategy, authStatus, isConnected, refresh: fetchData };
};
