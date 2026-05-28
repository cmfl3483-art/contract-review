import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    // 排除 Playwright E2E 测试目录，避免被 vitest 误捡
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      'e2e/**',
      'tests/e2e/**',
      'tests/infrastructure.spec.ts',
      'tests/mobile.spec.ts',
    ],
  },
});
