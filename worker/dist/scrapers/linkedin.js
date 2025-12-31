"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.postContent = postContent;
exports.engageFeed = engageFeed;
exports.searchAndEngage = searchAndEngage;
exports.scrapeNotifications = scrapeNotifications;
exports.scrapeAnalytics = scrapeAnalytics;
const playwright_extra_1 = require("playwright-extra");
const puppeteer_extra_plugin_stealth_1 = __importDefault(require("puppeteer-extra-plugin-stealth"));
const logger_1 = require("../utils/logger");
const path_1 = __importDefault(require("path"));
const fs_1 = __importDefault(require("fs"));
// @ts-ignore - stealth plugin types issue
playwright_extra_1.chromium.use((0, puppeteer_extra_plugin_stealth_1.default)());
const USER_DATA_DIR = path_1.default.resolve(process.cwd(), '../browser_profiles/linkedin_automation_profile');
/**
 * Launch a persistent browser context to maintain login sessions.
 */
async function getContext() {
    if (!fs_1.default.existsSync(USER_DATA_DIR)) {
        logger_1.logger.info(`Creating new browser profile directory: ${USER_DATA_DIR}`);
        fs_1.default.mkdirSync(USER_DATA_DIR, { recursive: true });
    }
    const browser = await playwright_extra_1.chromium.launchPersistentContext(USER_DATA_DIR, {
        headless: false, // Initial testing usually better with head
        viewport: { width: 1920, height: 1080 },
        args: [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu', // VDI/Server compat
        ],
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });
    return browser;
}
// Helper: Random Delay
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
const randomDelay = (min = 2000, max = 5000) => delay(Math.floor(Math.random() * (max - min + 1) + min));
// Helper: Check Login
async function checkLogin(page) {
    try {
        await page.goto('https://www.linkedin.com/feed/');
        await randomDelay(3000, 5000);
        // Check for common feed elements
        const isLoggedIn = await page.evaluate(() => {
            return !!document.querySelector('#global-nav-typeahead') ||
                !!document.querySelector('.global-nav__me-photo') ||
                !!document.querySelector('div.feed-identity-module');
        });
        return isLoggedIn;
    }
    catch (e) {
        return false;
    }
}
/**
 * JOB: LinkedIn Post
 * Data: { text: string, mediaPath?: string }
 */
async function postContent(job) {
    const { text, mediaPath } = job.data;
    const context = await getContext();
    const page = await context.newPage();
    try {
        if (!await checkLogin(page)) {
            logger_1.logger.error(`[${job.id}] Not logged in to LinkedIn`);
            return { success: false, error: 'Not logged in' };
        }
        logger_1.logger.info(`[${job.id}] Starting LinkedIn Post`);
        await page.goto('https://www.linkedin.com/feed/');
        await randomDelay();
        // 1. Click "Start a post"
        // Try multiple selectors
        const startBtn = page.getByText('Start a post', { exact: false }).first();
        if (await startBtn.isVisible()) {
            await startBtn.click();
        }
        else {
            // Fallback
            await page.click('button.share-box-feed-entry__trigger');
        }
        await randomDelay(2000, 3000);
        // 2. Handle Media (if any)
        if (mediaPath) {
            try {
                logger_1.logger.info(`[${job.id}] Uploading media: ${mediaPath}`);
                // In Playwright, we handle file chooser or input
                // LinkedIn often hides the input. We can use setInputFiles if we find the input.
                // Or click the "Media" button then handle chooser.
                // Strategy: Find hidden file input
                const fileInput = page.locator('input[type="file"]');
                await fileInput.setInputFiles(mediaPath);
                await randomDelay(5000, 8000); // Wait for upload
                // Check for "Done" button in image editor modal
                const doneBtn = page.getByText('Done').first();
                if (await doneBtn.isVisible()) {
                    await doneBtn.click();
                    await randomDelay(1000, 2000);
                }
            }
            catch (e) {
                logger_1.logger.warn(`[${job.id}] Media upload potentially failed: ${e}`);
            }
        }
        // 3. Type Text
        // Editor typically has role 'textbox'
        const editor = page.getByRole('textbox').first();
        await editor.click();
        await editor.fill(text);
        await randomDelay(2000, 3000);
        // 4. Click Post
        const postBtn = page.getByRole('button', { name: 'Post', exact: true }).filter({ hasText: 'Post' }).first();
        if (await postBtn.isEnabled()) {
            await postBtn.click();
            await randomDelay(3000, 5000);
            logger_1.logger.info(`[${job.id}] LinkedIn Post Success`);
            return { success: true, message: 'Posted successfully' };
        }
        else {
            throw new Error('Post button disabled');
        }
    }
    catch (error) {
        logger_1.logger.error(`[${job.id}] LinkedIn Post Failed: ${error.message}`);
        throw error;
    }
    finally {
        await context.close();
    }
}
/**
 * JOB: Engage Feed
 * Data: { count: number }
 */
async function engageFeed(job) {
    const count = job.data.count || 5;
    const context = await getContext();
    const page = await context.newPage();
    try {
        if (!await checkLogin(page))
            return { success: false, error: 'Not logged in' };
        logger_1.logger.info(`[${job.id}] Engaging with ${count} posts on feed`);
        await page.goto('https://www.linkedin.com/feed/');
        await randomDelay();
        let actions = 0;
        let scrolls = 0;
        while (actions < count && scrolls < 10) {
            // Scroll
            await page.mouse.wheel(0, 500);
            await randomDelay(1000, 2000);
            scrolls++;
            // Find Like buttons
            // aria-label="React Like..." and NOT "Undo Like"
            const likeButtons = await page.locator('button[aria-label*="Like"]:not([aria-label*="Undo"])').all();
            for (const btn of likeButtons) {
                if (actions >= count)
                    break;
                if (await btn.isVisible() && Math.random() > 0.4) {
                    await btn.click();
                    actions++;
                    logger_1.logger.info(`[${job.id}] Liked a post (${actions}/${count})`);
                    await randomDelay(2000, 5000);
                }
            }
        }
        return { success: true, actionsPerformed: actions };
    }
    catch (error) {
        logger_1.logger.error(`[${job.id}] Feed Engagement Failed: ${error.message}`);
        throw error;
    }
    finally {
        await context.close();
    }
}
/**
 * JOB: Search & Engage
 * Data: { keyword: string, count: number }
 */
async function searchAndEngage(job) {
    const { keyword, count = 3 } = job.data;
    const context = await getContext();
    const page = await context.newPage();
    try {
        if (!await checkLogin(page))
            return { success: false, error: 'Not logged in' };
        logger_1.logger.info(`[${job.id}] Searching for "${keyword}"`);
        const encoded = encodeURIComponent(keyword);
        // Filter by Content + Sort by Latest (as per Python script intent)
        await page.goto(`https://www.linkedin.com/search/results/content/?keywords=${encoded}&origin=GLOBAL_SEARCH_HEADER&sortBy="date_posted"`);
        await randomDelay(4000, 6000);
        let actions = 0;
        // Similar to engageFeed but on search results
        const likeButtons = await page.locator('button[aria-label*="Like"]:not([aria-label*="Undo"])').all();
        for (const btn of likeButtons) {
            if (actions >= count)
                break;
            if (await btn.isVisible()) {
                await btn.click();
                actions++;
                logger_1.logger.info(`[${job.id}] Liked search result (${actions}/${count})`);
                await randomDelay(2000, 4000);
            }
        }
        return { success: true, actionsPerformed: actions };
    }
    catch (error) {
        logger_1.logger.error(`[${job.id}] Search Engagement Failed: ${error.message}`);
        throw error;
    }
    finally {
        await context.close();
    }
}
/**
 * JOB: Scrape Notifications
 * Data: { maxCount: number }
 */
async function scrapeNotifications(job) {
    const maxCount = job.data.maxCount || 5;
    const context = await getContext();
    const page = await context.newPage();
    try {
        if (!await checkLogin(page))
            return { success: false, error: 'Not logged in' };
        await page.goto('https://www.linkedin.com/notifications/');
        await randomDelay();
        const cards = await page.locator('.nt-card').all();
        const notifications = [];
        for (const card of cards.slice(0, maxCount)) {
            const text = await card.innerText();
            const classes = await card.getAttribute('class');
            const unread = classes?.includes('nt-card--unread') || false;
            notifications.push({
                text: text.replace(/\n/g, ' ').trim(),
                unread,
                timestamp: new Date().toISOString()
            });
        }
        logger_1.logger.info(`[${job.id}] Scraped ${notifications.length} notifications`);
        return { success: true, notifications };
    }
    catch (error) {
        logger_1.logger.error(`[${job.id}] Notification Scrape Failed: ${error.message}`);
        throw error;
    }
    finally {
        await context.close();
    }
}
/**
 * JOB: Scrape Analytics
 * Data: {}
 */
async function scrapeAnalytics(job) {
    const context = await getContext();
    const page = await context.newPage();
    try {
        if (!await checkLogin(page))
            return { success: false, error: 'Not logged in' };
        await page.goto('https://www.linkedin.com/in/'); // Redirects to own profile
        await randomDelay();
        // Followers
        // Try to find the "followers" link in the header or activity section
        let count = 0;
        try {
            const followersLink = page.locator('a[href*="followers"]');
            if (await followersLink.count() > 0) {
                const text = await followersLink.first().innerText();
                const num = text.replace(/[^0-9]/g, '');
                count = parseInt(num) || 0;
            }
        }
        catch (e) {
            logger_1.logger.warn('Could not find follower count via link, trying generic search');
        }
        logger_1.logger.info(`[${job.id}] Scraped Analytics: ${count} followers`);
        return { success: true, followers: count };
    }
    catch (error) {
        logger_1.logger.error(`[${job.id}] Analytics Scrape Failed: ${error.message}`);
        throw error;
    }
    finally {
        await context.close();
    }
}
