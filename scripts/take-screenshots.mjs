#!/usr/bin/env node
/**
 * Capture dashboard screenshots for the landing page.
 * Requires: playwright (mcr.microsoft.com/playwright Docker image)
 * Target:   http://localhost:9201  (production container running with seed DB)
 * Output:   /screenshots/{login,dashboard,settings}.png  (mounted volume)
 */
import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'

const BASE_URL = process.env.BASE_URL || 'http://localhost:9201'
const OUT_DIR  = process.env.OUT_DIR  || '/screenshots'
const USER     = process.env.DASH_USER || 'admin'
const PASS     = process.env.DASH_PASS || 'demo'

const VIEWPORT = { width: 1280, height: 900 }

mkdirSync(OUT_DIR, { recursive: true })

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({ viewport: VIEWPORT })
const page    = await context.newPage()

// 1. Login page (unauthenticated)
await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' })
await page.screenshot({ path: `${OUT_DIR}/login.png`, fullPage: true })
console.log('✓ login.png')

// 2. Authenticate and capture dashboard
await page.locator('[name="username"]').fill(USER)
await page.locator('#password-field').fill(PASS)
await Promise.all([
  page.waitForNavigation({ waitUntil: 'networkidle' }),
  page.locator('[type="submit"]').click(),
])
await page.screenshot({ path: `${OUT_DIR}/dashboard.png`, fullPage: true })
console.log('✓ dashboard.png')

// 3. Settings page
await page.goto(`${BASE_URL}/settings`, { waitUntil: 'networkidle' })
await page.screenshot({ path: `${OUT_DIR}/settings.png`, fullPage: true })
console.log('✓ settings.png')

await browser.close()
console.log(`Screenshots saved to ${OUT_DIR}`)
