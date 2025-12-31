import { chromium, BrowserContext, Page, ElementHandle } from 'playwright';
import { addExtra } from 'playwright-extra';
import stealthPlugin from 'puppeteer-extra-plugin-stealth';
import path from 'path';
import fs from 'fs';
import { logger } from '../utils/logger';

// Add stealth plugin to Playwright
const chromiumExtra = addExtra(chromium as any);
chromiumExtra.use(stealthPlugin());

export class LinkedInBrowser {
    private browser: any;
    private context: BrowserContext | null = null;
    private page: Page | null = null;
    private userDataDir: string;

    constructor(userId?: string) {
        // Dynamic profile path support for Multi-Tenant Isolation
        const profileName = userId ? `${userId}_linkedin` : 'linkedin_automation_profile';
        this.userDataDir = path.resolve(process.cwd(), `../browser_profiles/${profileName}`);

        if (!fs.existsSync(this.userDataDir)) {
            fs.mkdirSync(this.userDataDir, { recursive: true });
        }
    }

    async init() {
        try {
            logger.info(`[LinkedIn] Launching browser with profile: ${this.userDataDir}`);

            // Launch persistent context
            this.context = await (chromiumExtra as any).launchPersistentContext(this.userDataDir, {
                headless: false, // LinkedIn often requires visual check, keep false for now or Config
                channel: 'chrome',
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--window-size=1280,800'
                ],
                viewport: { width: 1280, height: 800 }
            });

            const pages = this.context!.pages();
            this.page = pages.length > 0 ? pages[0] : await this.context!.newPage();

            logger.info('[LinkedIn] Browser initialized');

            // Check login
            const isLoggedIn = await this.checkLogin();
            if (!isLoggedIn) {
                logger.warn('[LinkedIn] Not logged in. Please log in manually in the opened browser.');
                // We keep it open for manual login if this was a dedicated session, 
                // but since this is a worker, we might just fail the job if interaction is impossible.
                // For "Manual Mode", we just wait a bit or return false.
            }

        } catch (error) {
            logger.error(`[LinkedIn] Failed to init browser: ${error}`);
            throw error;
        }
    }

    async close() {
        if (this.context) {
            await this.context.close();
            this.context = null;
            this.page = null;
        }
    }

    async checkLogin(): Promise<boolean> {
        if (!this.page) return false;
        try {
            await this.page.goto('https://www.linkedin.com/feed/', { timeout: 30000 });
            await this.page.waitForTimeout(3000);

            // Check for feed indicators
            const feedIndicator = await this.page.$('.global-nav__me-photo, #global-nav-typeahead');
            if (feedIndicator) {
                logger.info('[LinkedIn] Login verified');
                return true;
            }
            return false;
        } catch (e) {
            logger.error(`[LinkedIn] Login check failed: ${e}`);
            return false;
        }
    }

    async postContent(text: string, mediaPath?: string): Promise<boolean> {
        if (!this.page) return false;
        try {
            logger.info('[LinkedIn] Starting post creation...');
            await this.page.goto('https://www.linkedin.com/feed/');
            await this.page.waitForTimeout(5000);

            // Click "Start a post"
            // Selectors: span text="Start a post", buttons with that text
            const startPostBtn = await this.page.getByText('Start a post').first();
            if (startPostBtn) {
                await startPostBtn.click();
            } else {
                // Fallback selector
                await this.page.click('.share-box-feed-entry__trigger');
            }

            await this.page.waitForTimeout(2000);

            // Handle Media
            if (mediaPath && fs.existsSync(mediaPath)) {
                logger.info(`[LinkedIn] Uploading media: ${mediaPath}`);
                // Verify if it's image or video for button selection if needed, 
                // but usually the hidden input accepts both or we click the "Media" button

                // Clicking the image/media icon often triggers system dialog, but setting input files works best in Playwright
                // Find file input in the modal
                const fileInput = await this.page.$('input[type="file"]');
                if (fileInput) {
                    await fileInput.setInputFiles(mediaPath);
                    await this.page.waitForTimeout(5000); // Wait for upload

                    // Click "Next" or "Done" if presented (image editor)
                    const nextBtn = await this.page.getByText('Next').or(this.page.getByText('Done')).first();
                    if (await nextBtn.isVisible()) {
                        await nextBtn.click();
                        await this.page.waitForTimeout(1000);
                    }
                }
            }

            // Type Text
            logger.info('[LinkedIn] Typing content...');
            const editor = await this.page.getByRole('textbox', { name: /Text editor/i }).first();
            if (editor) {
                await editor.click();
                await editor.fill(text);
            } else {
                // Fallback
                await this.page.type('.ql-editor', text);
            }
            await this.page.waitForTimeout(2000);

            // Click Post
            logger.info('[LinkedIn] Clicking Post...');
            const postBtn = await this.page.getByRole('button', { name: 'Post', exact: true }).first();
            if (postBtn && await postBtn.isEnabled()) {
                await postBtn.click();
                await this.page.waitForTimeout(5000); // Wait for post to submit
                logger.info('[LinkedIn] Post successful');
                return true;
            } else {
                logger.error('[LinkedIn] Post button not found or disabled');
                return false;
            }

        } catch (error) {
            logger.error(`[LinkedIn] Post failed: ${error}`);
            return false;
        }
    }

    async engageFeed(count: number = 5): Promise<boolean> {
        if (!this.page) return false;
        try {
            logger.info(`[LinkedIn] Engaging with feed (Count: ${count})...`);
            await this.page.goto('https://www.linkedin.com/feed/');
            await this.page.waitForTimeout(3000);

            let actions = 0;
            let scrolls = 0;

            while (actions < count && scrolls < 10) {
                // Scroll
                await this.page.evaluate(() => window.scrollBy(0, 500));
                await this.page.waitForTimeout(2000);
                scrolls++;

                // Find Like Buttons
                // Selector: button with aria-label containing "Like" but not "Undo"
                // Playwright locator is robust
                const likeButtons = await this.page.locator('button[aria-label^="Like"]:not([aria-label*="Undo"])').all();

                for (const btn of likeButtons) {
                    if (actions >= count) break;

                    if (await btn.isVisible() && Math.random() > 0.5) {
                        try {
                            await btn.click();
                            actions++;
                            logger.info('[LinkedIn] Liked a post');
                            await this.page.waitForTimeout(3000);
                        } catch (e) {
                            // Ignore click errors
                        }
                    }
                }
            }
            return true;
        } catch (error) {
            logger.error(`[LinkedIn] Engagement failed: ${error}`);
            return false;
        }
    }
}
