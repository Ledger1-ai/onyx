"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.processJob = processJob;
const twitter_1 = require("./scrapers/twitter");
const logger_1 = require("./utils/logger");
async function processJob(job) {
    logger_1.logger.info(`Processing job ${job.id} of type ${job.name}`);
    switch (job.name) {
        case 'twitter-scrape':
            return await (0, twitter_1.scrapeTwitter)(job);
        case 'twitter:post':
            return await (0, twitter_1.postTweet)(job);
        case 'twitter:interact':
            return await (0, twitter_1.interact)(job);
        case 'twitter:follow':
            return await (0, twitter_1.follow)(job);
        case 'twitter:scan-mentions':
            return await (0, twitter_1.scrapeMentions)(job);
        case 'test-job':
            logger_1.logger.info('Test job executed');
            return { success: true, message: 'Test passed' };
        default:
            throw new Error(`Unknown job name: ${job.name}`);
    }
}
