"use client";

import React from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
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
    ArcElement,
    Filler
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    Filler
);

// Theme Colors
const CYAN = 'rgba(6, 182, 212, 1)';
const CYAN_ALPHA = 'rgba(6, 182, 212, 0.1)';
const PURPLE = 'rgba(168, 85, 247, 1)';

const GREEN = 'rgba(34, 197, 94, 1)';
const GRID_COLOR = 'rgba(255, 255, 255, 0.05)';
const TEXT_COLOR = 'rgba(255, 255, 255, 0.7)';
const FONT_FAMILY = 'Orbitron, monospace';

const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                color: TEXT_COLOR,
                font: { family: FONT_FAMILY, size: 10 }
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            titleColor: '#fff',
            bodyColor: '#ccc',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            padding: 10,
            font: { family: FONT_FAMILY }
        }
    },
    scales: {
        x: {
            grid: { color: GRID_COLOR },
            ticks: { color: TEXT_COLOR, font: { family: FONT_FAMILY, size: 10 } }
        },
        y: {
            grid: { color: GRID_COLOR },
            ticks: { color: TEXT_COLOR, font: { family: FONT_FAMILY, size: 10 } }
        }
    }
};



export function GrowthLineChart({ data }: { data: { labels: string[], followers: number[] } }) {
    const chartData = {
        labels: data.labels,
        datasets: [
            {
                label: 'Total Followers',
                data: data.followers,
                borderColor: CYAN,
                backgroundColor: CYAN_ALPHA,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#000',
                pointBorderColor: CYAN,
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }
        ]
    };

    return <Line options={commonOptions} data={chartData} />;
}

export function EngagementBarChart({ data }: { data: { labels: string[], likes: number[], replies: number[] } }) {
    const chartData = {
        labels: data.labels,
        datasets: [
            {
                label: 'Likes',
                data: data.likes,
                backgroundColor: PURPLE,
                borderRadius: 4
            },
            {
                label: 'Replies',
                data: data.replies,
                backgroundColor: GREEN,
                borderRadius: 4
            }
        ]
    };

    return <Bar options={commonOptions} data={chartData} />;
}

export function ActivityPieChart({ data }: { data: { labels: string[], values: number[] } }) {
    const chartData = {
        labels: data.labels,
        datasets: [
            {
                data: data.values,
                backgroundColor: [
                    CYAN,
                    PURPLE,
                    GREEN,
                    'rgba(234, 179, 8, 1)', // Yellow
                    'rgba(239, 68, 68, 1)', // Red
                ],
                borderColor: 'rgba(0,0,0,0.5)',
                borderWidth: 2
            }
        ]
    };

    const options = {
        ...commonOptions,
        scales: { x: { display: false }, y: { display: false } }
    };

    return <Doughnut options={options} data={chartData} />;
}
