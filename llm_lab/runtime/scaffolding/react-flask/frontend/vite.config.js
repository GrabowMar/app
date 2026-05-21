import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base='./' emits relative asset URLs so the bundle is location-agnostic:
// it works when served at '/', '/app/<id>/', or any other mount point.
// The reverse-proxy injects <base href> so deep-link reloads also resolve.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
