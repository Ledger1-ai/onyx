"use client";

import React, { useState, useEffect } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { Filter } from 'lucide-react';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

export default function AnalyticsMatrix({
    platform = 'twitter',
    onPlatformChange
}: {
    platform?: string,
    onPlatformChange?: (platform: string) => void
}) {
    // const [platform, setPlatform] = useState('twitter'); // Moved to parent
    const [loading, setLoading] = useState(true);
    const [chartData, setChartData] = useState<any>(null);
    const [summaryData, setSummaryData] = useState<any>(null);

    useEffect(() => {
        fetchPerformanceData();
    }, [platform]);

    const fetchPerformanceData = async () => {
        setLoading(true);
        try {
            const response = await fetch(`/api/performance?days=7&platform=${platform}`);
            const data = await response.json();

            setChartData(data.chart_data);
            setSummaryData(data.summary);
        } catch (error) {
            console.error("Error fetching analytics:", error);
        } finally {
            setLoading(false);
        }
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
                labels: {
                    color: '#a0aec0',
                    font: { family: 'Rajdhani' }
                }
            },
            title: { display: false },
        },
        scales: {
            x: {
                grid: { color: 'rgba(0, 255, 255, 0.05)' },
                ticks: { color: '#718096' }
            },
            y: {
                grid: { color: 'rgba(0, 255, 255, 0.05)' },
                ticks: { color: '#718096' }
            }
        }
    };

    // Prepare Line Chart Data
    const lineChartData = {
        labels: chartData?.labels || [],
        datasets: [
            {
                label: 'Engagement Rate',
                data: chartData?.datasets?.engagement || [],
                fill: true,
                borderColor: 'rgb(0, 255, 255)',
                backgroundColor: 'rgba(0, 255, 255, 0.1)',
                tension: 0.4,
                yAxisID: 'y'
            },
            {
                label: 'Growth',
                data: chartData?.datasets?.growth || [],
                fill: true,
                borderColor: 'rgb(100, 100, 255)', // Darker blue/purple
                backgroundColor: 'rgba(100, 100, 255, 0.1)',
                tension: 0.4,
                yAxisID: 'y1'
            }
        ],
    };

    // Line Chart Options with Dual Axis
    const lineOptions = {
        ...options,
        scales: {
            ...options.scales,
            y: {
                ...options.scales.y,
                type: 'linear' as const,
                display: true,
                position: 'left' as const,
                title: { display: true, text: 'Engagement %', color: '#00ffff' }
            },
            y1: {
                type: 'linear' as const,
                display: true,
                position: 'right' as const,
                grid: { drawOnChartArea: false },
                ticks: { color: '#6464ff' },
                title: { display: true, text: 'Follower Growth', color: '#6464ff' }
            },
        }
    };

    // Customize labels based on platform
    const getLabels = () => {
        switch (platform) {
            case 'linkedin':
                return ['Reactions', 'Comments', 'Reposts', 'Connections', 'Visits'];
            case 'facebook':
                return ['Reactions', 'Comments', 'Shares', 'Follows', 'Visits'];
            case 'instagram':
                return ['Likes', 'Comments', 'Shares', 'Follows', 'Visits'];
            default: // twitter
                return ['Likes', 'Replies', 'Reposts', 'Follows', 'Visits'];
        }
    };

    // Prepare Bar Chart Data (Activity)
    const barChartData = {
        labels: getLabels(),
        datasets: [
            {
                label: 'Total Actions',
                data: summaryData ? [
                    summaryData.likes || 0, // Maps to first label
                    summaryData.replies || 0, // Maps to second label
                    summaryData.reposts || 0, // Maps to third label
                    summaryData.follows || 0, // Maps to fourth label
                    summaryData.profile_visits || 0
                ] : [0, 0, 0, 0, 0],
                backgroundColor: [
                    'rgba(0, 255, 255, 0.5)',
                    'rgba(255, 0, 255, 0.5)',
                    'rgba(255, 255, 0, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(153, 102, 255, 0.5)',
                ],
                borderColor: [
                    'rgba(0, 255, 255, 1)',
                    'rgba(255, 0, 255, 1)',
                    'rgba(255, 255, 0, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                ],
                borderWidth: 1,
            },
        ],
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-full relative">
            {/* Platform Selector */}
            <div className="absolute top-[-30px] right-0 z-10 flex items-center gap-2">
                <Filter size={14} className="text-cyan-400" />
                <select
                    value={platform}
                    onChange={(e) => onPlatformChange ? onPlatformChange(e.target.value) : null}
                    className="bg-black/40 border border-cyan-500/30 text-cyan-400 text-xs rounded px-2 py-1 outline-none hover:border-cyan-500/60 transition-colors"
                >
                    <option value="twitter">Twitter</option>
                    <option value="linkedin">LinkedIn</option>
                    <option value="facebook">Facebook</option>
                    <option value="instagram">Instagram</option>
                    {/* <option value="combined">Combined</option> Future support */}
                </select>
            </div>

            <div className="glass-chart-container flex flex-col">
                <h3 className="text-xs font-bold text-gray-400 mb-2 font-orbitron">REAL-TIME ENGAGEMENT</h3>
                <div className="flex-1 relative">
                    {loading ? (
                        <div className="flex items-center justify-center h-full text-cyan-500/50">Loading...</div>
                    ) : (
                        <Line options={lineOptions} data={lineChartData} />
                    )}
                </div>
            </div>
            <div className="glass-chart-container flex flex-col">
                <h3 className="text-xs font-bold text-gray-400 mb-2 font-orbitron">ACTIVITY DISTRIBUTION</h3>
                <div className="flex-1 relative">
                    {loading ? (
                        <div className="flex items-center justify-center h-full text-cyan-500/50">Loading...</div>
                    ) : (
                        <Bar options={options} data={barChartData} />
                    )}
                </div>
            </div>
        </div>
    );
}
