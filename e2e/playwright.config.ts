import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [["html"], ["line"]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    { command: "cd ../backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000", url: "http://localhost:8000/health", reuseExistingServer: !process.env.CI, timeout: 30000 },
    { command: "cd ../frontend && pnpm build && pnpm start", url: "http://localhost:3000", reuseExistingServer: !process.env.CI, timeout: 60000 },
  ],
})
