/**
 * Veyra API Client
 * Clean REST client for all backend endpoints.
 */

const API_BASE = window.location.origin;

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorDetail = errorData.detail.map(d => `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}`).join(', ');
          } else {
            errorDetail = errorData.detail;
          }
        }
      } catch (_) {}
      throw new Error(errorDetail);
    }
    if (res.status === 204) {
      return null;
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error on [${options.method || 'GET'} ${endpoint}]:`, err);
    throw err;
  }
}

export const api = {
  // Health
  getHealth: () => request('/health'),

  // Goals
  getGoals: () => request('/goals'),
  getGoal: (id) => request(`/goals/${id}`),
  createGoal: (data) => request('/goals', { method: 'POST', body: JSON.stringify(data) }),
  deleteGoal: (id) => request(`/goals/${id}`, { method: 'DELETE' }),

  // Tasks
  getTasksForGoal: (goalId) => request(`/goals/${goalId}/tasks`),
  getTask: (id) => request(`/tasks/${id}`),
  createTask: (goalId, data) => request(`/goals/${goalId}/tasks`, { method: 'POST', body: JSON.stringify(data) }),
  updateTask: (id, data) => request(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteTask: (id) => request(`/tasks/${id}`, { method: 'DELETE' }),

  // AI Proposals
  generatePlan: (goalId, prompt) => request('/ai/plans', {
    method: 'POST',
    body: JSON.stringify({ goal_id: goalId, prompt }),
  }),
  getProposal: (id) => request(`/ai/plans/${id}`),
  approveProposal: (id) => request(`/ai/plans/${id}/approve`, { method: 'POST' }),
  rejectProposal: (id) => request(`/ai/plans/${id}/reject`, { method: 'POST' }),

  // Deterministic Scheduling
  generateSchedule: (goalId, startTime, availableMinutes) => request(`/goals/${goalId}/schedule`, {
    method: 'POST',
    body: JSON.stringify({ start_time: startTime, available_minutes: availableMinutes }),
  }),

  // Reviewable Replanning
  replanGoal: (goalId, startTime, availableMinutes) => request(`/goals/${goalId}/replan`, {
    method: 'POST',
    body: JSON.stringify({ start_time: startTime, available_minutes: availableMinutes }),
  }),
  applyReplanning: (goalId, adjustments) => request(`/goals/${goalId}/replan/apply`, {
    method: 'POST',
    body: JSON.stringify({ adjustments }),
  }),
};
