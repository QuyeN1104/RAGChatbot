import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';
const apiProxy = {
  target: apiTarget,
  changeOrigin: true,
  rewrite: (path) => path.replace(/^\/api(?=\/|$)/, '') || '/',
};

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { host: '0.0.0.0', proxy: { '/api': apiProxy } },
  preview: { host: '0.0.0.0', proxy: { '/api': apiProxy } },
});
