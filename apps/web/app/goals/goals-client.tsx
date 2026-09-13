"use client";

import { useMemo, useState } from "react";

import { createGoal, updateGoal } from "@/lib/api";
import {
  GoalPriority,
  GoalStatus,
  PRIORITY_ORDER,
  STATUS_ORDER,
  type Goal,
} from "@/lib/types";

const STATUS_STYLES: Record<GoalStatus, string> = {
  ACTIVE: "bg-emerald-100 text-emerald-800",
  COMPLETED: "bg-zinc-200 text-zinc-700",
  PAUSED: "bg-amber-100 text-amber-800",
  ARCHIVED: "bg-zinc-300 text-zinc-600",
};

const PRIORITY_DOT: Record<GoalPriority, string> = {
  LOW: "bg-zinc-300",
  MEDIUM: "bg-sky-400",
  HIGH: "bg-amber-400",
  CRITICAL: "bg-rose-500",
};

export default function GoalsClient({
  initialGoals,
}: {
  initialGoals: Goal[];
}) {
  const [goals, setGoals] = useState<Goal[]>(initialGoals);

  // create form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<GoalPriority>(GoalPriority.MEDIUM);
  const [targetDate, setTargetDate] = useState("");
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // detail state
  const [selected, setSelected] = useState<Goal | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!title.trim()) {
      setFormError("Title is required.");
      return;
    }
    setCreating(true);
    try {
      const goal = await createGoal({
        title,
        description: description.trim() ? description.trim() : undefined,
        priority,
        target_date: targetDate || undefined,
      });
      setGoals((prev) => [goal, ...prev]);
      setTitle("");
      setDescription("");
      setPriority(GoalPriority.MEDIUM);
      setTargetDate("");
      setSelected(goal);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not create goal");
    } finally {
      setCreating(false);
    }
  };

  const handleStatusChange = async (goal: Goal, status: GoalStatus) => {
    try {
      const updated = await updateGoal(goal.id, { status });
      setGoals((prev) => prev.map((g) => (g.id === goal.id ? updated : g)));
      setSelected(updated);
    } catch {
      // surface silently; state remains consistent on next load
    }
  };

  const ordered = useMemo(
    () =>
      [...goals].sort((a, b) => {
        const statusDiff =
          STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status);
        if (statusDiff !== 0) return statusDiff;
        return (
          PRIORITY_ORDER.indexOf(b.priority) - PRIORITY_ORDER.indexOf(a.priority)
        );
      }),
    [goals],
  );

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 p-6 sm:p-10">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Goals</h1>
        <p className="text-sm text-zinc-500">
          The outcomes you are working toward.
        </p>
      </header>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="flex flex-col gap-6">
          <form
            onSubmit={handleCreate}
            className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm"
          >
            <h2 className="mb-4 text-sm font-medium text-zinc-700">
              New goal
            </h2>
            <div className="flex flex-col gap-3">
              <label className="flex flex-col gap-1">
                <span className="text-xs font-medium text-zinc-500">
                  Title *
                </span>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  maxLength={120}
                  placeholder="e.g. Launch Veyra 1.0"
                  className="rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-xs font-medium text-zinc-500">
                  Description
                </span>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  placeholder="Optional notes about this goal"
                  className="resize-none rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                />
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-zinc-500">
                    Priority
                  </span>
                  <select
                    value={priority}
                    onChange={(e) =>
                      setPriority(e.target.value as GoalPriority)
                    }
                    className="rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                  >
                    {PRIORITY_ORDER.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-zinc-500">
                    Target date
                  </span>
                  <input
                    type="date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                    className="rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                  />
                </label>
              </div>
              {formError && <p className="text-xs text-rose-600">{formError}</p>}
              <button
                type="submit"
                disabled={creating}
                className="mt-1 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50"
              >
                {creating ? "Creating…" : "Create goal"}
              </button>
            </div>
          </form>
        </div>

        <div className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-zinc-700">
            {goals.length} goal{goals.length === 1 ? "" : "s"}
          </h2>
          {goals.length === 0 && (
            <p className="rounded-lg border border-dashed border-zinc-300 p-6 text-center text-sm text-zinc-500">
              No goals yet. Create your first one.
            </p>
          )}
          {ordered.map((goal) => (
            <button
              key={goal.id}
              onClick={() => setSelected(goal)}
              className="flex items-start justify-between gap-3 rounded-xl border border-zinc-200 bg-white p-4 text-left shadow-sm transition-colors hover:border-zinc-400"
            >
              <div className="flex flex-col gap-1">
                <span className="font-medium text-zinc-900">{goal.title}</span>
                {goal.description && (
                  <span className="line-clamp-1 text-sm text-zinc-500">
                    {goal.description}
                  </span>
                )}
                {goal.target_date && (
                  <span className="text-xs text-zinc-400">
                    Target {goal.target_date}
                  </span>
                )}
              </div>
              <div className="flex shrink-0 flex-col items-end gap-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[goal.status]}`}
                >
                  {goal.status}
                </span>
                <span className="flex items-center gap-1 text-xs text-zinc-500">
                  <span
                    className={`h-2 w-2 rounded-full ${PRIORITY_DOT[goal.priority]}`}
                  />
                  {goal.priority}
                </span>
              </div>
            </button>
          ))}
        </div>
      </section>

      {selected && (
        <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">{selected.title}</h2>
              <p className="text-xs text-zinc-400">
                Created {new Date(selected.created_at).toLocaleString()}
              </p>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-sm text-zinc-400 hover:text-zinc-600"
              aria-label="Close"
            >
              Close
            </button>
          </div>
          <p className="text-sm text-zinc-600">
            {selected.description || "No description."}
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
            <label className="flex items-center gap-2">
              <span className="text-zinc-500">Status</span>
              <select
                value={selected.status}
                onChange={(e) =>
                  handleStatusChange(selected, e.target.value as GoalStatus)
                }
                className="rounded-lg border border-zinc-300 px-2 py-1 text-sm outline-none focus:border-zinc-500"
              >
                {STATUS_ORDER.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
            <span className="text-zinc-500">Priority: {selected.priority}</span>
            {selected.target_date && (
              <span className="text-zinc-500">
                Target: {selected.target_date}
              </span>
            )}
          </div>
        </section>
      )}
    </div>
  );
}