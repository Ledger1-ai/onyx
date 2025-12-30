// Dashboard JavaScript
class TwitterAgentDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        const now = new Date();
        this.currentDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().split('T')[0];
        this.lastRequestedDate = this.currentDate;
        this.lastUpdate = null;
        this.isLoading = false;
        this.currentAnalyticsRange = '7D';

        this.init();
    }

    init() {
        this.initializeSocket();
        this.setupEventListeners();
        this.loadInitialData();
        this.setupCharts();
        this.setupAccountCharts();
        this.setupAdaptiveWidgets();

        // Start real-time updates every second
        setInterval(() => this.updateTimestamps(), 1000);
        setInterval(() => this.refreshData(), 5000); // Real-time updates every 5 seconds
    }

    initializeSocket() {
        this.socket = io({ transports: ["websocket", "polling"] });

        this.socket.on('connect', () => {
            console.log('Connected to dashboard server');
            this.updateSystemStatus('online');
            try {
                const now = new Date();
                const today = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().split('T')[0];
                this.currentDate = today;
                this.loadSchedule(today, true);
            } catch (e) { /* no-op */ }
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from dashboard server');
            this.updateSystemStatus('offline');
        });

        this.socket.on('status_update', (data) => {
            this.updateDashboard(data);
        });

        this.socket.on('status', (data) => {
            this.updateDashboard(data);
        });

        // Real-time schedule updates
        this.socket.on('schedule_update', (data) => {
            this.updateScheduleDisplay(data);
        });

        // Real-time settings updates
        this.socket.on('settings_update', (data) => {
            this.updateSettingsDisplay(data);
        });
    }

    setupEventListeners() {
        // Control buttons
        document.getElementById('start-agent').addEventListener('click', () => this.startAgent());
        document.getElementById('stop-agent').addEventListener('click', () => this.stopAgent());
        document.getElementById('trigger-optimization').addEventListener('click', () => this.triggerOptimization());
        document.getElementById('refresh-data').addEventListener('click', () => this.refreshData());

        // Date navigation
        document.getElementById('prev-day').addEventListener('click', () => this.changeDate(-1));
        document.getElementById('next-day').addEventListener('click', () => this.changeDate(1));

        // Toast close
        document.getElementById('close-toast').addEventListener('click', () => this.hideToast());

        // Clear logs
        const clearLogsBtn = document.getElementById('clear-logs');
        if (clearLogsBtn) {
            clearLogsBtn.addEventListener('click', () => this.clearLogs());
        }

        // Toggle switches with real-time updates
        document.getElementById('enable-shoutouts').addEventListener('change', (e) => {
            this.updateToggleSetting('enable_follower_shoutouts', e.target.checked);
        });

        document.getElementById('enable-auto-replies').addEventListener('change', (e) => {
            this.updateToggleSetting('enable_auto_replies', e.target.checked);
        });

        // Input fields with real-time updates
        document.getElementById('max-shoutouts').addEventListener('change', (e) => {
            this.updateInputSetting('max_shoutouts_per_session', parseInt(e.target.value));
        });

        document.getElementById('max-replies').addEventListener('change', (e) => {
            this.updateInputSetting('max_auto_replies_per_session', parseInt(e.target.value));
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', (event) => {
            // Don't close if clicking on the dropdown itself or a clickable task name
            if (!event.target.closest('#task-swap-dropdown') &&
                !event.target.closest('.cursor-pointer')) {
                this.closeAllDropdowns();
            }
        });

        // Analytics range controls
        const btn7 = document.getElementById('analytics-7D');
        const btn30 = document.getElementById('analytics-30D');
        const btn90 = document.getElementById('analytics-90D');
        if (btn7) btn7.addEventListener('click', () => { this.currentAnalyticsRange = '7D'; this.loadPerformanceData(); });
        if (btn30) btn30.addEventListener('click', () => { this.currentAnalyticsRange = '30D'; this.loadPerformanceData(); });
        if (btn90) btn90.addEventListener('click', () => { this.currentAnalyticsRange = '90D'; this.loadPerformanceData(); });

        // Task frequency sliders
        this.setupTaskFrequencySliders();
    }

    setupTaskFrequencySliders() {
        const sliders = [
            'tweet', 'scroll_engage', 'search_engage', 'reply',
            'content_creation', 'thread', 'radar_discovery'
        ];

        // Initialize current values
        this.currentDistribution = {
            tweet: 18,
            scroll_engage: 35,
            search_engage: 15,
            reply: 18,
            content_creation: 10,
            thread: 2,
            radar_discovery: 2
        };

        // Preset distributions
        this.presetDistributions = {
            balanced: {
                tweet: 18, scroll_engage: 35, search_engage: 15, reply: 18,
                content_creation: 10, thread: 2, radar_discovery: 2
            },
            engagement: {
                tweet: 10, scroll_engage: 45, search_engage: 25, reply: 15,
                content_creation: 3, thread: 1, radar_discovery: 1
            },
            content: {
                tweet: 25, scroll_engage: 20, search_engage: 10, reply: 10,
                content_creation: 25, thread: 8, radar_discovery: 2
            },
            discovery: {
                tweet: 15, scroll_engage: 20, search_engage: 30, reply: 10,
                content_creation: 5, thread: 5, radar_discovery: 15
            }
        };

        sliders.forEach(taskType => {
            const slider = document.getElementById(`${taskType}-slider`);
            const percentage = document.getElementById(`${taskType}-percentage`);

            if (slider && percentage) {
                // Set initial values
                slider.value = this.currentDistribution[taskType];
                percentage.textContent = `${this.currentDistribution[taskType]}%`;

                slider.addEventListener('input', (event) => {
                    this.handleSliderChange(taskType, parseInt(event.target.value));
                });
            }
        });

        // Preset button functionality
        Object.keys(this.presetDistributions).forEach(presetName => {
            const button = document.getElementById(`preset-${presetName}`);
            if (button) {
                button.addEventListener('click', () => {
                    this.applyPreset(presetName);
                });
            }
        });

        // Save button functionality
        const saveButton = document.getElementById('save-frequency-btn');
        if (saveButton) {
            saveButton.addEventListener('click', () => {
                this.saveTaskFrequencies();
            });
        }

        this.updateTotalPercentage();
    }

    applyPreset(presetName) {
        if (this.presetDistributions[presetName]) {
            this.currentDistribution = { ...this.presetDistributions[presetName] };

            // Update all sliders and percentages
            Object.keys(this.currentDistribution).forEach(taskType => {
                const slider = document.getElementById(`${taskType}-slider`);
                const percentage = document.getElementById(`${taskType}-percentage`);

                if (slider && percentage) {
                    slider.value = this.currentDistribution[taskType];
                    percentage.textContent = `${this.currentDistribution[taskType]}%`;
                }
            });

            this.updateTotalPercentage();

            // Visual feedback
            const button = document.getElementById(`preset-${presetName}`);
            if (button) {
                button.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    button.style.transform = '';
                }, 150);
            }
        }
    }

    handleSliderChange(changedTaskType, newValue) {
        // Clamp input
        newValue = Math.max(0, Math.min(100, Number(newValue) || 0));

        // Set changed value first
        this.currentDistribution[changedTaskType] = newValue;

        // Compute others' sum
        const keys = Object.keys(this.currentDistribution);
        const others = keys.filter(k => k !== changedTaskType);
        const othersSum = others.reduce((s, k) => s + this.currentDistribution[k], 0);

        // Target others total to keep overall 100
        const targetOthers = Math.max(0, 100 - newValue);

        // If no others or target is zero, zero out others
        if (others.length === 0 || targetOthers === 0) {
            others.forEach(k => { this.currentDistribution[k] = 0; });
        } else {
            // If current others sum is zero, distribute evenly
            if (othersSum === 0) {
                const even = Math.floor(targetOthers / others.length);
                let remainder = targetOthers - even * others.length;
                others.forEach((k, idx) => {
                    this.currentDistribution[k] = even + (remainder > 0 ? 1 : 0);
                    remainder -= 1;
                });
            } else {
                // Scale others proportionally to match targetOthers
                const scaled = others.map(k => ({ k, v: this.currentDistribution[k] * (targetOthers / othersSum) }));
                // Round and fix drift
                const rounded = scaled.map(x => ({ k: x.k, v: Math.round(x.v) }));
                let drift = targetOthers - rounded.reduce((s, x) => s + x.v, 0);
                // Adjust drift by adding/subtracting 1 to elements with largest decimal parts
                if (drift !== 0) {
                    const deltas = scaled.map((x, i) => ({ k: x.k, frac: x.v - Math.floor(x.v), idx: i }));
                    deltas.sort((a, b) => b.frac - a.frac);
                    for (let i = 0; i < Math.abs(drift); i++) {
                        const idx = drift > 0 ? i % rounded.length : i % rounded.length;
                        // Choose which element to adjust based on sign
                        if (drift > 0) {
                            rounded[idx].v += 1;
                        } else {
                            // subtract from the largest values first to avoid negative
                            const maxIdx = rounded.reduce((mi, x, j) => (x.v > rounded[mi].v ? j : mi), 0);
                            if (rounded[maxIdx].v > 0) rounded[maxIdx].v -= 1;
                        }
                    }
                }
                // Apply
                rounded.forEach(x => { this.currentDistribution[x.k] = Math.max(0, Math.min(100, x.v)); });
            }
        }

        // Final guard to ensure sum is exactly 100
        let total = Object.values(this.currentDistribution).reduce((s, v) => s + v, 0);
        if (total !== 100) {
            const fix = 100 - total;
            // Prefer adjusting a task other than the changed one
            const adjustKey = others.find(k => this.currentDistribution[k] + fix >= 0 && this.currentDistribution[k] + fix <= 100) || changedTaskType;
            this.currentDistribution[adjustKey] = Math.max(0, Math.min(100, this.currentDistribution[adjustKey] + fix));
        }

        // Update UI
        Object.keys(this.currentDistribution).forEach(taskType => {
            const slider = document.getElementById(`${taskType}-slider`);
            const percentage = document.getElementById(`${taskType}-percentage`);
            if (slider && percentage) {
                slider.value = this.currentDistribution[taskType];
                percentage.textContent = `${this.currentDistribution[taskType]}%`;
            }
        });

        this.updateTotalPercentage();
    }

    updateTotalPercentage() {
        const total = Object.values(this.currentDistribution).reduce((sum, val) => sum + val, 0);

        const totalElement = document.getElementById('total-percentage');
        const saveButton = document.getElementById('save-frequency-btn');

        if (totalElement) {
            totalElement.textContent = `${total}%`;

            // Color coding based on total
            if (total === 100) {
                totalElement.className = 'text-lg font-bold text-green-400';
            } else if (total >= 95 && total <= 105) {
                totalElement.className = 'text-lg font-bold text-yellow-400';
            } else {
                totalElement.className = 'text-lg font-bold text-red-400';
            }
        }

        // Enable/disable save button based on total
        if (saveButton) {
            if (total === 100) {
                saveButton.disabled = false;
                saveButton.classList.remove('opacity-50', 'cursor-not-allowed');
                saveButton.classList.add('shimmer-effect');
            } else {
                saveButton.disabled = true;
                saveButton.classList.add('opacity-50', 'cursor-not-allowed');
                saveButton.classList.remove('shimmer-effect');
            }
        }
    }

    async saveTaskFrequencies() {
        const saveButton = document.getElementById('save-frequency-btn');

        try {
            // Show loading state
            if (saveButton) {
                this.setButtonLoading(saveButton, true);
            }

            this.showToast('Updating task distribution...', 'info');

            console.log('🔧 Sending distribution:', this.currentDistribution);

            // Send the new distribution to the backend
            const response = await fetch('/api/tasks/update-frequencies', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    distribution: this.currentDistribution
                })
            });

            console.log('📡 Response status:', response.status);
            console.log('📡 Response headers:', response.headers);

            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                // Try to get the HTML response for debugging
                const htmlText = await response.text();
                console.error('❌ Received HTML instead of JSON:', htmlText.substring(0, 200));
                throw new Error('Server returned HTML instead of JSON. Check server logs.');
            }

            const data = await response.json();
            console.log('📊 Response data:', data);

            if (response.ok && data.success) {
                this.showToast(`Updated ${data.updated_tasks || 0} scheduled tasks`, 'success');

                // Refresh the schedule display to show updated tasks
                await this.loadSchedule();

            } else {
                throw new Error(data.error || 'Failed to update task frequencies');
            }

        } catch (error) {
            console.error('💥 Error saving task frequencies:', error);
            this.showToast(`Update failed: ${error.message}`, 'error');
        } finally {
            // Remove loading state
            if (saveButton) {
                this.setButtonLoading(saveButton, false);
            }
        }
    }

    async loadInitialData() {
        this.showLoading(true);

        try {
            // Set initial date display if present
            const scheduleDateEl = document.getElementById('schedule-date');
            if (scheduleDateEl) scheduleDateEl.textContent = new Date(this.currentDate + 'T00:00:00').toLocaleDateString();

            // Ensure schedule loads with a normalized date immediately
            await this.loadSchedule(this.currentDate, true);
            await Promise.all([
                this.loadSystemStatus(),
                this.loadPlatformStatus(), // New platform status check
                this.loadPerformanceData(),
                this.loadOptimizationData(),
                this.loadLogs()
            ]);

            // Only show success toast on initial load, not for real-time updates
            this.showToast('ANUBIS ONLINE', 'success');
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showToast('Error loading dashboard data', 'error');
        }

        this.showLoading(false);
    }

    async loadPlatformStatus() {
        try {
            const response = await fetch('/api/auth/status');
            const data = await response.json();

            if (response.ok) {
                this.updatePlatformStatus(data);
            }
        } catch (error) {
            console.error('Error loading platform status:', error);
        }
    }

    updatePlatformStatus(data) {
        // Twitter
        const twInd = document.getElementById('status-twitter-indicator');
        const twText = document.getElementById('status-twitter-text');
        if (twInd && twText) {
            if (data.twitter) {
                twInd.className = 'w-2 h-2 rounded-full bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.5)]';
                twText.className = 'text-xs text-green-400';
                twText.textContent = 'Connected';
            } else {
                twInd.className = 'w-2 h-2 rounded-full bg-red-500';
                twText.className = 'text-xs text-red-400';
                twText.textContent = 'Disconnected';
            }
        }

        // LinkedIn
        const liInd = document.getElementById('status-linkedin-indicator');
        const liText = document.getElementById('status-linkedin-text');
        const liBtn = document.getElementById('btn-linkedin-login');

        if (liInd && liText) {
            if (data.linkedin) {
                liInd.className = 'w-2 h-2 rounded-full bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.5)]';
                liText.className = 'text-xs text-green-400';
                liText.textContent = 'Connected';
                if (liBtn) liBtn.classList.add('hidden');
            } else {
                liInd.className = 'w-2 h-2 rounded-full bg-red-500';
                liText.className = 'text-xs text-red-400';
                liText.textContent = 'Disconnected';
                if (liBtn) {
                    liBtn.classList.remove('hidden');
                    // Ensure listener is attached (idempotent via named function or just re-attach)
                    liBtn.onclick = () => this.triggerLinkedInLogin();
                }
            }
        }
    }

    async triggerLinkedInLogin() {
        try {
            this.showToast('Launching LinkedIn Login...', 'info');
            const response = await fetch('/api/auth/linkedin/login', { method: 'POST' });
            const data = await response.json();

            if (data.status === 'success') {
                this.showToast('Login window opened on server', 'success');
            } else {
                this.showToast('Failed to open login: ' + data.message, 'error');
            }
        } catch (e) {
            this.showToast('Error triggering login', 'error');
        }
    }

    async loadSystemStatus(silent = false) {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            if (response.ok) {
                this.updateDashboard(data);
            } else {
                if (!silent) {
                    throw new Error(data.error || 'Failed to load system status');
                }
            }
        } catch (error) {
            if (!silent) {
                console.error('Error loading system status:', error);
                this.updateSystemStatus('error');
            }
        }
    }

    async loadSchedule(date = null, silent = false) {
        try {
            const targetDate = date || this.currentDate;
            // Track the last requested date to avoid stale renders
            this.lastRequestedDate = targetDate;
            const response = await fetch(`/api/schedule?date=${targetDate}`);
            const data = await response.json();

            if (response.ok) {
                // Guard against out-of-order responses
                const incoming = (data && data.date) ? data.date : targetDate;
                if (incoming === this.lastRequestedDate) {
                    this.updateScheduleDisplay(data);
                } else {
                    console.warn('Stale schedule response ignored:', incoming, 'expected:', this.lastRequestedDate);
                }
            } else {
                if (!silent) {
                    throw new Error(data.error || 'Failed to load schedule');
                }
            }
        } catch (error) {
            if (!silent) {
                console.error('Error loading schedule:', error);
            }
        }
    }

    async loadPerformanceData() {
        try {
            const response = await fetch(`/api/performance?days=7&time_range=${encodeURIComponent(this.currentAnalyticsRange || '7D')}`);
            const data = await response.json();

            if (response.ok) {
                this.updatePerformanceDisplay(data);
                this.updateCharts(data);
                this.updateAccountOverview(data);
            } else {
                throw new Error(data.error || 'Failed to load performance data');
            }
        } catch (error) {
            console.error('Error loading performance data:', error);
        }
    }

    async loadOptimizationData() {
        try {
            const response = await fetch('/api/optimization');
            const data = await response.json();

            if (response.ok) {
                this.updateStrategyDisplay(data);
            } else {
                throw new Error(data.error || 'Failed to load optimization data');
            }
        } catch (error) {
            console.error('Error loading optimization data:', error);
        }
    }

    async loadLogs() {
        try {
            const response = await fetch('/api/logs?limit=50');
            const data = await response.json();

            if (response.ok) {
                this.updateLogsDisplay(data);
            } else {
                throw new Error(data.error || 'Failed to load logs');
            }
        } catch (error) {
            console.error('Error loading logs:', error);
        }
    }

    updateDashboard(data) {
        this.lastUpdate = new Date();

        // Update status cards
        this.updateStatusCards(data);

        // Update live metrics
        this.updateLiveMetrics(data);

        // Update recent activity
        this.updateRecentActivity(data);

        // Update timestamps
        this.updateLastUpdateTime();
    }

    updateStatusCards(data) {
        // Current Activity
        const currentActivity = data.current_activity?.activity;
        const activityElement = document.getElementById('current-activity');
        if (currentActivity) {
            activityElement.textContent = this.formatActivityName(currentActivity);

            // Update progress bar
            const progress = data.current_activity?.progress || 0;
            document.getElementById('activity-progress').style.width = `${progress}%`;
        } else {
            activityElement.textContent = 'No active activity';
            document.getElementById('activity-progress').style.width = '0%';
        }

        // Next Activity
        const nextActivity = data.next_activity?.activity;
        const nextElement = document.getElementById('next-activity');
        const timeUntilElement = document.getElementById('time-until');

        if (nextActivity) {
            nextElement.textContent = this.formatActivityName(nextActivity);
            timeUntilElement.textContent = data.next_activity?.time_until || '--';
        } else {
            nextElement.textContent = 'No scheduled activity';
            timeUntilElement.textContent = '--';
        }

        // Daily Progress
        const dailyProgress = data.daily_progress || 0;
        document.getElementById('daily-progress').textContent = `${Math.round(dailyProgress)}%`;

        const completed = data.completed_activities || 0;
        const total = data.total_activities || 0;
        document.getElementById('activities-completed').textContent = `${completed}/${total} completed`;

        // Performance Score
        const metrics = data.performance_metrics;
        if (metrics && metrics.overall_score !== undefined) {
            const score = Math.round(metrics.overall_score * 100);
            document.getElementById('performance-score').textContent = `${score}%`;

            const scoreClass = this.getPerformanceScoreClass(score);
            const scoreElement = document.getElementById('performance-score');
            scoreElement.className = `text-2xl font-bold ${scoreClass}`;

            // Update trend
            const trend = metrics.trend || 'stable';
            document.getElementById('performance-trend').textContent = `Trend: ${trend}`;
        }
    }

    updateLiveMetrics(data) {
        const metricsContainer = document.getElementById('live-metrics');
        if (!metricsContainer) {
            // Container may not exist on certain views; avoid errors
            return;
        }
        const metrics = data.performance_metrics || {};

        const metricsHtml = Object.entries(metrics)
            .filter(([key, value]) => typeof value === 'number')
            .map(([key, value]) => {
                const formattedKey = this.formatMetricName(key);
                const formattedValue = this.formatMetricValue(key, value);
                const icon = this.getMetricIcon(key);

                return `
                    <div class="metric-item flex items-center justify-between p-3 rounded-lg">
                        <div class="flex items-center">
                            <i class="${icon} text-cyan-300 mr-3"></i>
                            <span class="micro">${formattedKey}</span>
                        </div>
                        <span class="metric-value text-lg font-semibold text-cyan-100">${formattedValue}</span>
                    </div>
                `;
            })
            .join('');

        metricsContainer.innerHTML = metricsHtml || '<p class="text-gray-500 text-center">No metrics available</p>';
    }

    updateRecentActivity(data) {
        // This would be populated from logs or activity data
        // For now, showing placeholder
        const container = document.getElementById('recent-activity');
        container.innerHTML = `
            <div class="micro-muted">
                <p class="mb-2">Recent activities will appear here</p>
                <p class="micro">Last update: ${new Date().toLocaleTimeString()}</p>
            </div>
        `;
    }

    updateScheduleDisplay(data) {
        // Only render if matches the last requested date (prevents race with Today/Prev/Next)
        if (data && data.date && this.lastRequestedDate && data.date !== this.lastRequestedDate) {
            return;
        }

        // Only update date if provided - use timezone-safe parsing
        if (data.date) {
            const label = document.getElementById('schedule-date');
            if (label) label.textContent = new Date(data.date + 'T00:00:00').toLocaleDateString();
        }

        const timeline = document.getElementById('schedule-timeline');
        const slots = data.slots || [];

        if (slots.length === 0) {
            timeline.innerHTML = '<div class="glass-mini-panel p-4 text-center"><p class="text-cyan-400/70 font-mono">NO MISSIONS SCHEDULED</p></div>';
            return;
        }

        const now = new Date();
        console.log('🗓️ Rendering schedule slots:', slots);
        console.log('⏰ Current time:', now);

        const timelineHtml = slots
            .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
            .map(slot => {
                console.log('📋 Processing slot:', {
                    id: slot.slot_id || slot.id,
                    activity: slot.activity_type,
                    status: slot.status,
                    start_time: slot.start_time
                });
                const startTime = new Date(slot.start_time);
                const isCurrentActivity = startTime <= now && now <= new Date(slot.end_time);
                const timeStr = startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                const statusClass = `activity-status-${slot.status}`;
                const pulseClass = isCurrentActivity ? 'active' : '';
                const activityIcon = this.getActivityIcon(slot.activity_type);

                // Only make future scheduled tasks clickable for swapping
                const isSwappable = slot.status === 'scheduled' && startTime > now;
                console.log('🔄 Slot swappable check:', {
                    id: slot.slot_id || slot.id,
                    status: slot.status,
                    startTime: startTime.toISOString(),
                    now: now.toISOString(),
                    isSwappable: isSwappable,
                    statusMatch: slot.status === 'scheduled',
                    timeMatch: startTime > now
                });

                // Ensure we have a valid slot ID before making it clickable
                const validSlotId = slot.slot_id || slot.id;
                if (!validSlotId) {
                    console.warn('⚠️ Slot missing ID:', slot);
                }

                // Make ALL scheduled tasks clickable for debugging purposes, but only if they have a valid ID
                const isClickableForDebug = slot.status === 'scheduled' && validSlotId;
                const taskNameClass = isClickableForDebug ? 'cursor-pointer hover:text-blue-400 underline text-decoration-underline' : '';
                const taskNameClick = isClickableForDebug ? `onclick="event.stopPropagation(); console.log('🖱️ Task clicked:', '${validSlotId}'); dashboard.testTaskClick('${validSlotId}', '${slot.activity_type}', this); return false;"` : '';

                console.log('🎨 Task rendering:', {
                    id: validSlotId,
                    isClickable: isClickableForDebug,
                    taskNameClass: taskNameClass,
                    hasClick: !!taskNameClick
                });

                // Make status clickable for manual override
                const statusClickable = validSlotId ? 'cursor-pointer hover:bg-gray-600 transition-colors' : '';
                const statusClick = validSlotId ? `onclick="event.stopPropagation(); dashboard.showTaskStatusDropdown('${validSlotId}', this); return false;"` : '';
                const statusTitle = validSlotId ? 'Click to change status' : '';

                return `
                    <div class="timeline-item ${slot.status} ${pulseClass}" data-slot-id="${validSlotId || ''}">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center">
                                <i class="${activityIcon} text-xl mr-4"></i>
                                <div class="relative">
                                    <p class="font-bold text-cyan-300 font-mono uppercase ${taskNameClass}" 
                                       ${taskNameClick}
                                       title="${isSwappable ? 'Click to swap this task' : ''}">
                                        ${this.formatActivityName(slot.activity_type)}
                                    </p>
                                    <p class="text-sm text-cyan-400/70 font-mono">${timeStr} - ${slot.priority} PRIORITY</p>
                                </div>
                            </div>
                            <span class="glass-mini-button ${statusClass} font-mono task-status ${statusClickable}" 
                                  ${statusClick}
                                  title="${statusTitle}">
                                ${slot.status.replace('_', ' ').toUpperCase()}
                            </span>
                        </div>
                        ${slot.description ? `<p class="text-sm text-cyan-400/80 mt-2 font-mono">${slot.description}</p>` : ''}
                    </div>
                `;
            })
            .join('');

        timeline.innerHTML = timelineHtml;
        this.refreshAdaptiveWidgets();
    }

    updatePerformanceDisplay(data) {
        // Update metrics and trends
        console.log('Performance data:', data);
    }

    updateAccountOverview(data) {
        const container = document.getElementById('account-overview');
        if (!container) return;

        const overview = (data && data.account_overview) || {};
        const current = overview.current || {};
        const pct = overview.percent_change || {};

        const metrics = [
            { key: 'impressions', label: 'Impressions' },
            { key: 'engagements', label: 'Engagements' },
            { key: 'engagement_rate', label: 'Engagement Rate', isPercent: true },
            { key: 'profile_visits', label: 'Profile Visits' },
            { key: 'likes', label: 'Likes' },
            { key: 'replies', label: 'Replies' },
            { key: 'reposts', label: 'Reposts' },
            { key: 'bookmarks', label: 'Bookmarks' },
            { key: 'shares', label: 'Shares' },
            { key: 'total_followers', label: 'Followers' },
            { key: 'verified_followers', label: 'Verified Followers' },
            { key: 'follows', label: 'Follows' }
        ];

        const tiles = metrics.map(m => {
            const val = current[m.key];
            const change = pct[m.key];
            const valueStr = (m.isPercent ? this.formatPercent(val) : this.formatCompactNumber(val));
            const changeHtml = this.renderChangeBadge(change);
            return `
                <div class="metric-item flex items-center justify-between p-3 rounded-lg">
                    <div class="flex flex-col">
                        <span class="micro">${m.label}</span>
                        <span class="metric-value text-lg font-semibold text-cyan-100">${valueStr}</span>
                    </div>
                    <div>${changeHtml}</div>
                </div>
            `;
        }).join('');

        container.innerHTML = tiles || '<p class="text-gray-500 text-center">No account analytics available</p>';
    }

    updateStrategyDisplay(data) {
        const container = document.getElementById('strategy-info');
        const strategy = data.current_strategy;

        if (!strategy) {
            container.innerHTML = '<p class="text-gray-500">No strategy information available</p>';
            return;
        }

        const html = `
            <div class="space-y-3">
                <div>
                    <h4 class="text-cyan-200 font-semibold">${strategy.name}</h4>
                    <p class="micro-muted">${strategy.description}</p>
                </div>
                
                <div>
                    <h5 class="micro mb-2">Activity Distribution</h5>
                    <div class="space-y-1">
                        ${Object.entries(strategy.activity_distribution)
                .map(([activity, percentage]) => `
                                <div class="flex justify-between micro">
                                    <span>${this.formatActivityName(activity)}</span>
                                    <span>${Math.round(percentage * 100)}%</span>
                                </div>
                            `).join('')}
                    </div>
                </div>
                
                <div>
                    <h5 class="micro mb-2">Optimal Times</h5>
                    <div class="flex flex-wrap gap-1">
                        ${strategy.optimal_posting_times.map(time =>
                    `<span class="glass-mini-panel px-2 py-1 micro">${time}</span>`
                ).join('')}
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    updateLogsDisplay(data) {
        const container = document.getElementById('activity-logs');
        const sessions = data.recent_sessions || [];
        const analyses = data.recent_analyses || [];

        // Combine and sort logs
        const allLogs = [
            ...sessions.map(session => ({
                type: 'session',
                timestamp: session.start_time,
                message: `${this.formatActivityName(session.activity_type)} session - ${session.accounts_engaged} accounts engaged`,
                level: 'info'
            })),
            ...analyses.map(analysis => ({
                type: 'analysis',
                timestamp: analysis.date,
                message: `Daily analysis completed - Score: ${Math.round((analysis.performance_score || 0) * 100)}%`,
                level: 'success'
            }))
        ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 20);

        const logsHtml = allLogs.map(log => {
            const time = new Date(log.timestamp).toLocaleString();
            return `
                <div class="log-entry log-entry-${log.level}">
                    <div class="flex justify-between items-start">
                        <span class="text-sm text-current">${log.message}</span>
                        <span class="micro-muted ml-2">${time}</span>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = logsHtml || '<p class="text-gray-500 text-center">No logs available</p>';
    }

    setupCharts() {
        // Engagement Chart
        const engagementCanvas = document.getElementById('engagement-chart');
        if (engagementCanvas && typeof engagementCanvas.getContext === 'function') {
            const engagementCtx = engagementCanvas.getContext('2d');
            this.charts.engagement = new Chart(engagementCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Engagement Rate',
                        data: [],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1
                        }
                    }
                }
            });
        } else {
            console.warn('Engagement chart canvas not found or unsupported');
            this.charts.engagement = null;
        }

        // Activity Chart
        const activityCanvas = document.getElementById('activity-chart');
        if (activityCanvas && typeof activityCanvas.getContext === 'function') {
            const activityCtx = activityCanvas.getContext('2d');
            this.charts.activity = new Chart(activityCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
                            '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        } else {
            console.warn('Activity chart canvas not found or unsupported');
            this.charts.activity = null;
        }
    }

    setupAccountCharts() {
        // Initialize account trends charts if canvases exist
        const makeLine = (canvasId, label, color) => {
            const el = document.getElementById(canvasId);
            if (el && typeof el.getContext === 'function') {
                const ctx = el.getContext('2d');
                return new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label,
                            data: [],
                            borderColor: color,
                            backgroundColor: color + '22', // translucent fill
                            tension: 0.3,
                            pointRadius: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
            return null;
        };

        this.charts.accImpressions = makeLine('account-impressions-chart', 'Impressions', '#0ea5e9'); // cyan-500
        this.charts.accEngagements = makeLine('account-engagements-chart', 'Engagements', '#22c55e'); // green-500
        this.charts.accFollowers = makeLine('account-followers-chart', 'Followers', '#eab308'); // yellow-500
    }

    updateCharts(data) {
        // Update engagement chart with trend data
        if (data.trends && data.trends.trends && this.charts.engagement) {
            const engagementTrend = data.trends.trends.engagement_rate;
            if (engagementTrend && engagementTrend.values) {
                const labels = engagementTrend.values.map(v => v[0]);
                const values = engagementTrend.values.map(v => v[1]);

                this.charts.engagement.data.labels = labels;
                this.charts.engagement.data.datasets[0].data = values;
                try {
                    this.charts.engagement.update();
                } catch (e) {
                    console.warn('Engagement chart update failed', e);
                }
            }
        }

        // Update activity chart with recent activities
        // This would need activity distribution data; guard chart existence
        if (this.charts.activity) {
            // Placeholder: keep activity chart responsive
            try {
                this.charts.activity.update();
            } catch (e) {
                console.warn('Activity chart update failed', e);
            }
        }

        // Account trends charts (impressions / engagements / followers)
        const acct = (data && data.account_trends) || {};
        const updateSeries = (series, chart) => {
            if (!series || !series.values || !chart) return;
            const labels = series.values.map(v => v[0]);
            const values = series.values.map(v => v[1]);
            chart.data.labels = labels;
            chart.data.datasets[0].data = values;
            try {
                chart.update();
            } catch (e) {
                console.warn('Account chart update failed', e);
            }
        };

        updateSeries(acct.impressions, this.charts.accImpressions);
        updateSeries(acct.engagements, this.charts.accEngagements);
        updateSeries(acct.total_followers, this.charts.accFollowers);
    }

    // Adaptive widget sizing
    setupAdaptiveWidgets() {
        try {
            const widgets = Array.from(document.querySelectorAll('.widget'));
            if (widgets.length === 0) return;
            const fit = (el) => this.computeWidgetScale(el);
            const ro = new ResizeObserver((entries) => {
                entries.forEach(entry => {
                    fit(entry.target);
                });
            });
            widgets.forEach(el => ro.observe(el));
            this._widgetResizeObserver = ro;
            // Initial fit
            widgets.forEach(el => fit(el));
        } catch (e) {
            console.warn('Adaptive widgets setup failed', e);
        }
    }

    computeWidgetScale(el) {
        try {
            const container = el;
            const target = el.querySelector('.card-body-scroll') || el;
            const h = container.clientHeight || 0;
            const ch = target.scrollHeight || 0;
            if (!h || !ch) return;
            const ratio = h / ch;
            let scale;
            if (ratio < 1) {
                // Content overflows: shrink text gently
                scale = Math.max(0.85, Math.min(1, ratio * 0.98));
            } else {
                // Extra space: gently grow text (cap growth)
                scale = Math.min(1.15, 1 + Math.min(0.15, (ratio - 1) * 0.25));
            }
            el.style.setProperty('--widget-scale', String(scale));
        } catch (e) {
            // no-op
        }
    }

    refreshAdaptiveWidgets() {
        try {
            document.querySelectorAll('.widget').forEach(el => this.computeWidgetScale(el));
        } catch (e) {
            // no-op
        }
    }

    // Control functions
    async startAgent() {
        const button = document.getElementById('start-agent');

        // Add null check for button
        if (button) {
            this.setButtonLoading(button, true);
        }

        try {
            const response = await fetch('/api/control/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();

            if (response.ok) {
                this.showToast('ANUBIS INITIALIZED', 'success');
                this.updateSystemStatus('online');
            } else {
                throw new Error(data.message || 'Failed to start agent');
            }
        } catch (error) {
            console.error('Error starting agent:', error);
            this.showToast(`INIT FAILED: ${error.message}`, 'error');
        }

        // Add null check for button
        if (button) {
            this.setButtonLoading(button, false);
        }
    }

    async stopAgent() {
        const button = document.getElementById('stop-agent');

        // Add null check for button
        if (button) {
            this.setButtonLoading(button, true);
        }

        try {
            const response = await fetch('/api/control/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();

            if (response.ok) {
                this.showToast('ANUBIS TERMINATED', 'success');
                this.updateSystemStatus('offline');
            } else {
                throw new Error(data.message || 'Failed to stop agent');
            }
        } catch (error) {
            console.error('Error stopping agent:', error);
            this.showToast(`TERMINATION FAILED: ${error.message}`, 'error');
        }

        // Add null check for button
        if (button) {
            this.setButtonLoading(button, false);
        }
    }

    async manageNotifications() {
        try {
            const settings = {
                enable_follower_shoutouts: document.getElementById('enable-shoutouts').checked,
                enable_auto_replies: document.getElementById('enable-auto-replies').checked,
                max_shoutouts_per_session: parseInt(document.getElementById('max-shoutouts').value),
                max_auto_replies_per_session: parseInt(document.getElementById('max-replies').value)
            };

            const response = await fetch('/api/notifications/manage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });

            const data = await response.json();

            if (response.ok) {
                this.showToast('AUTO MODE ACTIVE', 'success');
            } else {
                throw new Error(data.message || 'Failed to start notification management');
            }
        } catch (error) {
            console.error('Error managing notifications:', error);
            this.showToast(`AUTO MODE FAILED`, 'error');
        }
    }

    async triggerAutoReply() {
        try {
            const response = await fetch('/api/notifications/auto-reply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    max_replies: 5,
                    reply_style: 'helpful'
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showToast('REPLY EXECUTED', 'success');
            } else {
                throw new Error(data.message || 'Failed to trigger auto-reply');
            }
        } catch (error) {
            console.error('Error with auto-reply:', error);
            this.showToast(`REPLY FAILED`, 'error');
        }
    }

    async createShoutout() {
        try {
            const username = document.getElementById('shoutout-username').value.trim();
            if (!username) {
                this.showToast('USERNAME REQUIRED', 'warning');
                return;
            }

            const response = await fetch('/api/notifications/shoutout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username.replace('@', ''),
                    include_bio_analysis: true,
                    artwork_style: 'geometric'
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showToast(`SHOUTOUT DEPLOYED: ${username}`, 'success');
                document.getElementById('shoutout-username').value = '';
            } else {
                throw new Error(data.message || 'Failed to create shoutout');
            }
        } catch (error) {
            console.error('Error creating shoutout:', error);
            this.showToast(`SHOUTOUT FAILED`, 'error');
        }
    }

    async triggerOptimization() {
        const button = document.getElementById('trigger-optimization');
        this.setButtonLoading(button, true);

        try {
            const response = await fetch('/api/control/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();

            if (response.ok) {
                this.showToast('OPTIMIZATION ACTIVE', 'success');
                // Refresh data after optimization
                setTimeout(() => this.loadInitialData(), 2000);
            } else {
                throw new Error(data.message || 'Failed to trigger optimization');
            }
        } catch (error) {
            console.error('Error triggering optimization:', error);
            this.showToast(`OPTIMIZATION FAILED`, 'error');
        }

        this.setButtonLoading(button, false);
    }

    refreshData() {
        // Silent real-time updates - only update essential data
        // Removed frequent socket emits to avoid Engine.IO 'Too many packets in payload' with polling transport
        this.loadSystemStatus(true); // Pass silent flag
        this.loadSchedule(null, true); // Pass silent flag
    }

    changeDate(direction) {
        const currentDate = new Date(this.currentDate + 'T00:00:00');
        currentDate.setDate(currentDate.getDate() + direction);
        const norm = new Date(currentDate.getTime() - currentDate.getTimezoneOffset() * 60000);
        this.currentDate = norm.toISOString().split('T')[0];
        this.loadSchedule();
    }

    clearLogs() {
        document.getElementById('activity-logs').innerHTML = '<p class="text-gray-500 text-center">Logs cleared</p>';
    }

    // Utility functions
    updateSystemStatus(status) {
        // The status elements don't exist in the current HTML, so this is a no-op
        // Could be implemented later if status elements are added to the header
        console.log('System status updated to:', status);
    }

    updateLastUpdateTime() {
        if (this.lastUpdate) {
            document.getElementById('last-update-time').textContent = this.lastUpdate.toLocaleTimeString();
        }
    }

    updateTimestamps() {
        // Update relative timestamps in the UI
        this.updateLastUpdateTime();
    }

    formatActivityName(activity) {
        return activity.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    formatMetricName(metric) {
        return metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    formatMetricValue(metric, value) {
        if (metric.includes('rate') || metric.includes('score')) {
            return `${Math.round(value * 100)}%`;
        }
        if (metric.includes('count') || metric.includes('followers')) {
            return value.toLocaleString();
        }
        return value.toString();
    }

    getMetricIcon(metric) {
        const iconMap = {
            engagement_rate: 'fas fa-heart',
            follower_growth: 'fas fa-user-plus',
            tweet_impressions: 'fas fa-eye',
            reach: 'fas fa-globe',
            performance_score: 'fas fa-star'
        };
        return iconMap[metric] || 'fas fa-chart-bar';
    }

    formatCompactNumber(value) {
        if (value === undefined || value === null || isNaN(value)) return '0';
        const abs = Math.abs(value);
        if (abs >= 1e9) return (value / 1e9).toFixed(1).replace(/\.0$/, '') + 'B';
        if (abs >= 1e6) return (value / 1e6).toFixed(1).replace(/\.0$/, '') + 'M';
        if (abs >= 1e3) return (value / 1e3).toFixed(1).replace(/\.0$/, '') + 'K';
        return Number(value).toLocaleString();
    }

    formatPercent(value) {
        if (value === undefined || value === null || isNaN(value)) return '0%';
        // If value appears to be a fraction (0-1), convert to %
        if (value <= 1 && value >= 0) return `${Math.round(value * 100)}%`;
        return `${Math.round(value)}%`;
    }

    renderChangeBadge(change) {
        if (change === undefined || change === null || isNaN(change)) {
            return '<span class="micro-muted">--</span>';
        }
        const up = change > 0;
        const same = change === 0;
        const color = same ? 'text-gray-400' : (up ? 'text-green-500' : 'text-red-500');
        const arrow = same ? '' : (up ? '↑' : '↓');
        const val = Math.round(Math.abs(change));
        return `<span class="${color} font-mono">${arrow} ${val}%</span>`;
    }

    getActivityIcon(activity) {
        const iconMap = {
            tweet: 'fas fa-edit activity-icon-tweet',
            scroll_engage: 'fas fa-mouse activity-icon-scroll_engage',
            search_engage: 'fas fa-search activity-icon-search_engage',
            reply: 'fas fa-reply activity-icon-reply',
            auto_reply: 'fas fa-robot activity-icon-auto_reply',
            content_creation: 'fas fa-palette activity-icon-content_creation',
            radar_discovery: 'fas fa-satellite-dish activity-icon-radar_discovery',
            analytics_check: 'fas fa-chart-line activity-icon-analytics_check',
            monitor: 'fas fa-desktop activity-icon-monitor',
            performance_analysis: 'fas fa-chart-line activity-icon-performance_analysis',
            strategy_review: 'fas fa-clipboard-check activity-icon-strategy_review'
        };
        return iconMap[activity] || 'fas fa-cog';
    }

    getPerformanceScoreClass(score) {
        if (score >= 80) return 'performance-excellent';
        if (score >= 60) return 'performance-good';
        if (score >= 40) return 'performance-fair';
        return 'performance-poor';
    }

    setButtonLoading(button, loading) {
        // Add null check to prevent errors
        if (!button) {
            console.warn('setButtonLoading called with null button');
            return;
        }

        if (loading) {
            button.classList.add('btn-loading');
            button.disabled = true;
        } else {
            button.classList.remove('btn-loading');
            button.disabled = false;
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (!overlay) return;
        if (show) {
            overlay.classList.remove('hidden');
            overlay.classList.add('flex');
        } else {
            overlay.classList.add('hidden');
            overlay.classList.remove('flex');
        }
    }

    showToast(message, type = 'info', title = '') {
        const toast = document.getElementById('notification-toast');
        const icon = document.getElementById('toast-icon');
        const titleElement = document.getElementById('toast-title');
        const messageElement = document.getElementById('toast-message');

        // Set icon and colors based on type
        const iconMap = {
            success: 'fas fa-check-circle text-green-500',
            error: 'fas fa-exclamation-circle text-red-500',
            warning: 'fas fa-exclamation-triangle text-yellow-500',
            info: 'fas fa-info-circle text-blue-500'
        };

        icon.className = iconMap[type] || iconMap.info;
        titleElement.textContent = title || type.charAt(0).toUpperCase() + type.slice(1);
        messageElement.textContent = message;

        // Show toast
        toast.classList.remove('hidden');
        // Remove the translate-x-full class to slide it in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 10);

        // Auto-hide after 3 seconds
        setTimeout(() => this.hideToast(), 3000);
    }

    hideToast() {
        const toast = document.getElementById('notification-toast');
        // Add the translate-x-full class to slide it out
        toast.classList.add('translate-x-full');

        setTimeout(() => {
            toast.classList.add('hidden');
        }, 300);
    }

    async updateToggleSetting(setting, value) {
        try {
            const response = await fetch('/api/settings/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [setting]: value })
            });

            if (response.ok) {
                // More concise notifications
                const settingName = setting.replace(/_/g, ' ').replace('enable ', '').toUpperCase();
                this.showToast(`${settingName} ${value ? 'ON' : 'OFF'}`, 'success');
            } else {
                throw new Error('Failed to update setting');
            }
        } catch (error) {
            console.error('Error updating setting:', error);
            this.showToast(`Update failed`, 'error');
        }
    }

    async updateInputSetting(setting, value) {
        try {
            const response = await fetch('/api/settings/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [setting]: value })
            });

            if (response.ok) {
                // More concise notifications
                const settingName = setting.replace(/_/g, ' ').replace('max ', '').replace(' per session', '').toUpperCase();
                this.showToast(`${settingName}: ${value}`, 'success');
            } else {
                throw new Error('Failed to update setting');
            }
        } catch (error) {
            console.error('Error updating setting:', error);
            this.showToast(`Update failed`, 'error');
        }
    }

    updateSettingsDisplay(data) {
        // Update toggle states
        if (data.enable_follower_shoutouts !== undefined) {
            document.getElementById('enable-shoutouts').checked = data.enable_follower_shoutouts;
        }
        if (data.enable_auto_replies !== undefined) {
            document.getElementById('enable-auto-replies').checked = data.enable_auto_replies;
        }

        // Update input values
        if (data.max_shoutouts_per_session !== undefined) {
            document.getElementById('max-shoutouts').value = data.max_shoutouts_per_session;
        }
        if (data.max_auto_replies_per_session !== undefined) {
            document.getElementById('max-replies').value = data.max_auto_replies_per_session;
        }
    }

    async showSettings() {
        // Show the task configuration modal
        const modal = document.getElementById('task-config-modal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        await this.loadTaskConfiguration();
    }

    async loadTaskConfiguration() {
        try {
            const response = await fetch('/api/tasks/configuration');
            const data = await response.json();

            if (data.success) {
                this.renderTaskSelection(data.tasks);
                this.renderSchedule(data.schedule);
            } else {
                this.showNotification('Failed to load task configuration', 'error');
            }
        } catch (error) {
            console.error('Error loading task configuration:', error);
            this.showNotification('Error loading task configuration', 'error');
        }
    }

    renderTaskSelection(tasks) {
        const container = document.getElementById('task-selection');
        container.innerHTML = tasks.map(task => `
            <div class="flex items-center space-x-3 p-3 bg-gray-700 rounded">
                <input type="checkbox" 
                       id="task-${task.id}" 
                       ${task.enabled ? 'checked' : ''} 
                       class="form-checkbox h-5 w-5 text-blue-600"
                       onchange="dashboard.toggleTask('${task.id}')">
                <label for="task-${task.id}" class="text-white">
                    ${task.name}
                </label>
            </div>
        `).join('');
    }

    renderSchedule(schedule) {
        // This method is kept for compatibility but schedule is now managed in updateScheduleDisplay
        console.log('Schedule updated:', schedule);
    }

    async toggleTask(taskId) {
        try {
            const response = await fetch('/api/tasks/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ taskId })
            });

            const data = await response.json();
            if (data.success) {
                this.showToast(`Task ${data.enabled ? 'enabled' : 'disabled'} successfully`, 'success');
            } else {
                this.showToast('Failed to toggle task', 'error');
            }
        } catch (error) {
            console.error('Error toggling task:', error);
            this.showToast('Error toggling task', 'error');
        }
    }

    async regenerateSchedule() {
        try {
            // Show loading state
            this.showToast('Regenerating schedule...', 'info');

            const response = await fetch('/api/tasks/regenerate', {
                method: 'POST'
            });

            const data = await response.json();
            if (data.success) {
                this.closeTaskConfig(); // Close the modal
                await this.loadSchedule(); // Reload the schedule display
                this.showToast(data.message || 'Schedule regenerated successfully', 'success');
            } else {
                this.showToast(data.error || 'Failed to regenerate schedule', 'error');
            }
        } catch (error) {
            console.error('Error regenerating schedule:', error);
            this.showToast('Error regenerating schedule', 'error');
        }
    }

    async createFreshSchedule() {
        try {
            // Show loading state
            this.showToast('Creating fresh schedule...', 'info');

            const response = await fetch('/api/tasks/create-fresh', {
                method: 'POST'
            });

            const data = await response.json();
            if (data.success) {
                this.closeTaskConfig(); // Close the modal
                await this.loadSchedule(); // Reload the schedule display
                this.showToast(data.message || 'Fresh schedule created successfully', 'success');
            } else {
                this.showToast(data.error || 'Failed to create fresh schedule', 'error');
            }
        } catch (error) {
            console.error('Error creating fresh schedule:', error);
            this.showToast('Error creating fresh schedule', 'error');
        }
    }

    async saveTaskConfig() {
        try {
            const response = await fetch('/api/tasks/save-config', {
                method: 'POST'
            });

            const data = await response.json();
            if (data.success) {
                this.closeTaskConfig();
                this.showToast('Configuration saved successfully', 'success');
            } else {
                this.showToast('Failed to save configuration', 'error');
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showToast('Error saving configuration', 'error');
        }
    }

    closeTaskConfig() {
        const modal = document.getElementById('task-config-modal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        this.currentSwapTaskId = null; // Clear any stored task ID
    }

    testTaskClick(slotId, activityType, element) {
        // Validate slotId before proceeding
        if (!slotId || slotId === 'undefined' || slotId === 'null') {
            console.error('❌ Invalid slotId passed to testTaskClick:', slotId);
            this.showToast('Error: Invalid task ID. Please refresh the page and try again.', 'error');
            return;
        }

        console.log('🧪 TEST: Task click detected!', {
            slotId: slotId,
            activityType: activityType,
            element: element
        });

        this.showToast(`Loading swap options for ${activityType}...`, 'info');

        // Show the real API call dropdown directly
        this.showTaskSwapDropdown(slotId, element);
    }

    async showTaskSwapDropdown(slotId, element) {
        try {
            // Validate slotId before proceeding
            if (!slotId || slotId === 'undefined' || slotId === 'null') {
                console.error('❌ Invalid slotId passed to showTaskSwapDropdown:', slotId);
                this.showToast('Error: Invalid task ID. Please refresh the page and try again.', 'error');
                return;
            }

            console.log('🔄 showTaskSwapDropdown called with slotId:', slotId);
            console.log('🎯 Element clicked:', element);

            // Close any existing dropdowns
            this.closeAllDropdowns();

            // Show immediate feedback
            this.showToast('Loading swap options...', 'info');

            // Get swap options for this task
            console.log('📡 Fetching swap options...');
            const response = await fetch('/api/tasks/swap-options', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ taskId: slotId })
            });

            console.log('📨 Response status:', response.status);
            const data = await response.json();
            console.log('📋 Swap options data:', data);

            if (!data.success) {
                console.error('❌ API returned error:', data.error);
                this.showToast(data.error || 'Failed to load swap options', 'error');
                return;
            }

            if (!data.options || data.options.length === 0) {
                console.warn('⚠️ No swap options available');
                this.showToast('No alternative tasks available', 'warning');
                return;
            }

            // Create dropdown with simpler approach
            console.log('🎨 Creating dropdown...');
            this.createAndShowDropdown(slotId, data.options, element);

        } catch (error) {
            console.error('💥 Error in showTaskSwapDropdown:', error);
            this.showToast('Error loading swap options: ' + error.message, 'error');
        }
    }

    createAndShowDropdown(slotId, options, element) {
        // Remove any existing dropdown
        const existingDropdown = document.getElementById('task-swap-dropdown');
        if (existingDropdown) {
            existingDropdown.remove();
        }

        // Create dropdown element
        const dropdown = document.createElement('div');
        dropdown.id = 'task-swap-dropdown';

        // Set styles directly for maximum compatibility and visibility
        Object.assign(dropdown.style, {
            position: 'fixed',  // Use fixed positioning for viewport-relative placement
            backgroundColor: '#0f172a',  // Darker background for better visibility
            border: '2px solid #00ffff',  // Bright cyan border
            borderRadius: '8px',
            boxShadow: '0 0 30px rgba(0, 255, 255, 0.5), 0 10px 25px rgba(0, 0, 0, 0.8)',  // Cyber glow
            zIndex: '99999',  // Higher z-index
            minWidth: '220px',
            maxHeight: '300px',
            overflowY: 'auto',
            padding: '8px 0',
            display: 'block',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            animation: 'fadeIn 0.2s ease-out'
        });

        // Add animation keyframes if not already present
        if (!document.getElementById('dropdown-animations')) {
            const style = document.createElement('style');
            style.id = 'dropdown-animations';
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(-10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `;
            document.head.appendChild(style);
        }

        // Create header
        const header = document.createElement('div');
        header.textContent = 'SWAP TASK WITH:';
        Object.assign(header.style, {
            padding: '10px 16px',
            borderBottom: '1px solid #00ffff',
            color: '#00ffff',
            fontSize: '11px',
            fontWeight: 'bold',
            textTransform: 'uppercase',
            fontFamily: 'monospace',
            textShadow: '0 0 5px rgba(0, 255, 255, 0.5)'
        });
        dropdown.appendChild(header);

        // Create options
        options.forEach(option => {
            const optionDiv = document.createElement('div');
            optionDiv.textContent = option.name;
            Object.assign(optionDiv.style, {
                padding: '14px 16px',
                color: '#ffffff',
                cursor: 'pointer',
                fontSize: '14px',
                transition: 'all 0.2s ease',
                fontFamily: 'inherit',
                borderLeft: '3px solid transparent'
            });

            optionDiv.addEventListener('mouseenter', () => {
                optionDiv.style.backgroundColor = 'rgba(0, 255, 255, 0.1)';
                optionDiv.style.borderLeftColor = '#00ffff';
                optionDiv.style.color = '#00ffff';
                optionDiv.style.textShadow = '0 0 5px rgba(0, 255, 255, 0.5)';
            });

            optionDiv.addEventListener('mouseleave', () => {
                optionDiv.style.backgroundColor = 'transparent';
                optionDiv.style.borderLeftColor = 'transparent';
                optionDiv.style.color = '#ffffff';
                optionDiv.style.textShadow = 'none';
            });

            optionDiv.addEventListener('click', (e) => {
                e.stopPropagation();
                console.log('🔄 Option clicked:', option.name, option.id);
                this.selectTaskSwap(slotId, option.id);
            });

            dropdown.appendChild(optionDiv);
        });

        // Create cancel option
        const cancelDiv = document.createElement('div');
        cancelDiv.textContent = 'Cancel';
        Object.assign(cancelDiv.style, {
            padding: '12px 16px',
            color: '#ff6b6b',
            cursor: 'pointer',
            fontSize: '14px',
            borderTop: '1px solid #333',
            marginTop: '4px',
            textAlign: 'center',
            fontWeight: 'bold',
            transition: 'all 0.2s ease'
        });

        cancelDiv.addEventListener('mouseenter', () => {
            cancelDiv.style.backgroundColor = 'rgba(255, 107, 107, 0.1)';
            cancelDiv.style.textShadow = '0 0 5px rgba(255, 107, 107, 0.5)';
        });

        cancelDiv.addEventListener('mouseleave', () => {
            cancelDiv.style.backgroundColor = 'transparent';
            cancelDiv.style.textShadow = 'none';
        });

        cancelDiv.addEventListener('click', (e) => {
            e.stopPropagation();
            this.closeAllDropdowns();
        });

        dropdown.appendChild(cancelDiv);

        // Position dropdown relative to the clicked element
        const rect = element.getBoundingClientRect();

        // Add to DOM first to get accurate measurements
        document.body.appendChild(dropdown);

        // Get dropdown dimensions after adding to DOM
        const dropdownRect = dropdown.getBoundingClientRect();
        const dropdownWidth = dropdownRect.width || 220; // fallback width
        const dropdownHeight = dropdownRect.height || 200; // fallback height

        // Position below and left-aligned with the task name
        let top = rect.bottom + 5;
        let left = rect.left;

        // Ensure dropdown stays within viewport bounds
        if (top + dropdownHeight > window.innerHeight) {
            // Show above if not enough space below
            top = rect.top - dropdownHeight - 5;
        }

        if (left + dropdownWidth > window.innerWidth) {
            // Move left if not enough space on right
            left = window.innerWidth - dropdownWidth - 10;
        }

        // Ensure it doesn't go off the left edge
        if (left < 10) {
            left = 10;
        }

        // Apply final positioning
        dropdown.style.top = `${top}px`;
        dropdown.style.left = `${left}px`;

        console.log('📍 Dropdown positioned at:', {
            top: dropdown.style.top,
            left: dropdown.style.left,
            rect: rect,
            elementText: element.textContent,
            elementPosition: element.getBoundingClientRect()
        });

        // Store reference (already added to DOM above)
        this.currentDropdown = dropdown;

        // Add click-outside-to-close functionality
        setTimeout(() => {
            const handleClickOutside = (event) => {
                if (!dropdown.contains(event.target) && !element.contains(event.target)) {
                    this.closeAllDropdowns();
                    document.removeEventListener('click', handleClickOutside);
                }
            };
            document.addEventListener('click', handleClickOutside);
        }, 100);

        // Add multiple visual indicators that dropdown is active
        this.showToast('🎯 Task swap menu opened - Check below task name!', 'info');

        // Add a temporary red border to the clicked element for debugging
        const originalBorder = element.style.border;
        element.style.border = '2px solid red';
        setTimeout(() => {
            element.style.border = originalBorder;
        }, 3000);

        console.log('✅ Dropdown added to DOM with the following properties:');
        console.log('   - ID:', dropdown.id);
        console.log('   - Position:', dropdown.style.position);
        console.log('   - Top:', dropdown.style.top);
        console.log('   - Left:', dropdown.style.left);
        console.log('   - Z-index:', dropdown.style.zIndex);
        console.log('   - Display:', dropdown.style.display);
        console.log('   - Parent:', dropdown.parentElement);
        console.log('   - Computed style:', window.getComputedStyle(dropdown));

        // Test if dropdown is actually visible in DOM
        setTimeout(() => {
            const foundDropdown = document.getElementById('task-swap-dropdown');
            console.log('🔍 Dropdown visibility check:');
            console.log('   - Found in DOM:', !!foundDropdown);
            if (foundDropdown) {
                const computedStyle = window.getComputedStyle(foundDropdown);
                console.log('   - Computed display:', computedStyle.display);
                console.log('   - Computed visibility:', computedStyle.visibility);
                console.log('   - Computed opacity:', computedStyle.opacity);
                console.log('   - Computed z-index:', computedStyle.zIndex);
                console.log('   - Bounding rect:', foundDropdown.getBoundingClientRect());
            }
        }, 100);
    }

    async selectTaskSwap(slotId, newActivityType) {
        try {
            this.closeAllDropdowns();

            // Find additional identifying information from the current schedule
            const taskElement = document.querySelector(`[data-slot-id="${slotId}"]`);
            let additionalInfo = {};

            if (taskElement) {
                // Extract time information from the element
                const timeElement = taskElement.querySelector('.text-sm');
                if (timeElement) {
                    const timeText = timeElement.textContent;
                    const timeMatch = timeText.match(/(\d{1,2}:\d{2})/);
                    if (timeMatch) {
                        additionalInfo.scheduledTime = timeMatch[1];
                    }
                }

                // Extract current activity type
                const activityElement = taskElement.querySelector('.font-bold');
                if (activityElement) {
                    additionalInfo.currentActivity = activityElement.textContent.trim();
                }
            }

            console.log('🔄 Swapping task with info:', {
                slotId,
                newActivityType,
                additionalInfo
            });

            const response = await fetch('/api/tasks/swap', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    oldTaskId: slotId,
                    newTaskId: newActivityType,
                    additionalInfo: additionalInfo
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showToast(data.message || 'Task swapped successfully', 'success');
                // Reload the schedule to show the updated task
                await this.loadSchedule();
            } else {
                // Check if schedule was auto-regenerated
                if (data.auto_regenerated) {
                    this.showToast(data.error || 'Schedule regenerated - please try again', 'warning');
                    // Reload the schedule to show the regenerated tasks
                    await this.loadSchedule();
                } else {
                    // Show error with solution if provided
                    const errorMsg = data.error || 'Failed to swap task';
                    const solutionMsg = data.solution ? `\n\nSolution: ${data.solution}` : '';
                    this.showToast(errorMsg + solutionMsg, 'error');
                }
            }
        } catch (error) {
            console.error('Error swapping task:', error);
            this.showToast('Error swapping task', 'error');
        }
    }

    closeAllDropdowns() {
        if (this.currentDropdown) {
            this.currentDropdown.remove();
            this.currentDropdown = null;
        }

        // Close any other dropdowns that might exist
        const existingSwapDropdowns = document.querySelectorAll('#task-swap-dropdown');
        existingSwapDropdowns.forEach(dropdown => dropdown.remove());

        const existingStatusDropdowns = document.querySelectorAll('#task-status-dropdown');
        existingStatusDropdowns.forEach(dropdown => dropdown.remove());
    }

    async updateTaskStatus(slotId, newStatus) {
        try {
            this.showToast(`Updating task status to ${newStatus}...`, 'info');

            const response = await fetch('/api/tasks/update-status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    slot_id: slotId,
                    status: newStatus
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.showToast(`Task status updated to ${newStatus}!`, 'success');

                // Update the task element immediately
                const taskElement = document.querySelector(`[data-slot-id="${slotId}"]`);
                if (taskElement) {
                    // Update status badge
                    const statusElement = taskElement.querySelector('.task-status');
                    if (statusElement) {
                        statusElement.textContent = newStatus;
                        statusElement.className = `task-status ${this.getStatusClass(newStatus)}`;
                    }

                    // Update the task appearance based on status
                    this.updateTaskAppearance(taskElement, newStatus);
                }

                // Reload the full schedule to ensure consistency
                await this.loadSchedule();
            } else {
                this.showToast(`Failed to update task status: ${data.error || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('Error updating task status:', error);
            this.showToast('Error updating task status', 'error');
        }
    }

    updateTaskAppearance(taskElement, status) {
        // Remove existing status classes
        taskElement.classList.remove('task-completed', 'task-failed', 'task-skipped', 'task-in-progress', 'task-scheduled');

        // Add new status class
        switch (status) {
            case 'completed':
                taskElement.classList.add('task-completed');
                break;
            case 'failed':
                taskElement.classList.add('task-failed');
                break;
            case 'skipped':
                taskElement.classList.add('task-skipped');
                break;
            case 'in_progress':
                taskElement.classList.add('task-in-progress');
                break;
            default:
                taskElement.classList.add('task-scheduled');
        }
    }

    getStatusClass(status) {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800 border-green-200';
            case 'failed':
                return 'bg-red-100 text-red-800 border-red-200';
            case 'skipped':
                return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'in_progress':
                return 'bg-blue-100 text-blue-800 border-blue-200';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    }

    showTaskStatusDropdown(slotId, element) {
        // Close any existing dropdowns
        this.closeAllDropdowns();

        const statuses = [
            { id: 'completed', name: '✅ Mark as Completed' },
            { id: 'skipped', name: '⏭️ Mark as Skipped' },
            { id: 'failed', name: '❌ Mark as Failed' },
            { id: 'scheduled', name: '📅 Reset to Scheduled' }
        ];

        // Create dropdown element
        const dropdown = document.createElement('div');
        dropdown.id = 'task-status-dropdown';

        Object.assign(dropdown.style, {
            position: 'fixed',
            backgroundColor: '#0f172a',
            border: '2px solid #fbbf24',
            borderRadius: '8px',
            boxShadow: '0 0 30px rgba(251, 191, 36, 0.5), 0 10px 25px rgba(0, 0, 0, 0.8)',
            zIndex: '99999',
            minWidth: '200px',
            maxHeight: '300px',
            overflowY: 'auto',
            padding: '8px 0',
            display: 'block',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            animation: 'fadeIn 0.2s ease-out'
        });

        // Create header
        const header = document.createElement('div');
        header.textContent = 'UPDATE STATUS:';
        Object.assign(header.style, {
            padding: '10px 16px',
            borderBottom: '1px solid #fbbf24',
            color: '#fbbf24',
            fontSize: '11px',
            fontWeight: 'bold',
            textTransform: 'uppercase',
            fontFamily: 'monospace',
            textShadow: '0 0 5px rgba(251, 191, 36, 0.5)'
        });
        dropdown.appendChild(header);

        // Create status options
        statuses.forEach(status => {
            const optionDiv = document.createElement('div');
            optionDiv.textContent = status.name;
            Object.assign(optionDiv.style, {
                padding: '14px 16px',
                color: '#ffffff',
                cursor: 'pointer',
                fontSize: '14px',
                transition: 'all 0.2s ease',
                fontFamily: 'inherit',
                borderLeft: '3px solid transparent'
            });

            optionDiv.addEventListener('mouseenter', () => {
                optionDiv.style.backgroundColor = 'rgba(251, 191, 36, 0.1)';
                optionDiv.style.borderLeftColor = '#fbbf24';
                optionDiv.style.color = '#fbbf24';
                optionDiv.style.textShadow = '0 0 5px rgba(251, 191, 36, 0.5)';
            });

            optionDiv.addEventListener('mouseleave', () => {
                optionDiv.style.backgroundColor = 'transparent';
                optionDiv.style.borderLeftColor = 'transparent';
                optionDiv.style.color = '#ffffff';
                optionDiv.style.textShadow = 'none';
            });

            optionDiv.addEventListener('click', (e) => {
                e.stopPropagation();
                this.updateTaskStatus(slotId, status.id);
                this.closeAllDropdowns();
            });

            dropdown.appendChild(optionDiv);
        });

        // Create cancel option
        const cancelDiv = document.createElement('div');
        cancelDiv.textContent = 'Cancel';
        Object.assign(cancelDiv.style, {
            padding: '12px 16px',
            color: '#ff6b6b',
            cursor: 'pointer',
            fontSize: '14px',
            borderTop: '1px solid #333',
            marginTop: '4px',
            textAlign: 'center',
            fontWeight: 'bold',
            transition: 'all 0.2s ease'
        });

        cancelDiv.addEventListener('click', (e) => {
            e.stopPropagation();
            this.closeAllDropdowns();
        });

        dropdown.appendChild(cancelDiv);

        // Position dropdown relative to the status button
        const rect = element.getBoundingClientRect();

        // Add to DOM first to get accurate measurements
        document.body.appendChild(dropdown);

        // Get dropdown dimensions after adding to DOM
        const dropdownRect = dropdown.getBoundingClientRect();
        const dropdownWidth = dropdownRect.width || 200; // fallback width
        const dropdownHeight = dropdownRect.height || 200; // fallback height

        // Position below and right-aligned with the status button (extending inward)
        let top = rect.bottom + 5;
        let left = rect.right - dropdownWidth; // Right-align with status button

        // Ensure dropdown stays within viewport bounds
        if (top + dropdownHeight > window.innerHeight) {
            // Show above if not enough space below
            top = rect.top - dropdownHeight - 5;
        }

        // Ensure it doesn't go off the left edge
        if (left < 10) {
            left = 10;
        }

        // Ensure it doesn't go off the right edge
        if (left + dropdownWidth > window.innerWidth) {
            left = window.innerWidth - dropdownWidth - 10;
        }

        // Apply final positioning
        dropdown.style.top = `${top}px`;
        dropdown.style.left = `${left}px`;

        // Store reference (already added to DOM above)
        this.currentDropdown = dropdown;

        // Add click-outside-to-close functionality
        setTimeout(() => {
            const handleClickOutside = (event) => {
                if (!dropdown.contains(event.target) && !element.contains(event.target)) {
                    this.closeAllDropdowns();
                    document.removeEventListener('click', handleClickOutside);
                }
            };
            document.addEventListener('click', handleClickOutside);
        }, 100);
    }
}

// Date picker & range controls
(function scheduleDateControls() {
    function formatDateInput(d) {
        return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().split('T')[0];
    }
    function setPickerTo(dateStr) {
        const picker = document.getElementById('schedule-date-picker');
        if (picker) picker.value = dateStr;
    }
    document.addEventListener('DOMContentLoaded', () => {
        const picker = document.getElementById('schedule-date-picker');
        const todayBtn = document.getElementById('today-btn');
        const loadRangeBtn = document.getElementById('load-range-btn');
        const prev = document.getElementById('prev-day');
        const next = document.getElementById('next-day');
        const start = document.getElementById('range-start');
        const end = document.getElementById('range-end');
        // Initialize picker to today
        const todayStr = formatDateInput(new Date());
        setPickerTo(todayStr);
        if (typeof dashboard !== 'undefined') {
            dashboard.currentDate = todayStr;
            // Force load with explicit ?date param to avoid stale data
            dashboard.loadSchedule(todayStr, true);
            /* Label removed */
        }
        // Handlers
        if (picker) {
            picker.addEventListener('change', (e) => {
                const value = e.target.value;
                if (value && typeof dashboard !== 'undefined') {
                    const norm = formatDateInput(new Date(value + 'T00:00:00'));
                    dashboard.currentDate = norm;
                    setPickerTo(norm);
                    dashboard.loadSchedule(norm);
                    /* Label removed */
                }
            });
        }
        if (todayBtn) {
            todayBtn.addEventListener('click', () => {
                const t = formatDateInput(new Date());
                setPickerTo(t);
                if (typeof dashboard !== 'undefined') {
                    dashboard.currentDate = t;
                    // Also set currentDate on the instance explicitly
                    window.dashboard.currentDate = t;
                    dashboard.loadSchedule(t, true);
                }
            });
        }
        if (prev) {
            prev.addEventListener('click', () => {
                const base = picker && picker.value ? new Date(picker.value + 'T00:00:00') : new Date();
                base.setDate(base.getDate() - 1);
                const v = formatDateInput(base);
                setPickerTo(v);
                if (typeof dashboard !== 'undefined') {
                    dashboard.currentDate = v;
                    dashboard.loadSchedule(v);
                    /* Label removed */
                }
            });
        }
        if (next) {
            next.addEventListener('click', () => {
                const base = picker && picker.value ? new Date(picker.value + 'T00:00:00') : new Date();
                base.setDate(base.getDate() + 1);
                const v = formatDateInput(base);
                setPickerTo(v);
                if (typeof dashboard !== 'undefined') {
                    dashboard.currentDate = v;
                    dashboard.loadSchedule(v);
                    /* Label removed */
                }
            });
        }
        if (loadRangeBtn) {
            loadRangeBtn.addEventListener('click', async () => {
                if (!start || !end || !start.value || !end.value) return;
                try {
                    // Client-side aggregation of /api/schedule for each date
                    const startDate = new Date(start.value + 'T00:00:00');
                    const endDate = new Date(end.value + 'T00:00:00');
                    if (isNaN(startDate) || isNaN(endDate) || startDate > endDate) return;

                    const days = [];
                    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
                        days.push(new Date(d));
                    }
                    const toYmd = (d) => d.toISOString().split('T')[0];
                    const results = await Promise.all(days.map(async (d) => {
                        const ymd = toYmd(new Date(d.getTime() - d.getTimezoneOffset() * 60000));
                        const r = await fetch(`/api/schedule?date=${ymd}`);
                        const j = await r.json();
                        return r.ok ? (j.slots || []).map(s => ({ ...s })) : [];
                    }));
                    const combined = results.flat().sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
                    if (typeof dashboard !== 'undefined') {
                        // Update view with range and set the currentDate to the start of range for consistency
                        dashboard.currentDate = start.value;
                        dashboard.updateScheduleDisplay({ date: start.value, slots: combined });
                    }
                    // Close the dropdown after loading
                    const panel = document.getElementById('range-panel');
                    if (panel) panel.classList.add('hidden');
                } catch (err) {
                    console.error('Error loading range', err);
                }
            });
        }
    });
})();

// Range dropdown toggle and date normalization
(function scheduleEnhancements() {
    const onReady = (fn) => (document.readyState === 'loading') ? document.addEventListener('DOMContentLoaded', fn) : fn();
    const toLocalYMD = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().split('T')[0];
    onReady(() => {
        const picker = document.getElementById('schedule-date-picker');
        const scheduleDate = null;
        // Normalize picker value when user edits it
        if (picker) {
            picker.addEventListener('change', () => {
                if (!picker.value) return;
                const d = new Date(picker.value + 'T00:00:00');
                const norm = toLocalYMD(d);
                if (picker.value !== norm) picker.value = norm;
                if (scheduleDate) scheduleDate.textContent = new Date(norm + 'T00:00:00').toLocaleDateString();
            });
        }
        // Range dropdown
        const toggle = document.getElementById('range-toggle');
        const panel = document.getElementById('range-panel');
        const cancel = document.getElementById('range-cancel');
        if (toggle && panel) {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                panel.classList.toggle('hidden');
            });
            if (cancel) cancel.addEventListener('click', () => panel.classList.add('hidden'));
            document.addEventListener('click', (e) => {
                if (!panel.contains(e.target) && e.target !== toggle) panel.classList.add('hidden');
            });
        }
    });
})();


// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new TwitterAgentDashboard();
    // Sync picker with dashboard and force-load today's schedule
    try {
        const tzFix = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().split('T')[0];
        const picker = document.getElementById('schedule-date-picker');
        const todayStr = tzFix(new Date());
        if (picker) {
            if (!picker.value) picker.value = todayStr;
            const selected = picker.value || todayStr;
            window.dashboard.currentDate = selected;
            window.dashboard.loadSchedule(selected, true);
        } else {
            // No picker found; still ensure schedule loads
            window.dashboard.currentDate = todayStr;
            window.dashboard.loadSchedule(todayStr, true);
        }
    } catch (e) {
        console.warn('Schedule bootstrap failed', e);
    }
});
