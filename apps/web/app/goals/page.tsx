import type { Goal } from "@/lib/types";
import { listGoals } from "@/lib/api";
import GoalsClient from "./goals-client";

export const dynamic = "force-dynamic";

export default async function GoalsPage() {
  let initialGoals: Goal[] = [];
  try {
    initialGoals = await listGoals();
  } catch {
    // If the API is unreachable, render the empty state; the client reports errors.
  }

  return <GoalsClient initialGoals={initialGoals} />;
}