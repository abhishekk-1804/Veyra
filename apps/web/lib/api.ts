import type { Goal, GoalInput, GoalPatch } from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string | Array<unknown> };
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(res.status, detail);
  }

  return (await res.json()) as T;
}

export async function listGoals(): Promise<Goal[]> {
  return request<Goal[]>("/goals");
}

export async function getGoal(id: string): Promise<Goal> {
  return request<Goal>(`/goals/${id}`);
}

export async function createGoal(input: GoalInput): Promise<Goal> {
  return request<Goal>("/goals", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function updateGoal(
  id: string,
  patch: GoalPatch,
): Promise<Goal> {
  return request<Goal>(`/goals/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}