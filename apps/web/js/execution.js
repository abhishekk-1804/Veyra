/**
 * Veyra Deterministic Execution & Replanning Controller
 */

import { store } from './state.js';
import { api } from './api.js';
import { escapeHtml, formatMinutes, formatDate, formatDateTimeLocal, showToast } from './ui.js';

export function renderExecution() {
  const container = document.getElementById('execution-view');
  if (!container) return;

  const { goals, selectedGoalId, activeSchedule, activeReplanning } = store.getState();
  const activeGoal = store.getSelectedGoal();

  container.innerHTML = `
    <div class="execution-container">
      <div class="dashboard-hero">
        <h1 class="hero-title">Deterministic Execution Engine</h1>
        <p class="hero-subtitle">Pure algorithmic dispatch bounded by time capacity. No system-clock dependencies.</p>
      </div>

      <div class="invariant-banner">
        <div class="invariant-icon">⚙️</div>
        <div class="invariant-text">
          <strong>Deterministic Guarantee:</strong> Identical tasks and execution windows produce identical execution plans. Replanning proposes adjustments for your explicit approval.
        </div>
      </div>

      <!-- Execution Window Configuration -->
      <div class="execution-config-card">
        <div class="config-fields">
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label" for="schedule-goal-select">Active Goal</label>
            <select id="schedule-goal-select">
              ${goals.length === 0 ? '<option value="">No goals available</option>' : ''}
              ${goals.map(g => `
                <option value="${g.id}" ${g.id === selectedGoalId ? 'selected' : ''}>
                  ${escapeHtml(g.title)}
                </option>
              `).join('')}
            </select>
          </div>

          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label" for="schedule-start-time">Window Start Time</label>
            <input type="datetime-local" id="schedule-start-time" value="${formatDateTimeLocal()}" />
          </div>

          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label" for="schedule-minutes">Available Capacity (Mins)</label>
            <div style="display: flex; gap: 6px;">
              <input type="number" id="schedule-minutes" value="180" min="15" max="1440" style="width: 100px;" />
              <button class="btn btn-secondary btn-sm preset-min-btn" data-min="120">2h</button>
              <button class="btn btn-secondary btn-sm preset-min-btn" data-min="240">4h</button>
              <button class="btn btn-secondary btn-sm preset-min-btn" data-min="480">8h</button>
            </div>
          </div>
        </div>

        <div style="display: flex; gap: 8px;">
          <button class="btn btn-primary" id="compute-schedule-btn" ${goals.length === 0 ? 'disabled' : ''}>
            ▶ Compute Schedule
          </button>
        </div>
      </div>

      <!-- Schedule Results Container -->
      <div id="schedule-results-area">
        ${renderScheduleOutput(activeSchedule)}
      </div>

      <!-- Replanning Section -->
      <div class="replanning-section">
        <div class="replanning-header">
          <div>
            <div class="card-title">Reviewable Replanning</div>
            <div class="card-subtitle">Detect overdue tasks and priority bottlenecks to adjust workload</div>
          </div>
          <button class="btn btn-secondary btn-sm" id="trigger-replan-btn" ${goals.length === 0 ? 'disabled' : ''}>
            🔄 Analyze & Propose Replan
          </button>
        </div>
        <div id="replanning-results-area">
          ${renderReplanningOutput(activeReplanning)}
        </div>
      </div>
    </div>
  `;

  // Goal select change
  const goalSelect = document.getElementById('schedule-goal-select');
  if (goalSelect) {
    goalSelect.onchange = (e) => {
      store.setState({ selectedGoalId: e.target.value });
    };
  }

  // Presets
  container.querySelectorAll('.preset-min-btn').forEach(btn => {
    btn.onclick = () => {
      const min = btn.getAttribute('data-min');
      const input = document.getElementById('schedule-minutes');
      if (input) input.value = min;
    };
  });

  // Compute Schedule Button
  const computeBtn = document.getElementById('compute-schedule-btn');
  if (computeBtn) {
    computeBtn.onclick = async () => {
      const goalId = document.getElementById('schedule-goal-select').value;
      const startTimeInput = document.getElementById('schedule-start-time').value;
      const minutesInput = document.getElementById('schedule-minutes').value;

      if (!goalId) {
        showToast('Please select a goal first', 'error');
        return;
      }

      const startTime = startTimeInput ? new Date(startTimeInput).toISOString() : new Date().toISOString();
      const availableMinutes = parseInt(minutesInput, 10) || 180;

      computeBtn.disabled = true;
      computeBtn.textContent = 'Computing...';

      try {
        const schedule = await api.generateSchedule(goalId, startTime, availableMinutes);
        store.setState({ activeSchedule: schedule });
        showToast('Deterministic schedule generated', 'success');
        renderExecution();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        computeBtn.disabled = false;
        computeBtn.textContent = '▶ Compute Schedule';
      }
    };
  }

  // Trigger Replan Button
  const replanBtn = document.getElementById('trigger-replan-btn');
  if (replanBtn) {
    replanBtn.onclick = async () => {
      const goalId = document.getElementById('schedule-goal-select').value;
      const startTimeInput = document.getElementById('schedule-start-time').value;
      const minutesInput = document.getElementById('schedule-minutes').value;

      if (!goalId) {
        showToast('Please select a goal first', 'error');
        return;
      }

      const startTime = startTimeInput ? new Date(startTimeInput).toISOString() : new Date().toISOString();
      const availableMinutes = parseInt(minutesInput, 10) || 180;

      replanBtn.disabled = true;
      replanBtn.textContent = 'Analyzing...';

      try {
        const replanProposal = await api.replanGoal(goalId, startTime, availableMinutes);
        store.setState({ activeReplanning: replanProposal });
        showToast(`Replanning analysis complete: ${replanProposal.adjustments.length} adjustments proposed`, 'info');
        renderExecution();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        replanBtn.disabled = false;
        replanBtn.textContent = '🔄 Analyze & Propose Replan';
      }
    };
  }

  bindReplanningActions();
}

function renderScheduleOutput(schedule) {
  if (!schedule) {
    return `
      <div class="empty-state">
        <div class="empty-icon">⏱️</div>
        <div class="empty-title">No Execution Plan Computed</div>
        <div class="empty-desc">Configure your available window above and compute a deterministic execution schedule.</div>
      </div>
    `;
  }

  const { scheduled = [], deferred = [], total_scheduled_minutes = 0, total_deferred_minutes = 0 } = schedule;
  const capacityMinutes = total_scheduled_minutes + 60; // relative reference or total capacity
  const topTask = scheduled.length > 0 ? scheduled[0] : null;

  return `
    <!-- Focus Spotlight -->
    ${topTask ? `
      <div class="focus-spotlight">
        <div class="spotlight-badge">⚡ Immediate Focus Task</div>
        <div class="spotlight-title">${escapeHtml(topTask.title)}</div>
        <div class="spotlight-meta">
          <span class="badge badge-${topTask.priority.toLowerCase()}">${topTask.priority}</span>
          <span>Window: [${topTask.start_offset}m → ${topTask.end_offset}m]</span>
          <span>Duration: ${formatMinutes(topTask.estimated_minutes)}</span>
          ${topTask.due_date ? `<span>Due: ${formatDate(topTask.due_date)}</span>` : ''}
        </div>
      </div>
    ` : ''}

    <!-- Utilization Overview -->
    <div class="utilization-card" style="margin-top: 1rem;">
      <div class="utilization-header">
        <span>Capacity Utilization: <strong>${formatMinutes(total_scheduled_minutes)} scheduled</strong> (${scheduled.length} tasks)</span>
        <span>Deferred: <strong>${formatMinutes(total_deferred_minutes)}</strong> (${deferred.length} tasks)</span>
      </div>
      <div class="utilization-bar-track">
        <div class="utilization-bar-fill" style="width: ${total_scheduled_minutes > 0 ? Math.min(100, Math.round((total_scheduled_minutes / (total_scheduled_minutes + total_deferred_minutes || 1)) * 100)) : 0}%;"></div>
      </div>
    </div>

    <!-- Scheduled vs Deferred Columns -->
    <div class="schedule-columns" style="margin-top: 1.25rem;">
      <!-- Scheduled Queue -->
      <div class="queue-card">
        <div class="card-header">
          <span class="card-title">Scheduled Sequence (${scheduled.length})</span>
          <span class="badge badge-accepted">Within Window</span>
        </div>
        <div class="queue-list">
          ${scheduled.length === 0 ? `
            <div style="font-size: 0.85rem; color: var(--text-muted); padding: 1rem; text-align: center;">
              No tasks scheduled in this window.
            </div>
          ` : scheduled.map(t => `
            <div class="queue-item">
              <div class="queue-item-left">
                <span class="queue-item-title">${escapeHtml(t.title)}</span>
                <span class="queue-item-offset">[${t.start_offset}m - ${t.end_offset}m] • ${formatMinutes(t.estimated_minutes)}</span>
              </div>
              <div class="queue-item-right">
                <span class="badge badge-${t.priority.toLowerCase()}">${t.priority}</span>
              </div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Deferred Queue -->
      <div class="queue-card">
        <div class="card-header">
          <span class="card-title">Deferred Tasks (${deferred.length})</span>
          <span class="badge badge-pending">Next Window</span>
        </div>
        <div class="queue-list">
          ${deferred.length === 0 ? `
            <div style="font-size: 0.85rem; color: var(--text-muted); padding: 1rem; text-align: center;">
              Zero deferred tasks. Entire workload fits in window!
            </div>
          ` : deferred.map(t => `
            <div class="queue-item" style="opacity: 0.75;">
              <div class="queue-item-left">
                <span class="queue-item-title">${escapeHtml(t.title)}</span>
                <span class="queue-item-offset">${formatMinutes(t.estimated_minutes)}</span>
              </div>
              <div class="queue-item-right">
                <span class="badge badge-${t.priority.toLowerCase()}">${t.priority}</span>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
}

function renderReplanningOutput(replanning) {
  if (!replanning) {
    return `
      <p style="font-size: 0.85rem; color: var(--text-muted);">
        No active replanning proposal. Click "Analyze & Propose Replan" to evaluate overdue tasks or priority bottlenecks.
      </p>
    `;
  }

  const { adjustments = [], current_schedule = null } = replanning;

  if (adjustments.length === 0) {
    return `
      <div style="font-size: 0.85rem; color: var(--accent-emerald); padding: 0.75rem 0;">
        ✓ Schedule is balanced and healthy. No priority escalations or deferral adjustments required.
      </div>
    `;
  }

  return `
    <div style="margin-top: 0.5rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
        <span style="font-size: 0.85rem; color: var(--text-secondary);">
          Proposed Adjustments (${adjustments.length}):
        </span>
        <button class="btn btn-success btn-sm" id="apply-replan-btn">
          ✓ Apply All Adjustments
        </button>
      </div>

      <div class="adjustments-list">
        ${adjustments.map(adj => `
          <div class="adjustment-item">
            <div>
              <strong style="color: var(--text-primary);">${escapeHtml(adj.action)}:</strong>
              <span style="color: var(--text-secondary); margin-left: 6px;">${escapeHtml(adj.reason)}</span>
            </div>
            ${adj.suggested_priority ? `
              <span class="badge badge-${adj.suggested_priority.toLowerCase()}">${adj.suggested_priority}</span>
            ` : ''}
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

function bindReplanningActions() {
  const applyBtn = document.getElementById('apply-replan-btn');
  if (applyBtn) {
    applyBtn.onclick = async () => {
      const { selectedGoalId, activeReplanning } = store.getState();
      if (!selectedGoalId || !activeReplanning) return;

      applyBtn.disabled = true;
      applyBtn.textContent = 'Applying...';

      try {
        const result = await api.applyReplanning(selectedGoalId, activeReplanning.adjustments);
        showToast(`Replanning applied! ${result.applied_count} adjustments executed`, 'success');
        store.setState({ activeReplanning: null });
        renderExecution();
      } catch (err) {
        showToast(err.message, 'error');
        applyBtn.disabled = false;
        applyBtn.textContent = '✓ Apply All Adjustments';
      }
    };
  }
}
