/**
 * Veyra Goals & Tasks Workspace Controller
 */

import { store } from './state.js';
import { api } from './api.js';
import { escapeHtml, formatMinutes, formatDate, showToast, showModal, closeModal } from './ui.js';

export async function renderGoals() {
  const container = document.getElementById('goals-view');
  if (!container) return;

  const { goals, selectedGoalId, tasks, taskFilter } = store.getState();
  const activeGoal = store.getSelectedGoal();

  // Filter tasks
  const filteredTasks = tasks.filter(t => {
    if (taskFilter === 'ALL') return true;
    return t.status === taskFilter;
  });

  const completedCount = tasks.filter(t => t.status === 'COMPLETED').length;
  const progressPct = tasks.length > 0 ? Math.round((completedCount / tasks.length) * 100) : 0;

  container.innerHTML = `
    <div class="workspace-layout">
      <!-- Left Sidebar: Goals -->
      <aside class="goals-sidebar">
        <div class="goals-sidebar-header">
          <h2 class="card-title">Goals</h2>
          <button class="btn btn-primary btn-sm" id="create-goal-btn">+ New Goal</button>
        </div>
        <div class="goals-list">
          ${goals.length === 0 ? `
            <div class="empty-state" style="padding: 1.5rem 1rem;">
              <div class="empty-title" style="font-size: 0.95rem;">No Goals</div>
              <p class="empty-desc" style="font-size: 0.8rem;">Create your first goal to begin.</p>
            </div>
          ` : goals.map(g => {
            const isSelected = g.id === selectedGoalId;
            return `
              <div class="goal-item ${isSelected ? 'active' : ''}" data-id="${g.id}">
                <div class="goal-item-top">
                  <span class="goal-item-title">${escapeHtml(g.title)}</span>
                </div>
                <div class="goal-item-meta">
                  <span>${formatDate(g.target_date)}</span>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </aside>

      <!-- Right Panel: Goal Details & Tasks -->
      <main class="tasks-panel">
        ${!activeGoal ? `
          <div class="empty-state">
            <div class="empty-icon">📂</div>
            <div class="empty-title">Select a Goal</div>
            <div class="empty-desc">Choose a goal from the sidebar or create a new one to manage its tasks.</div>
          </div>
        ` : `
          <div class="goal-detail-header">
            <div class="goal-detail-top">
              <div class="goal-title-group">
                <h2>${escapeHtml(activeGoal.title)}</h2>
                <p class="goal-description">${escapeHtml(activeGoal.description || 'No description provided.')}</p>
              </div>
              <div style="display: flex; gap: 8px;">
                <button class="btn btn-primary btn-sm" id="create-task-btn">+ Add Task</button>
                <button class="btn btn-danger btn-sm" id="delete-goal-btn">Delete Goal</button>
              </div>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar-fill" style="width: ${progressPct}%;"></div>
            </div>
            <div class="goal-stats-row">
              <span>Progress: ${progressPct}%</span>
              <span>Tasks: ${tasks.length} (${completedCount} completed)</span>
              <span>Target: ${formatDate(activeGoal.target_date)}</span>
            </div>
          </div>

          <div class="tasks-controls">
            <div class="filter-group">
              ${['ALL', 'TODO', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'].map(f => `
                <button class="filter-btn ${taskFilter === f ? 'active' : ''}" data-filter="${f}">
                  ${f.replace('_', ' ')}
                </button>
              `).join('')}
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-family: var(--font-mono);">
              Showing ${filteredTasks.length} of ${tasks.length}
            </div>
          </div>

          <div class="tasks-list">
            ${filteredTasks.length === 0 ? `
              <div class="empty-state">
                <div class="empty-icon">📝</div>
                <div class="empty-title">No tasks found</div>
                <div class="empty-desc">Add tasks manually or use the AI Planner to propose a milestone decomposition.</div>
                <button class="btn btn-secondary btn-sm" id="quick-add-task-btn">+ Add First Task</button>
              </div>
            ` : filteredTasks.map(t => `
              <div class="task-item ${t.status.toLowerCase()}" data-id="${t.id}">
                <div class="task-left">
                  <select class="status-select" data-task-id="${t.id}">
                    <option value="TODO" ${t.status === 'TODO' ? 'selected' : ''}>TODO</option>
                    <option value="IN_PROGRESS" ${t.status === 'IN_PROGRESS' ? 'selected' : ''}>IN PROGRESS</option>
                    <option value="COMPLETED" ${t.status === 'COMPLETED' ? 'selected' : ''}>COMPLETED</option>
                    <option value="CANCELLED" ${t.status === 'CANCELLED' ? 'selected' : ''}>CANCELLED</option>
                  </select>
                  <div class="task-content">
                    <span class="task-title">${escapeHtml(t.title)}</span>
                    ${t.description ? `<span class="task-notes">${escapeHtml(t.description)}</span>` : ''}
                  </div>
                </div>
                <div class="task-right">
                  <span class="badge badge-${t.priority.toLowerCase()}">${t.priority}</span>
                  ${t.estimated_minutes ? `
                    <span class="task-meta-tag">⏱️ ${formatMinutes(t.estimated_minutes)}</span>
                  ` : ''}
                  ${t.due_date ? `
                    <span class="task-meta-tag">📅 ${formatDate(t.due_date)}</span>
                  ` : ''}
                  <button class="btn btn-icon delete-task-btn" data-task-id="${t.id}" title="Delete Task">🗑️</button>
                </div>
              </div>
            `).join('')}
          </div>
        `}
      </main>
    </div>
  `;

  // Bind Goal Items click
  container.querySelectorAll('.goal-item').forEach(el => {
    el.onclick = async () => {
      const goalId = el.getAttribute('data-id');
      await selectGoal(goalId);
    };
  });

  // Bind New Goal button
  const createGoalBtn = document.getElementById('create-goal-btn');
  if (createGoalBtn) {
    createGoalBtn.onclick = () => openCreateGoalModal();
  }

  // Bind Delete Goal button
  const deleteGoalBtn = document.getElementById('delete-goal-btn');
  if (deleteGoalBtn && activeGoal) {
    deleteGoalBtn.onclick = () => {
      showModal({
        title: 'Delete Goal',
        bodyHtml: `
          <p style="color: var(--text-secondary); margin-bottom: 1rem;">
            Are you sure you want to delete <strong>${escapeHtml(activeGoal.title)}</strong>?
            All associated tasks and proposals will be permanently removed.
          </p>
        `,
        confirmText: 'Delete Permanently',
        confirmClass: 'btn-danger',
        onConfirm: async () => {
          try {
            await api.deleteGoal(activeGoal.id);
            showToast('Goal deleted successfully', 'success');
            const updatedGoals = store.getState().goals.filter(g => g.id !== activeGoal.id);
            const nextSelectedId = updatedGoals.length > 0 ? updatedGoals[0].id : null;
            store.setState({ goals: updatedGoals, selectedGoalId: nextSelectedId, tasks: [] });
            if (nextSelectedId) {
              await selectGoal(nextSelectedId);
            } else {
              renderGoals();
            }
          } catch (err) {
            showToast(err.message, 'error');
          }
        },
      });
    };
  }

  // Bind Filter buttons
  container.querySelectorAll('.filter-btn').forEach(btn => {
    btn.onclick = () => {
      const filter = btn.getAttribute('data-filter');
      store.setState({ taskFilter: filter });
      renderGoals();
    };
  });

  // Bind Add Task buttons
  const addTaskBtns = [
    document.getElementById('create-task-btn'),
    document.getElementById('quick-add-task-btn')
  ].filter(Boolean);

  addTaskBtns.forEach(btn => {
    btn.onclick = () => openCreateTaskModal();
  });

  // Bind Status Dropdowns
  container.querySelectorAll('.status-select').forEach(select => {
    select.onchange = async (e) => {
      const taskId = select.getAttribute('data-task-id');
      const newStatus = e.target.value;
      try {
        await api.updateTask(taskId, { status: newStatus });
        showToast(`Task status updated to ${newStatus}`, 'success');
        await refreshTasks();
      } catch (err) {
        showToast(err.message, 'error');
        await refreshTasks(); // rollback select on error
      }
    };
  });

  // Bind Delete Task buttons
  container.querySelectorAll('.delete-task-btn').forEach(btn => {
    btn.onclick = async () => {
      const taskId = btn.getAttribute('data-task-id');
      try {
        await api.deleteTask(taskId);
        showToast('Task removed', 'success');
        await refreshTasks();
      } catch (err) {
        showToast(err.message, 'error');
      }
    };
  });
}

export async function selectGoal(goalId) {
  store.setState({ selectedGoalId: goalId });
  await refreshTasks();
  renderGoals();
}

async function refreshTasks() {
  const { selectedGoalId } = store.getState();
  if (!selectedGoalId) return;
  try {
    const tasks = await api.getTasksForGoal(selectedGoalId);
    store.setState({ tasks });
  } catch (err) {
    console.error('Failed to fetch tasks:', err);
  }
}

function openCreateGoalModal() {
  showModal({
    title: 'Create New Goal',
    bodyHtml: `
      <form id="create-goal-form">
        <div class="form-group">
          <label class="form-label" for="goal-title-input">Goal Title *</label>
          <input type="text" id="goal-title-input" required maxlength="200" placeholder="e.g., Deliver Veyra V1 Platform" />
        </div>
        <div class="form-group">
          <label class="form-label" for="goal-desc-input">Description</label>
          <textarea id="goal-desc-input" rows="3" maxlength="2000" placeholder="Summary of objective and key requirements..."></textarea>
        </div>
        <div class="form-group">
          <label class="form-label" for="goal-target-input">Target Date</label>
          <input type="date" id="goal-target-input" />
        </div>
      </form>
    `,
    confirmText: 'Create Goal',
    confirmClass: 'btn-primary',
    onConfirm: async () => {
      const title = document.getElementById('goal-title-input').value.trim();
      const description = document.getElementById('goal-desc-input').value.trim() || null;
      const targetDate = document.getElementById('goal-target-input').value || null;

      if (!title) {
        showToast('Goal title is required', 'error');
        return false;
      }

      try {
        const newGoal = await api.createGoal({
          title,
          description,
          target_date: targetDate ? new Date(targetDate).toISOString() : null,
        });
        showToast('Goal created successfully', 'success');
        const updatedGoals = [...store.getState().goals, newGoal];
        store.setState({ goals: updatedGoals, selectedGoalId: newGoal.id, tasks: [] });
        await selectGoal(newGoal.id);
        return true;
      } catch (err) {
        showToast(err.message, 'error');
        return false;
      }
    },
  });
}

function openCreateTaskModal() {
  const activeGoal = store.getSelectedGoal();
  if (!activeGoal) return;

  showModal({
    title: `Add Task to ${escapeHtml(activeGoal.title)}`,
    bodyHtml: `
      <form id="create-task-form">
        <div class="form-group">
          <label class="form-label" for="task-title-input">Task Title *</label>
          <input type="text" id="task-title-input" required maxlength="200" placeholder="e.g., Setup database migrations" />
        </div>
        <div class="form-group">
          <label class="form-label" for="task-desc-input">Description / Notes</label>
          <textarea id="task-desc-input" rows="2" maxlength="2000" placeholder="Implementation details or acceptance criteria..."></textarea>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="form-group">
            <label class="form-label" for="task-priority-select">Priority</label>
            <select id="task-priority-select">
              <option value="LOW">Low</option>
              <option value="MEDIUM" selected>Medium</option>
              <option value="HIGH">High</option>
              <option value="URGENT">Urgent</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label" for="task-estimate-input">Estimated Minutes</label>
            <input type="number" id="task-estimate-input" min="1" max="1440" placeholder="e.g., 45" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label" for="task-due-input">Due Date</label>
          <input type="date" id="task-due-input" />
        </div>
      </form>
    `,
    confirmText: 'Create Task',
    confirmClass: 'btn-primary',
    onConfirm: async () => {
      const title = document.getElementById('task-title-input').value.trim();
      const description = document.getElementById('task-desc-input').value.trim() || null;
      const priority = document.getElementById('task-priority-select').value;
      const estimateVal = document.getElementById('task-estimate-input').value;
      const dueDateVal = document.getElementById('task-due-input').value;

      if (!title) {
        showToast('Task title is required', 'error');
        return false;
      }

      const payload = {
        title,
        description,
        priority,
        estimated_minutes: estimateVal ? parseInt(estimateVal, 10) : null,
        due_date: dueDateVal ? new Date(dueDateVal).toISOString() : null,
      };

      try {
        await api.createTask(activeGoal.id, payload);
        showToast('Task created', 'success');
        await refreshTasks();
        renderGoals();
        return true;
      } catch (err) {
        showToast(err.message, 'error');
        return false;
      }
    },
  });
}
