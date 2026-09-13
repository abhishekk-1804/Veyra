export const GoalStatus = {
  ACTIVE: "ACTIVE",
  COMPLETED: "COMPLETED",
  PAUSED: "PAUSED",
  ARCHIVED: "ARCHIVED",
} as const;
export type GoalStatus = (typeof GoalStatus)[keyof typeof GoalStatus];

export const GoalPriority = {
  LOW: "LOW",
  MEDIUM: "MEDIUM",
  HIGH: "HIGH",
  CRITICAL: "CRITICAL",
} as const;
export type GoalPriority = (typeof GoalPriority)[keyof typeof GoalPriority];

export interface Goal {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  status: GoalStatus;
  priority: GoalPriority;
  target_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface GoalInput {
  title: string;
  description?: string;
  status?: GoalStatus;
  priority?: GoalPriority;
  target_date?: string;
}

export interface GoalPatch {
  title?: string;
  description?: string;
  status?: GoalStatus;
  priority?: GoalPriority;
  target_date?: string;
}

export const STATUS_ORDER: GoalStatus[] = [
  GoalStatus.ACTIVE,
  GoalStatus.COMPLETED,
  GoalStatus.PAUSED,
  GoalStatus.ARCHIVED,
];

export const PRIORITY_ORDER: GoalPriority[] = [
  GoalPriority.LOW,
  GoalPriority.MEDIUM,
  GoalPriority.HIGH,
  GoalPriority.CRITICAL,
];