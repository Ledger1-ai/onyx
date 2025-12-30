import { Job } from 'bullmq';
import { chromium as playwrightExtra } from 'playwright-extra';
import stealthPlugin from 'puppeteer-extra-plugin-stealth';
import { logger } from '../utils/logger';
import path from 'path';
import fs from 'fs';

// @ts-ignore - stealth plugin types issue
playwrightExtra.use(stealthPlugin());

const USER_DATA_DIR = path.resolve(process.cwd(), '../browser_profiles/twitter_automation_profile');

/**
 * Launch a persistent browser context to maintain login sessions.
 */
async function getContext() {
    // Ensure directory exists
    if (!fs.existsSync(USER_DATA_DIR)) {
        logger.info(`Creating new browser profile directory: ${USER_DATA_DIR}`);
        fs.mkdirSync(USER_DATA_DIR, { recursive: true });
    } else {
        logger.info(`Using existing browser profile: ${USER_DATA_DIR}`);
    }

    return await playwrightExtra.launchPersistentContext(USER_DATA_DIR, {
        headless: false, // Start visible for debugging settings, toggle later if needed
        channel: 'chrome',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--window-size=1920,1080'
        ],
        viewport: { width: 1920, height: 1080 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });
}

export async function scrapeTwitter(job: Job) {
    const { targetUrl } = job.data;
    logger.info(`Launching Twitter scraper for ${targetUrl || 'home timeline'}`);

    const context = await getContext();
    const page = await context.newPage();

    try {
        // Intercept GraphQL for clean data
        const collectedTweets: any[] = [];
        page.on('response', async (response) => {
            const url = response.url();
            if (url.includes('/graphql/') && (url.includes('TweetDetail') || url.includes('HomeTimeline'))) {
                try {
                    const json = await response.json();
                    collectedTweets.push(json);
                } catch (e) { }
            }
        });

        await page.goto(targetUrl || 'https://twitter.com/home', { waitUntil: 'domcontentloaded' });

        // Check for login redirect
        if (page.url().includes('login') || page.url().includes('logout')) {
            logger.warn('Session invalid, redirecting to login. Manual intervention may be required if headless.');
        }

        await page.waitForTimeout(5000);
        // Scroll to load more tweets
        await page.evaluate(() => window.scrollBy(0, 1000));
        await page.waitForTimeout(3000);

        const screenshotPath = `scrape_${job.id}.png`;
        await page.screenshot({ path: screenshotPath });

        return {
            success: true,
            tweetsFound: collectedTweets.length,
            screenshot: screenshotPath
        };

    } catch (error: any) {
        logger.error(`Scrape failed: ${error.message}`);
        throw error;
    } finally {
        await context.close();
    }
}

export async function postTweet(job: Job) {
    const { content, mediaFiles } = job.data;
    logger.info(`Posting tweet: ${content?.substring(0, 50)}...`);

    const context = await getContext();
    const page = await context.newPage();

    try {
        await page.goto('https://twitter.com/compose/tweet', { waitUntil: 'domcontentloaded' });

        const editorSelector = '[data-testid="tweetTextarea_0"]';
        // Wait longer for editor in case of network lag
        await page.waitForSelector(editorSelector, { timeout: 20000 });

        if (content) {
            await page.fill(editorSelector, content);
        }

        if (mediaFiles && mediaFiles.length > 0) {
            logger.info(`Uploading ${mediaFiles.length} media files`);
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles(mediaFiles);
            await page.waitForTimeout(5000); // Allow upload time
        }

        const tweetButton = page.locator('[data-testid="tweetButton"]');
        await tweetButton.click();

        await page.waitForSelector('[data-testid="toast"]', { timeout: 8000 })
            .catch(() => logger.info("Toast not found, assuming success"));

        logger.info('Tweet posted successfully');
        return { success: true };

    } catch (error: any) {
        logger.error(`Post tweet failed: ${error.message}`);
        await page.screenshot({ path: `error_post_${job.id}.png` });
        throw error;
    } finally {
        await context.close();
    }
}

export async function interact(job: Job) {
    const { tweetId, action, content } = job.data; // action: 'like' | 'retweet' | 'reply'
    logger.info(`Performing ${action} on tweet ${tweetId}`);

    const context = await getContext();
    const page = await context.newPage();

    try {
        await page.goto(`https://twitter.com/i/web/status/${tweetId}`, { waitUntil: 'domcontentloaded' });
        await page.waitForSelector('article', { timeout: 20000 });

        if (action === 'like') {
            const likeButton = page.locator('[data-testid="like"]');
            if (await likeButton.isVisible()) {
                await likeButton.click();
            } else {
                logger.info('Already liked or button not found');
            }
        } else if (action === 'retweet') {
            const retweetButton = page.locator('[data-testid="retweet"]');
            await retweetButton.click();
            await page.waitForSelector('[data-testid="retweetConfirm"]');
            await page.click('[data-testid="retweetConfirm"]');
        } else if (action === 'reply') {
            const replyBox = page.locator('[data-testid="tweetTextarea_0"]');
            await replyBox.click(); // Focus
            await replyBox.fill(content || '');
            await page.click('[data-testid="tweetButtonInline"]');
        }

        logger.info(`Interaction ${action} complete`);
        return { success: true };

    } catch (error: any) {
        logger.error(`Interaction failed: ${error.message}`);
        await page.screenshot({ path: `error_interact_${job.id}.png` });
        throw error;
    } finally {
        await context.close();
    }
}

export async function follow(job: Job) {
    const { username } = job.data;
    logger.info(`Following user ${username}`);

    const context = await getContext();
    const page = await context.newPage();

    try {
        await page.goto(`https://twitter.com/${username}`);
        await page.waitForLoadState('networkidle');

        // Try multiple selectors for Follow button
        const followButton = page.locator(`[aria-label^="Follow @${username}"]`).first();
        const simplifiedButton = page.locator('text=Follow').first();

        if (await followButton.isVisible()) {
            await followButton.click();
            logger.info(`Followed ${username}`);
        } else if (await simplifiedButton.isVisible()) {
            await simplifiedButton.click();
            logger.info(`Followed ${username} (simplified selector)`);
        } else {
            logger.info(`Follow button not found, potentially already following`);
        }

        return { success: true };

    } catch (error: any) {
        logger.error(`Follow failed: ${error.message}`);
        throw error;
    } finally {
        await context.close();
    }
}

export async function scrapeMentions(job: Job) {
    logger.info('Scraping mentions for auto-reply opportunities');

    const context = await getContext();
    const page = await context.newPage();
    const mentions: any[] = [];

    try {
        page.on('response', async (response) => {
            const url = response.url();
            if (url.includes('/graphql/') && url.includes('Notifications')) {
                try {
                    const json = await response.json();
                    mentions.push(json);
                } catch (e) { }
            }
        });

        await page.goto('https://twitter.com/notifications', { waitUntil: 'domcontentloaded' });
        await page.waitForSelector('[data-testid="primaryColumn"]', { timeout: 20000 });

        await page.evaluate(() => window.scrollBy(0, 1000));
        await page.waitForTimeout(5000);

        logger.info(`Captured ${mentions.length} notification batches`);

        return {
            success: true,
            mentionsFound: mentions.length
        };

    } catch (error: any) {
        logger.error(`Mentions scrape failed: ${error.message}`);
        throw error;
    } finally {
        await context.close();
    }
}
