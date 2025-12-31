import { logger } from './utils/logger';
// import Job from '../models/Job'; 

export class Scheduler {
    private isRunning: boolean = false;
    private checkInterval: NodeJS.Timeout | null = null;

    constructor() { }

    start() {
        if (this.isRunning) return;
        this.isRunning = true;

        logger.info('Starting Schedule Dispatcher (MongoDB Mode)...');

        // Check schedule every minute
        this.checkInterval = setInterval(() => this.checkSchedule(), 60000);
    }

    stop() {
        if (this.checkInterval) clearInterval(this.checkInterval);
        this.isRunning = false;
    }

    private async checkSchedule() {
        try {
            // Placeholder: logic to find due tasks from DB would go here
            // For now, we rely on manual commands or other triggers
        } catch (error) {
            logger.error('Error checking schedule:', error);
        }
    }
}
