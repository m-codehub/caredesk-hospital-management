import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: true,
    allowedHosts: true,
    strictPort: false,
    port: 5173,
  },
  preview: {
    host: true,
    allowedHosts: true,
    strictPort: false,
    port: 4173,
  },
});
