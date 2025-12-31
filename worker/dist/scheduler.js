"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Scheduler = void 0;
const logger_1 = require("./utils/logger");
class Scheduler {
    constructor(redis, queue) {
        this.timer = null;
        this.isRunning = false;
        this.redis = redis;
        this.queue = queue;
    }
    start() {
        if (this.isRunning)
            return;
        this.isRunning = true;
        logger_1.logger.info('Starting Schedule Dispatcher...');
        // Run immediately, then every 60s
        this.checkSchedule();
        this.timer = setInterval(() => this.checkSchedule(), 60000);
    }
    stop() {
        if (this.timer)
            clearInterval(this.timer);
        this.isRunning = false;
        logger_1.logger.info('Stopping Schedule Dispatcher...');
    }
    async checkSchedule() {
        try {
            const scheduleJson = await this.redis.get('schedule:daily_plan');
            const isActive = await this.redis.get('dispatcher:active');
            if (isActive !== 'true') {
                // logger.debug('Dispatcher execution skipped (System Paused)');
                // Optional: We could log this if we want verbose logs, but it might spam every minute.
                // Better to remain silent or log only on state change if possible.
                return;
            }
            if (!scheduleJson)
                return;
            const schedule = JSON.parse(scheduleJson);
            const now = new Date();
            let hasChanges = false;
            for (const slot of schedule.slots) {
                const startTime = new Date(slot.start_time);
                const endTime = new Date(slot.end_time);
                // Check if task is due (start_time <= now <= end_time) AND status is 'pending'
                // We add a small buffer (e.g., if we are within 5 mins past start time, assume it's valid to start)
                if (slot.status === 'pending' && now >= startTime && now <= endTime) {
                    logger_1.logger.info(`Dispatching task: ${slot.activity_type} (Slot: ${slot.slot_id})`);
                    // 1. Map Activity Type to Job Name
                    const jobName = this.mapActivityToJob(slot.activity_type);
                    if (jobName) {
                        // 2. Add to Queue
                        await this.queue.add(jobName, {
                            slotId: slot.slot_id,
                            activityType: slot.activity_type,
                            timestamp: new Date().toISOString()
                        }, {
                            priority: slot.priority,
                            jobId: slot.slot_id // Prevent duplicates using slot_id as job ID
                        });
                        // 3. Update Status
                        slot.status = 'in_progress';
                        hasChanges = true;
                    }
                    else {
                        logger_1.logger.warn(`No job mapping found for activity: ${slot.activity_type}`);
                    }
                }
            }
            // 4. Save updated schedule back to Redis if we dispatched anything
            if (hasChanges) {
                await this.redis.set('schedule:daily_plan', JSON.stringify(schedule));
            }
        }
        catch (error) {
            logger_1.logger.error('Scheduler check failed:', error);
        }
    }
    mapActivityToJob(activityType) {
        switch (activityType) {
            case 'TWITTER_TWEET': return 'twitter:post';
            case 'TWITTER_REPLY': return 'twitter:scan-mentions'; // Logic usually scans then replies
            case 'TWITTER_ENGAGE': return 'twitter:interact'; // Generalized interaction
            case 'TWITTER_FOLLOW': return 'twitter:follow';
            case 'TWITTER_TRENDS': return 'twitter-scrape'; // General scrape/monitor
            // LinkedIn Mappings
            case 'LINKEDIN_ARTICLE': return 'linkedin:post';
            case 'LINKEDIN_POST': return 'linkedin:post';
            case 'LINKEDIN_CONNECT': return 'linkedin:search'; // Connect implies searching people
            case 'LINKEDIN_ENGAGE': return 'linkedin:engage';
            case 'LINKEDIN_CHECK': return 'linkedin:scan-notifications';
            case 'SYSTEM_CHECK': return 'test-job'; // Mapping system check to test/health job
            default: return null;
        }
    }
}
exports.Scheduler = Scheduler;
