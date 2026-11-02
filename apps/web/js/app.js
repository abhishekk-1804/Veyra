/**
 * Veyra Application Bootstrap
 * Vanilla JavaScript (ES Module) Main Entrypoint
 */

import { api } from './api.js';
import { store } from './state.js';
import { initRouter } from './router.js';
import { renderDashboard } from './dashboard.js';
import { renderGoals, selectGoal } from './goals.js';
import { renderPlanner } from './planner.js';
import { renderExecution } from './execution.js';
import { showToast } from './ui.js';

async function init() {
  console.log('Initializing Veyra AI-Native Execution Platform...');

  // Health check
  try {
    const health = await api.getHealth();
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-label');
    if (statusDot && statusText) {
      statusDot.style.backgroundColor = 'var(--accent-emerald)';
      statusText.textContent = 'API CONNECTED';
    }
  } catch (err) {
    console.warn('Backend offline or health check failed:', err);
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-label');
    if (statusDot && statusText) {
      statusDot.style.backgroundColor = 'var(--accent-rose)';
      statusText.textContent = 'API OFFLINE';
    }
  }

  // Load initial goals
  try {
    const goals = await api.getGoals();
    const initialSelectedId = goals.length > 0 ? goals[0].id : null;
    store.setState({ goals, selectedGoalId: initialSelectedId });
    if (initialSelectedId) {
      const tasks = await api.getTasksForGoal(initialSelectedId).catch(() => []);
      store.setState({ tasks });
    }
  } catch (err) {
    console.error('Failed to load initial goals:', err);
    showToast('Failed to connect to Veyra API', 'error');
  }

  // Initialize Router
  const router = initRouter({
    dashboard: () => renderDashboard(),
    goals: () => renderGoals(),
    planner: () => renderPlanner(),
    execution: () => renderExecution(),
  });

  // Global nav click delegation
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const view = link.getAttribute('data-view');
      router.navigate(view);
    });
  });

  console.log('Veyra application ready.');
}

window.addEventListener('DOMContentLoaded', init);
