import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs/promises";

const BASE = process.env.E2E_BASE_URL || "http://localhost:5173";
const API_BASE = process.env.E2E_API_BASE || "http://localhost:8000/api";
const API_KEY = process.env.E2E_RAILMIND_API_KEY;

async function loadApiKeyFromDotEnv(): Promise<string | undefined> {
  try {
    const envPath = new URL("../../.env", import.meta.url);
    const envContents = await fs.readFile(envPath, "utf8");
    const match = envContents.match(/^VITE_RAILMIND_API_KEY=(.+)$/m);
    return match?.[1]?.trim();
  } catch {
    return undefined;
  }
}

test.describe("Feeds E2E", () => {
  test("upload -> appears on dashboard -> stop removes feed", async ({ page, request }) => {
    await page.goto(BASE);

    // Ensure app loaded
    await expect(page.locator("text=Dashboard")).toBeVisible();

    // Use backend API to upload a small test video file to avoid complex file dialogs in Playwright
    const videoPath = new URL("../fixtures/testvideo.mp4", import.meta.url);
    const fileBuffer = await fs.readFile(videoPath);

    // Upload via backend API
    const apiKey = API_KEY || (await loadApiKeyFromDotEnv());
    if (!apiKey) {
      throw new Error(
        "Missing API key for E2E test. Set E2E_RAILMIND_API_KEY or VITE_RAILMIND_API_KEY in test environment.",
      );
    }

    await page.addInitScript((key) => {
      (window as Window & { __RAILMIND_API_KEY?: string }).__RAILMIND_API_KEY = key;
    }, apiKey);

    const uploadRes = await request.post(`${API_BASE}/feeds/upload`, {
      headers: { "X-API-Key": apiKey },
      multipart: {
        file: {
          name: "testvideo.mp4",
          mimeType: "video/mp4",
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
    await page.waitForLoadState("networkidle");

    const feedRow = page.locator("tr", { hasText: feedId });
    await expect(feedRow).toBeVisible({ timeout: 30000 });

    // Click Stop button in the same row
    await feedRow.locator('button:has-text("Stop")').click();

    // Confirm feed removed from UI
    await expect(feedRow).toHaveCount(0, { timeout: 30000 });
  });
});
