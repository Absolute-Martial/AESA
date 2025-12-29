export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-primary mb-4">
          AESA
        </h1>
        <p className="text-xl text-text-muted mb-8">
          AI Engineering Study Assistant
        </p>
        <div className="glass-panel p-6 max-w-md">
          <p className="text-text-main">
            Your intelligent scheduling companion for KU Engineering studies.
          </p>
        </div>
      </div>
    </main>
  );
}
