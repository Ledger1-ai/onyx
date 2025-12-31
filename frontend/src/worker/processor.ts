import { IJobAdapter } from './types/IJobAdapter';
import { scrapeTwitter, postTweet, interact, follow, scrapeMentions } from './scrapers/twitter';
import { postFacebook, postInstagram } from './scrapers/meta_api';
import { LinkedInBrowser } from './workers/linkedin_browser';
import { logger } from './utils/logger';

// Singleton instance for LinkedIn Browser
const linkedin = new LinkedInBrowser();
let linkedinInitialized = false;

async function getLinkedIn() {
    if (!linkedinInitialized) {
        await linkedin.init();
        linkedinInitialized = true;
    }
    return linkedin;
}

export async function processJob(job: IJobAdapter) {
    logger.info(`Processing job ${job.id} of type ${job.name}`);

    switch (job.name) {
        // --- Twitter ---
        case 'twitter-scrape':
            return await scrapeTwitter(job);
        case 'twitter:post':
            return await postTweet(job);
        case 'twitter:interact':
            return await interact(job);
        case 'twitter:follow':
            return await follow(job);
        case 'twitter:scan-mentions':
            return await scrapeMentions(job);

        // --- Meta (API) ---
        case 'meta:facebook-post':
            return await postFacebook(job);
        case 'meta:instagram-post':
            return await postInstagram(job);

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
            logger.warn('Search not fully implemented in browser worker yet');
            return true;
        case 'linkedin:scan-notifications':
            logger.warn('Notifications scan not implemented in browser worker yet');
            return true;
        case 'linkedin:analytics':
            logger.warn('Analytics scan not implemented in browser worker yet');
            return true;

        case 'test-job':
            logger.info('Test job executed');
            return { success: true, message: 'Test passed' };
        case 'start-agent':
            logger.info('Received Start Agent signal. Dispatcher is now active.');
            return { success: true, message: 'Agent started' };

        default:
            throw new Error(`Unknown job name: ${job.name}`);
    }
}
