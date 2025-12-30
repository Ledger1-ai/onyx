"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const bullmq_1 = require("bullmq");
const ioredis_1 = __importDefault(require("ioredis"));
const express_1 = __importDefault(require("express"));
const api_1 = require("@bull-board/api");
const bullMQAdapter_1 = require("@bull-board/api/bullMQAdapter");
const express_2 = require("@bull-board/express");
const dotenv_1 = __importDefault(require("dotenv"));
const processor_1 = require("./processor");
const logger_1 = require("./utils/logger");
dotenv_1.default.config();
const REDIS_HOST = process.env.REDIS_HOST || 'localhost';
const REDIS_PORT = parseInt(process.env.REDIS_PORT || '6379');
const redisConnection = new ioredis_1.default({
    host: REDIS_HOST,
    port: REDIS_PORT,
    maxRetriesPerRequest: null,
});
const QUEUE_NAME = 'anubis-tasks';
// Create Worker
const worker = new bullmq_1.Worker(QUEUE_NAME, processor_1.processJob, {
    connection: redisConnection,
    concurrency: 5, // Adjust based on RAM/CPU (Playwright is heavy)
    limiter: {
        max: 10,
        duration: 1000,
    }
});
worker.on('completed', (job) => {
    logger_1.logger.info(`Job ${job.id} completed!`);
});
worker.on('failed', (job, err) => {
    logger_1.logger.error(`Job ${job?.id} failed: ${err.message}`);
});
// -- Monitoring (BullBoard) --
const app = (0, express_1.default)();
const serverAdapter = new express_2.ExpressAdapter();
serverAdapter.setBasePath('/admin/queues');
const jobQueue = new bullmq_1.Queue(QUEUE_NAME, { connection: redisConnection });
(0, api_1.createBullBoard)({
    queues: [new bullMQAdapter_1.BullMQAdapter(jobQueue)],
    serverAdapter: serverAdapter,
});
app.use('/admin/queues', serverAdapter.getRouter());
const PORT = 3001;
app.listen(PORT, () => {
    logger_1.logger.info(`Dashboard running on http://localhost:${PORT}/admin/queues`);
    logger_1.logger.info(`Worker listening for jobs in queue: ${QUEUE_NAME}...`);
    // Heartbeat Loop
    setInterval(async () => {
        try {
            await redisConnection.set('worker:heartbeat', Date.now());
        }
        catch (e) {
            logger_1.logger.error('Failed to send heartbeat');
        }
    }, 10000);
});
// Graceful Shutdown
process.on('SIGTERM', async () => {
    logger_1.logger.info('SIGTERM signal received: closing worker');
    await worker.close();
    process.exit(0);
});
