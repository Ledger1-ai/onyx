import dotenv from 'dotenv';
import { Queue, Worker, RedisConnection } from 'bullmq';
import IORedis from 'ioredis';
import express from 'express';
import { createBullBoard } from '@bull-board/api';
import { BullMQAdapter } from '@bull-board/api/bullMQAdapter';
import { ExpressAdapter } from '@bull-board/express';
import { processJob } from './processor';
import { Scheduler } from './scheduler';
import { logger } from './utils/logger';

dotenv.config();

const redisConnection = new IORedis(process.env.REDIS_URL || 'redis://localhost:6379', {
    maxRetriesPerRequest: null,
});

const QUEUE_NAME = 'anubis-tasks';
const jobQueue = new Queue(QUEUE_NAME, { connection: redisConnection });

const worker = new Worker(QUEUE_NAME, processJob, {
    connection: redisConnection,
    concurrency: 5,
    limiter: {
        max: 10,
        duration: 1000,
    },
});

worker.on('completed', (job) => {
    logger.info(`Job ${job.id} completed!`);
});

worker.on('failed', (job, err) => {
    logger.error(`Job ${job?.id} failed: ${err.message}`);
});

// Initialize Scheduler
const scheduler = new Scheduler(redisConnection, jobQueue);
scheduler.start();

const app = express();
const serverAdapter = new ExpressAdapter();
serverAdapter.setBasePath('/admin/queues');

createBullBoard({
    queues: [new BullMQAdapter(jobQueue) as any],
    serverAdapter: serverAdapter,
});

app.use('/admin/queues', serverAdapter.getRouter());

const PORT = 3001;
app.listen(PORT, () => {
    logger.info(`Dashboard running on http://localhost:${PORT}/admin/queues`);
    logger.info(`Worker listening for jobs in queue: ${QUEUE_NAME}...`);

    // Heartbeat Loop
    setInterval(async () => {
        try {
            await redisConnection.set('worker:heartbeat', Date.now());
        } catch (e) {
            logger.error('Failed to send heartbeat');
        }
    }, 10000);
});

// Graceful Shutdown
process.on('SIGTERM', async () => {
    logger.info('SIGTERM signal received: closing worker');
    await worker.close();
    process.exit(0);
});
