/**
 * Veyra Centralized State Management
 * Minimalist pub/sub state store.
 */

class StateStore {
  constructor() {
    this.state = {
      goals: [],
      selectedGoalId: null,
      tasks: [],
      activeProposal: null,
      activeSchedule: null,
      activeReplanning: null,
      taskFilter: 'ALL', // 'ALL', 'TODO', 'IN_PROGRESS', 'COMPLETED'
    };
    this.listeners = new Set();
  }

  getState() {
    return this.state;
  }

  setState(updates) {
    this.state = { ...this.state, ...updates };
    this.notify();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    for (const listener of this.listeners) {
      try {
        listener(this.state);
      } catch (err) {
        console.error('State subscriber error:', err);
      }
    }
  }

  getSelectedGoal() {
    return this.state.goals.find(g => g.id === this.state.selectedGoalId) || null;
  }
}

export const store = new StateStore();
