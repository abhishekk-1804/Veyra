/**
 * Veyra AI Planner Controller
 * Implements the core invariant: AI Proposes, User Decides.
 */

import { store } from './state.js';
import { api } from './api.js';
import { escapeHtml, formatMinutes, formatDate, showToast } from './ui.js';

export function renderPlanner() {
  const container = document.getElementById('planner-view');
  if (!container) return;

  const { goals, selectedGoalId, activeProposal } = store.getState();
  const activeGoal = store.getSelectedGoal();

  container.innerHTML = `
    <div class="planner-container">
      <div class="planner-hero">
        <h1 class="hero-title">AI Intent Decomposition</h1>
        <p class="hero-subtitle">Propose structured task plans using verified AI synthesis. You retain complete authority.</p>
      </div>

      <div class="invariant-banner">
        <div class="invariant-icon">🤖</div>
        <div class="invariant-text">
          <strong>Reviewable Guarantee:</strong> The AI proposes tasks. No database records or execution states are mutated until you explicitly approve.
        </div>
      </div>

      <div class="planner-input-card">
        <div class="form-group">
          <label class="form-label" for="planner-goal-select">Target Goal *</label>
          <select id="planner-goal-select">
            ${goals.length === 0 ? '<option value="">No goals available</option>' : ''}
            ${goals.map(g => `
              <option value="${g.id}" ${g.id === selectedGoalId ? 'selected' : ''}>
                ${escapeHtml(g.title)}
              </option>
            `).join('')}
          </select>
        </div>

        <div class="form-group">
          <label class="form-label" for="planner-intent-input">Intent & Guidance *</label>
          <textarea
            id="planner-intent-input"
            class="intent-textarea"
            placeholder="Describe what you want to achieve (e.g., 'Break down this goal into high-priority architectural milestones and database models')"
          >Break down this goal into actionable implementation tasks with estimates and priorities.</textarea>
          <span class="form-hint">The AI will produce a bounded proposal (max 15 tasks, max 80 hours total effort).</span>
        </div>

        <div class="planner-actions">
          <span style="font-size: 0.8rem; color: var(--text-muted); font-family: var(--font-mono);">
            Status: Deterministic validation enabled
          </span>
          <button class="btn btn-primary" id="generate-proposal-btn" ${goals.length === 0 ? 'disabled' : ''}>
            ✨ Generate Plan Proposal
          </button>
        </div>
      </div>

      <!-- Proposal Container -->
      <div id="proposal-output-area">
        ${renderProposalCard(activeProposal)}
      </div>
    </div>
  `;

  // Goal select change
  const goalSelect = document.getElementById('planner-goal-select');
  if (goalSelect) {
    goalSelect.onchange = (e) => {
      store.setState({ selectedGoalId: e.target.value });
    };
  }

  // Generate proposal button
  const genBtn = document.getElementById('generate-proposal-btn');
  if (genBtn) {
    genBtn.onclick = async () => {
      const goalId = document.getElementById('planner-goal-select').value;
      const prompt = document.getElementById('planner-intent-input').value.trim();

      if (!goalId) {
        showToast('Please select a goal first', 'error');
        return;
      }
      if (!prompt) {
        showToast('Please enter an intent prompt', 'error');
        return;
      }

      genBtn.disabled = true;
      genBtn.textContent = 'Generating proposal...';

      try {
        const proposal = await api.generatePlan(goalId, prompt);
        store.setState({ activeProposal: proposal });
        showToast('Plan proposal generated for review', 'success');
        renderPlanner();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        genBtn.disabled = false;
        genBtn.textContent = '✨ Generate Plan Proposal';
      }
    };
  }

  bindProposalActions();
}

function renderProposalCard(proposal) {
  if (!proposal) {
    return `
      <div class="empty-state">
        <div class="empty-icon">💡</div>
        <div class="empty-title">No Active Proposal</div>
        <div class="empty-desc">Formulate your intent above and generate a plan proposal to review.</div>
      </div>
    `;
  }

  const payload = proposal.proposal || {};
  const tasks = payload.tasks || [];
  const summary = payload.summary || 'Proposed task breakdown for target objective.';
  const totalMins = tasks.reduce((sum, t) => sum + (t.estimated_minutes || 0), 0);
  const status = proposal.status;

  return `
    <div class="proposal-card ${status.toLowerCase()}">
      <div class="proposal-banner">
        <div class="proposal-banner-text">
          <strong>AI Plan Proposal</strong> • ID: <span style="font-family: var(--font-mono);">${proposal.id.substring(0, 8)}...</span>
        </div>
        <span class="badge badge-${status.toLowerCase()}">${status}</span>
      </div>

      <div class="proposal-summary">
        ${escapeHtml(summary)}
      </div>

      <div style="overflow-x: auto;">
        <table class="proposed-tasks-table">
          <thead>
            <tr>
              <th style="width: 45%;">Task Title & Details</th>
              <th style="width: 15%;">Priority</th>
              <th style="width: 20%;">Estimate</th>
              <th style="width: 20%;">Due Date</th>
            </tr>
          </thead>
          <tbody>
            ${tasks.map(t => `
              <tr>
                <td>
                  <div class="proposed-task-title">${escapeHtml(t.title)}</div>
                  ${t.notes ? `<div class="proposed-task-notes">${escapeHtml(t.notes)}</div>` : ''}
                </td>
                <td>
                  <span class="badge badge-${(t.priority || 'medium').toLowerCase()}">${t.priority || 'MEDIUM'}</span>
                </td>
                <td style="font-family: var(--font-mono); font-size: 0.8rem;">
                  ${formatMinutes(t.estimated_minutes)}
                </td>
                <td style="font-family: var(--font-mono); font-size: 0.8rem;">
                  ${formatDate(t.due_date)}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

      <div class="proposal-footer">
        <div class="proposal-meta-stats">
          Total: ${tasks.length} proposed tasks (${formatMinutes(totalMins)} planned)
        </div>
        <div class="proposal-decision-btns">
          ${status === 'PENDING' ? `
            <button class="btn btn-danger btn-sm" id="reject-proposal-btn" data-id="${proposal.id}">
              Reject Proposal
            </button>
            <button class="btn btn-success btn-sm" id="approve-proposal-btn" data-id="${proposal.id}">
              ✓ Approve & Create Tasks
            </button>
          ` : status === 'ACCEPTED' ? `
            <span style="font-size: 0.85rem; color: var(--accent-emerald); font-weight: 600;">
              ✓ Approved & Persisted to Workspace
            </span>
          ` : `
            <span style="font-size: 0.85rem; color: var(--accent-rose); font-weight: 600;">
              ✗ Proposal Rejected (0 tasks created)
            </span>
          `}
        </div>
      </div>
    </div>
  `;
}

function bindProposalActions() {
  const approveBtn = document.getElementById('approve-proposal-btn');
  const rejectBtn = document.getElementById('reject-proposal-btn');

  if (approveBtn) {
    approveBtn.onclick = async () => {
      const id = approveBtn.getAttribute('data-id');
      approveBtn.disabled = true;
      approveBtn.textContent = 'Approving...';
      try {
        const createdTasks = await api.approveProposal(id);
        showToast(`Approved! Created ${createdTasks.length} tasks in workspace`, 'success');
        // Refresh proposal status
        const updatedProposal = await api.getProposal(id);
        store.setState({ activeProposal: updatedProposal });
        renderPlanner();
      } catch (err) {
        showToast(err.message, 'error');
        approveBtn.disabled = false;
        approveBtn.textContent = '✓ Approve & Create Tasks';
      }
    };
  }

  if (rejectBtn) {
    rejectBtn.onclick = async () => {
      const id = rejectBtn.getAttribute('data-id');
      rejectBtn.disabled = true;
      rejectBtn.textContent = 'Rejecting...';
      try {
        await api.rejectProposal(id);
        showToast('Proposal rejected. Zero tasks were created in your workspace.', 'info');
        const updatedProposal = await api.getProposal(id);
        store.setState({ activeProposal: updatedProposal });
        renderPlanner();
      } catch (err) {
        showToast(err.message, 'error');
        rejectBtn.disabled = false;
        rejectBtn.textContent = 'Reject Proposal';
      }
    };
  }
}
