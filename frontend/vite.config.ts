import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

const apiTarget = process.env.API_TARGET ?? 'http://localhost:8000';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		proxy: {
			'/api': {
				target: apiTarget,
				changeOrigin: true,
			},
			'/_allauth': {
				target: apiTarget,
				changeOrigin: true,
			},
			'/admin': {
				target: apiTarget,
				changeOrigin: true,
			},
			'/media': {
				target: apiTarget,
				changeOrigin: true,
			},
		},
	},
});
