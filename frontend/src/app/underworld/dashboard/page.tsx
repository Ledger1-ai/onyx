"use client";

import React from 'react';

import MissionSchedule from '@/components/Dashboard/MissionSchedule';
import CommandCenter from '@/components/Dashboard/CommandCenter';
import PlatformStatus from '@/components/Dashboard/PlatformStatus';
import StatusOverview from '@/components/Dashboard/StatusOverview';
import TaskFrequencyControls from '@/components/Dashboard/TaskFrequencyControls';
import AutoProtocols from '@/components/Dashboard/AutoProtocols';

import { useDashboardData } from '@/hooks/useDashboardData';

export default function Dashboard() {
  const { status, schedule, strategy, authStatus, refresh } = useDashboardData();

  const handleSaveFrequency = async (distribution: Record<string, number>, platform: string) => {
    try {
      const res = await fetch('/api/tasks/update-frequencies', {
        method: 'POST',
        body: JSON.stringify({ distribution, platform }),
        headers: { 'Content-Type': 'application/json' }
      });
      if (res.ok) {
        refresh(); // Refresh dashboard data
      } else {
        console.error('Failed to save distribution');
      }
    } catch (err) {
      console.error('Error saving distribution:', err);
    }
  };

  return (
    <div className="min-h-screen pb-10">
      {/* Header is handled by layout now, but keeping if layout doesn't cover all cases or specific page structure needs it. 
          The plan said layout.tsx adds Header, so we might duplicate it. 
          However, usually if layout adds it, we remove it here. 
          I will COMMENT OUT Header here since UnderworldLayout has it. */}
      {/* <Header /> */}

      <main className="w-full px-6 py-4">
        {/* Top Row: Command Center (HUD) */}
        <div className="mb-6">
          <CommandCenter onRefresh={refresh} />
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">

          {/* Left Column: Mission Schedule */}
          <div className="xl:col-span-3">
            <MissionSchedule
              schedule={schedule}
              afterlifeEnabled={status?.active_mode === 'afterlife'}
              authStatus={authStatus}
            />
          </div>

          {/* Center Column: Command & Analytics */}
          <div className="xl:col-span-6 space-y-6">

            <PlatformStatus activeMode={status?.active_mode || 'standard'} />
            <AutoProtocols />
            <StatusOverview data={status ? { ...status, daily_progress: status.daily_progress ?? 0, completed_activities: status.completed_activities ?? 0, total_activities: status.total_activities ?? 0 } : null} />

            {/* Analytics moved to /underworld/analytics */}
          </div>

          {/* Right Column: Controls & Logs */}
          <div className="xl:col-span-3 space-y-6">
            <div className="h-auto">
              <TaskFrequencyControls
                onSave={handleSaveFrequency}
                initialData={strategy?.activity_distribution}
                afterlifeEnabled={status?.active_mode === 'afterlife'}
              />
            </div>


          </div>

        </div>
      </main>
    </div>
  );
}
