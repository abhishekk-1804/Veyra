import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-full flex-1 items-center justify-center bg-zinc-50 dark:bg-black">
      <main className="flex max-w-lg flex-col items-start gap-6 px-8 py-16">
        <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
          Veyra
        </p>
        <h1 className="text-3xl font-semibold leading-tight tracking-tight text-zinc-900 dark:text-zinc-50">
          Get things done, deliberately.
        </h1>
        <p className="text-lg leading-8 text-zinc-600 dark:text-zinc-400">
          An AI-native execution and productivity platform. Start by defining
          the goals you are working toward.
        </p>
        <Link
          href="/goals"
          className="rounded-full bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
        >
          Go to Goals
        </Link>
      </main>
    </div>
  );
}