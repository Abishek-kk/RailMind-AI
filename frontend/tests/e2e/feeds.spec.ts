import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs/promises';

const BASE = process.env.E2E_BASE_URL || 'http://localhost:5173';
const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000/api';

test.describe('Feeds E2E', () => {
  test('upload -> appears on dashboard -> stop removes feed', async ({ page, request }) => {
    await page.goto(BASE);

    // Ensure app loaded
    await expect(page.locator('text=Dashboard')).toBeVisible();

    // Use backend API to upload a small test video file to avoid complex file dialogs in Playwright
    const videoPath = new URL('../fixtures/testvideo.mp4', import.meta.url);
    const fileBuffer = await fs.readFile(videoPath);

    // Upload via backend API
    const uploadRes = await request.post(`${API_BASE}/feeds/upload`, {
      multipart: {
        file: {
          name: 'testvideo.mp4',
          mimeType: 'video/mp4',
          buffer: fileBuffer,
        },
      },
    });

    expect(uploadRes.status()).toBe(201);
    const uploadJson = await uploadRes.json();
    const feedId = uploadJson.feed_id;
    expect(feedId).toBeTruthy();

    // Navigate to dashboard and wait for the feed row to appear
    await page.goto(`${BASE}/dashboard`);
    await page.waitForSelector(`text=${feedId}`, { timeout: 20000 });

    // Click Stop button in the same row
    const row = page.locator(`tr:has-text("${feedId}")`);
    await expect(row).toBeVisible();
    await row.locator('button:has-text("Stop")').click();

    // Confirm feed removed from UI
    await expect(page.locator(`text=${feedId}`)).toHaveCount(0);
  });
});
