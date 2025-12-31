"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.processJob = processJob;
const twitter_1 = require("./scrapers/twitter");
const meta_api_1 = require("./scrapers/meta_api");
const linkedin_browser_1 = require("./workers/linkedin_browser");
const logger_1 = require("./utils/logger");
// Singleton instance for LinkedIn Browser
const linkedin = new linkedin_browser_1.LinkedInBrowser();
let linkedinInitialized = false;
async function getLinkedIn() {
    if (!linkedinInitialized) {
        await linkedin.init();
        linkedinInitialized = true;
    }
    return linkedin;
}
async function processJob(job) {
    logger_1.logger.info(`Processing job ${job.id} of type ${job.name}`);
    switch (job.name) {
        // --- Twitter ---
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
        // --- Meta (API) ---
        case 'meta:facebook-post':
            return await (0, meta_api_1.postFacebook)(job);
        case 'meta:instagram-post':
            return await (0, meta_api_1.postInstagram)(job);
        // --- LinkedIn ---
        case 'linkedin:post': {
            const browser = await getLinkedIn();
            const { content, mediaPath } = job.data;
            return await browser.postContent(content, mediaPath);
        }
        case 'linkedin:engage': {
            const browser = await getLinkedIn();
            const { count } = job.data;
            return await browser.engageFeed(count || 5);
        }
        // Placeholder handling for search/notifications until mapped in Browser
        case 'linkedin:search':
            logger_1.logger.warn('Search not fully implemented in browser worker yet');
            return true;
        case 'linkedin:scan-notifications':
            logger_1.logger.warn('Notifications scan not implemented in browser worker yet');
            return true;
        case 'linkedin:analytics':
            logger_1.logger.warn('Analytics scan not implemented in browser worker yet');
            return true;
        case 'test-job':
            logger_1.logger.info('Test job executed');
            return { success: true, message: 'Test passed' };
        default:
            throw new Error(`Unknown job name: ${job.name}`);
    }
}
