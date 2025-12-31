import dotenv from 'dotenv';
// Load environment variables before anything else
dotenv.config({ path: '.env.local' });
dotenv.config();

import next from 'next';
import express from 'express';
import { createServer } from 'http';
import { parse } from 'url';
import { startWorker } from './src/worker'; // Use relative path for server.ts

const dev = process.env.NODE_ENV !== 'production';
const hostname = 'localhost';
const port = parseInt(process.env.PORT || '3000', 10);

const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();

app.prepare().then(async () => {
    const server = express();

    // Start Backbone Worker (Scraper/Scheduler)
    try {
        await startWorker(server);
        console.log('> Worker initialized successfully');
    } catch (err) {
        console.error('> Failed to initialize worker:', err);
    }


    // Middleware / Proxy for Auth Protection (Replacment for next.js middleware)
    server.use('/underworld', (req, res, next) => {
        // Exclude Gateway (Login) from protection
        if (req.path === '/gateway') {
            return next();
        }

        // Check for auth_token in cookies
        const cookieHeader = req.headers.cookie;
        const hasToken = cookieHeader && cookieHeader.includes('auth_token=');

        if (!hasToken) {
            return res.redirect('/underworld/gateway');
        }

        next();
    });

    // Handle all other requests with Next.js
    // Handle all other requests with Next.js
    server.all(/.*/, (req: any, res: any) => {
        return handle(req, res);
    });

    server.listen(port, (err?: any) => {
        if (err) throw err;
        console.log(`> Ready on http://${hostname}:${port}`);
    });
});

