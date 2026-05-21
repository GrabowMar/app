import './_appBase.js';
import './index.css';
import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import { APP_BASE } from './_appBase.js';
import App from './App.vue';

const router = createRouter({
  history: createWebHistory(APP_BASE + '/'),
  routes: [],
});

const app = createApp(App);
app.use(router);
app.mount('#app');
