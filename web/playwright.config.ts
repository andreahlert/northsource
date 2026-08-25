import { defineConfig } from "@playwright/test";

const MOCK = "http://localhost:8001";

export default defineConfig({
  testDir: "./tests",
  testMatch: /.*\.spec\.ts/,
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  use: { baseURL: "http://localhost:3000", trace: "retain-on-failure" },
  webServer: [
    {
      command: "node tests/mock-api.mjs",
      url: `${MOCK}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 15_000,
    },
    {
      command: "npm run dev",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: { API_URL: MOCK, NEXT_PUBLIC_API_URL: MOCK, NEXT_PUBLIC_REPO_URL: "https://github.com/ahlert/northsource" },
    },
  ],
});
