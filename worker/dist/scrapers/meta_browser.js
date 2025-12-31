"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.watchStories = watchStories;
exports.watchReels = watchReels;
const logger_1 = require("../utils/logger");
// We reuse the existing browser context passed from processor (if available) 
// or we launch one if the processor structure supports it. 
// Assuming processor.ts manages the browser/page lifecycle and passes `job.data.page` or we handle it here.
// NOTE: In the current architecture, processor.ts typically passes the job. 
// We might need to adjust processor.ts to pass the browser page if it's a browser job.
async function watchStories(page, platform) {
    logger_1.logger.info(`[Meta Browser] Watching ${platform} Stories...`);
    const url = platform === 'facebook'
        ? 'https://www.facebook.com/stories'
        : 'https://www.instagram.com/stories';
    try {
        await page.goto(url, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(5000); // Wait for load
        // Verify login state
        const title = await page.title();
        if (title.includes('Log In') || title.includes('Welcome')) {
            throw new Error(`Not logged into ${platform}`);
        }
        // Logic: Just "viewing" is often enough for "Active Status"
        // Legacy app took a screenshot.
        await page.screenshot({ path: `screenshots/${platform}_stories_${Date.now()}.png` });
        // Emulate some viewing time
        await page.waitForTimeout(10000); // 10s of "watching"
        logger_1.logger.info(`[Meta Browser] Successfully watched ${platform} stories.`);
        return { success: true, message: `Watched ${platform} stories`, screenshot: true };
    }
    catch (error) {
        logger_1.logger.error(`[Meta Browser] Error watching stories: ${error.message}`);
        throw error;
    }
}
async function watchReels(page, platform) {
    logger_1.logger.info(`[Meta Browser] Watching ${platform} Reels...`);
    // Facebook Reels: https://www.facebook.com/reel
    // Instagram Reels: https://www.instagram.com/reels
    const url = platform === 'facebook'
        ? 'https://www.facebook.com/reel'
        : 'https://www.instagram.com/reels';
    try {
        await page.goto(url, { waitUntil: 'networkidle' });
        await page.waitForTimeout(5000);
        // Simple scroll to simulate watching multiple reels
        for (let i = 0; i < 5; i++) {
            await page.mouse.wheel(0, 500);
            await page.waitForTimeout(3000 + Math.random() * 2000); // 3-5s per reel
        }
        await page.screenshot({ path: `screenshots/${platform}_reels_${Date.now()}.png` });
        logger_1.logger.info(`[Meta Browser] Successfully watched ${platform} reels.`);
        return { success: true, message: `Watched ${platform} reels`, screenshot: true };
    }
    catch (error) {
        logger_1.logger.error(`[Meta Browser] Error watching reels: ${error.message}`);
        throw error;
    }
}
