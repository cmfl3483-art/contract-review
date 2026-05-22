import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Browser compatibility target
    target: ['chrome120', 'firefox120', 'safari17', 'edge120'],
    // Enable code splitting
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks(id) {
          // Vendor chunks
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router')) {
              return 'react-vendor';
            }
            if (id.includes('antd')) {
              return 'antd-vendor';
            }
            if (id.includes('@tanstack/react-query')) {
              return 'query-vendor';
            }
            if (id.includes('socket.io-client')) {
              return 'socket-vendor';
            }
            if (id.includes('axios') || id.includes('dayjs') || id.includes('zustand')) {
              return 'utils-vendor';
            }
          }
        },
      },
    },
    // Optimize chunk size
    chunkSizeWarningLimit: 1000,
    // Disable minification for now (can be enabled with terser or esbuild if needed)
    minify: false,
    // Enable source maps for production debugging (optional)
    sourcemap: false,
  },
  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'antd',
      '@tanstack/react-query',
      'axios',
      'dayjs',
      'zustand',
      'socket.io-client',
    ],
  },
});
