import dotenv from 'dotenv';
import { Express } from 'express';
import { connectDB } from '../lib/db';
import Job from '../models/Job';
import { processJob } from './processor';
// import { Scheduler } from './scheduler'; // Will refactor next
import { logger } from './utils/logger';

dotenv.config();

const POLL_INTERVAL_MS = 5000;
let isRunning = false;
let pollingInterval: NodeJS.Timeout | null = null;

async function pollQueue() {
    if (isRunning) return;
    isRunning = true;

    try {
        // Find and lock the oldest pending job
        // atomic update: find pending -> set processing
        const job = await Job.findOneAndUpdate(
            { status: 'pending' },
            { status: 'processing', processedAt: new Date() },
            { sort: { createdAt: 1 }, new: true }
        );

        if (job) {
            logger.info(`Processing job ${job._id} of type ${job.type}`);

            try {
                // Adapt to processor interface (which expects a BullMQ job structure with .name and .data)
                const jobAdapter: any = {
                    id: job._id.toString(),
                    name: job.type,
                    data: job.data,
                    log: (msg: string) => logger.info(`[Job ${job._id}] ${msg}`)
                };

                const result = await processJob(jobAdapter);

                await Job.updateOne(
                    { _id: job._id },
                    { status: 'completed', result: result }
                );
                logger.info(`Job ${job._id} completed!`);

                // If we found a job, check again immediately instead of waiting full interval
                isRunning = false;
                setImmediate(pollQueue);
                return;

            } catch (err: any) {
                logger.error(`Job ${job._id} failed: ${err.message}`);
                await Job.updateOne(
                    { _id: job._id },
                    { status: 'failed', error: err.message }
                );
            }
        }
    } catch (error) {
        logger.error('Error polling queue:', error);
    } finally {
        isRunning = false;
    }
}

export async function startWorker(app?: Express) {
    logger.info('Initializing MongoDB Worker...');

    // Connect to DB
    await connectDB();

    // Start Polling Loop
    logger.info(`Starting polling loop (${POLL_INTERVAL_MS}ms interval)...`);

    // Initial poll
    pollQueue();

    // Set interval
    pollingInterval = setInterval(pollQueue, POLL_INTERVAL_MS);

    // Initialize Scheduler (Temporarily disabled until refactored)
    // const scheduler = new Scheduler(); 
    // scheduler.start();

    if (app) {
        // Simple Admin Dashboard Route (replaces BullBoard)
        app.get('/admin/queues', async (req, res) => {
            try {
                const stats = {
                    pending: await Job.countDocuments({ status: 'pending' }),
                    processing: await Job.countDocuments({ status: 'processing' }),
                    completed: await Job.countDocuments({ status: 'completed' }),
                    failed: await Job.countDocuments({ status: 'failed' }),
                };

                const recentFailures = await Job.find({ status: 'failed' })
                    .sort({ updatedAt: -1 })
                    .limit(5);

                const recentCompleted = await Job.find({ status: 'completed' })
                    .sort({ updatedAt: -1 })
                    .limit(5);

                res.send(`
                    <html>
                        <head><title>Job Queue Dashboard</title></head>
                        <body style="font-family: sans-serif; padding: 2rem;">
                            <h1>Job Queue Status</h1>
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
                                <div style="background: #eee; padding: 1rem; border-radius: 8px;">Pending: <b>${stats.pending}</b></div>
                                <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px;">Processing: <b>${stats.processing}</b></div>
                                <div style="background: #e8f5e9; padding: 1rem; border-radius: 8px;">Completed: <b>${stats.completed}</b></div>
                                <div style="background: #ffebee; padding: 1rem; border-radius: 8px;">Failed: <b>${stats.failed}</b></div>
                            </div>
                            
                            <h3>Recent Failures</h3>
                            <pre>${JSON.stringify(recentFailures, null, 2)}</pre>
                            
                            <h3>Recent Completed</h3>
                            <pre>${JSON.stringify(recentCompleted, null, 2)}</pre>
                        </body>
                    </html>
                `);
            } catch (e) {
                res.status(500).send('Error loading stats');
            }
        });
        logger.info('Legacy BullBoard replaced with /admin/queues stats page');
    }

    return { pollingInterval };
}
