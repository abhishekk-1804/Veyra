/**
 * Veyra Dashboard View Controller
 */

import { store } from './state.js';
import { api } from './api.js';
import { escapeHtml, formatMinutes, formatDate } from './ui.js';

export async function renderDashboard() {
  const container = document.getElementById('dashboard-view');
  if (!container) return;

  const { goals } = store.getState();

  // Fetch tasks for all goals to compute aggregate portfolio metrics
  let allTasks = [];
  try {
    const taskPromises = goals.map(g => api.getTasksForGoal(g.id).catch(() => []));
    const taskResults = await Promise.all(taskPromises);
    allTasks = taskResults.flat();
  } catch (err) {
    console.error('Error calculating dashboard metrics:', err);
  }

  const totalGoals = goals.length;
  const totalTasks = allTasks.length;
  const completedTasks = allTasks.filter(t => t.status === 'COMPLETED').length;
  const activeTasks = allTasks.filter(t => t.status === 'TODO' || t.status === 'IN_PROGRESS').length;
  const completionRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
  const totalMinutes = allTasks.reduce((acc, t) => acc + (t.estimated_minutes || 0), 0);

  container.innerHTML = `
    <div class="dashboard-hero">
      <h1 class="hero-title">Execution Portfolio</h1>
      <p class="hero-subtitle">Deterministic task execution and verifiable AI planning workspace.</p>
    </div>

    <div class="invariant-banner">
      <div class="invariant-icon">⚖️</div>
      <div class="invariant-text">
        <strong>Architectural Invariant:</strong> AI proposes plans. Deterministic application code validates, decides, persists, and executes.
      </div>
    </div>

    <div class="metrics-grid">
      <div class="metric-card">
        <span class="metric-label">Active Goals</span>
        <span class="metric-value">${totalGoals}</span>
        <span class="metric-sub">Total tracked objectives</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">In-Flight Tasks</span>
        <span class="metric-value">${activeTasks}</span>
        <span class="metric-sub">Across all active goals</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">Completion Rate</span>
        <span class="metric-value">${completionRate}%</span>
        <span class="metric-sub">${completedTasks} of ${totalTasks} tasks finished</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">Planned Time</span>
        <span class="metric-value">${formatMinutes(totalMinutes)}</span>
        <span class="metric-sub">Total estimated effort</span>
      </div>
    </div>

    <div class="arch-card">
      <div class="card-title">Continuous Execution Lifecycle</div>
      <div class="card-subtitle">Transparent control flow from intent formulation to deterministic dispatch</div>
      <div class="arch-flow">
        <div class="arch-step">
          <span class="arch-step-badge badge-intent">1. Intent</span>
          <div class="arch-step-title">Objective Definition</div>
          <div class="arch-step-desc">Establish verified goals and target milestones</div>
        </div>
        <div class="arch-arrow">→</div>
        <div class="arch-step">
          <span class="arch-step-badge badge-propose">2. Propose</span>
          <div class="arch-step-title">AI Decomposition</div>
          <div class="arch-step-desc">Structured, ephemeral plan proposals generated</div>
        </div>
        <div class="arch-arrow">→</div>
        <div class="arch-step">
          <span class="arch-step-badge badge-decide">3. Decide</span>
          <div class="arch-step-title">Explicit Approval</div>
          <div class="arch-step-desc">Human verifies. Zero tasks created without approval</div>
        </div>
        <div class="arch-arrow">→</div>
        <div class="arch-step">
          <span class="arch-step-badge badge-execute">4. Execute</span>
          <div class="arch-step-title">Deterministic Dispatch</div>
          <div class="arch-step-desc">Pure scheduling sequence bounded by capacity</div>
        </div>
      </div>
    </div>

    <div class="dashboard-goals-section">
      <div class="dashboard-goals-header">
        <h2 class="card-title">Portfolio Objectives</h2>
        <button class="btn btn-secondary btn-sm" id="dashboard-new-goal-btn">+ Add Goal</button>
      </div>
      <div class="dashboard-goals-list">
        ${goals.length === 0 ? `
          <div class="empty-state" style="grid-column: 1 / -1;">
            <div class="empty-icon">🎯</div>
            <div class="empty-title">No Goals Configured</div>
            <div class="empty-desc">Create your first goal to begin planning and deterministic scheduling.</div>
            <button class="btn btn-primary" id="dashboard-empty-new-goal-btn">Create Goal</button>
          </div>
        ` : goals.map(g => {
          const goalTasks = allTasks.filter(t => t.goal_id === g.id);
          const goalDone = goalTasks.filter(t => t.status === 'COMPLETED').length;
          const pct = goalTasks.length > 0 ? Math.round((goalDone / goalTasks.length) * 100) : 0;
          return `
            <div class="card goal-card-preview" data-id="${g.id}">
              <div class="card-header">
                <span class="card-title">${escapeHtml(g.title)}</span>
                <span class="badge badge-${pct === 100 ? 'completed' : 'in_progress'}">${pct}%</span>
              </div>
              <p class="card-subtitle" style="margin-bottom: 1rem; line-height: 1.4;">
                ${escapeHtml(g.description || 'No description provided.')}
              </p>
              <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: ${pct}%;"></div>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; font-size: 0.8rem; color: var(--text-muted);">
                <span>${goalTasks.length} tasks (${goalDone} done)</span>
                <span>Target: ${formatDate(g.target_date)}</span>
              </div>
              <div style="display: flex; gap: 8px; margin-top: 1rem;">
                <button class="btn btn-secondary btn-sm select-goal-jump" data-id="${g.id}" data-tab="goals" style="flex: 1;">Workspace</button>
                <button class="btn btn-secondary btn-sm select-goal-jump" data-id="${g.id}" data-tab="planner" style="flex: 1;">Decompose</button>
                <button class="btn btn-secondary btn-sm select-goal-jump" data-id="${g.id}" data-tab="execution" style="flex: 1;">Schedule</button>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;

  // Bind actions
  const newGoalBtns = [
    document.getElementById('dashboard-new-goal-btn'),
    document.getElementById('dashboard-empty-new-goal-btn')
  ].filter(Boolean);

  newGoalBtns.forEach(btn => {
    btn.onclick = () => {
      window.location.hash = '#goals';
      setTimeout(() => {
        const createBtn = document.getElementById('create-goal-btn');
        if (createBtn) createBtn.click();
      }, 50);
    };
  });

  container.querySelectorAll('.select-goal-jump').forEach(btn => {
    btn.onclick = () => {
      const goalId = btn.getAttribute('data-id');
      const tab = btn.getAttribute('data-tab');
      store.setState({ selectedGoalId: goalId });
      window.location.hash = `#${tab}`;
    };
  });
}
