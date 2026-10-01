// Shown only to a sender Kaaval has confirmed as fraud. Enforced server-side.
export default function BlockedScreen({ message }) {
  return (
    <div className="min-h-screen bg-alarm flex items-center justify-center px-6">
      <div className="max-w-md text-center">
        <svg viewBox="0 0 24 24" className="w-14 h-14 mx-auto text-alarm-ink" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
          <rect x="4" y="10" width="16" height="11" rx="2" />
          <path d="M8 10V7a4 4 0 0 1 8 0v3" />
        </svg>
        <h1 className="mt-6 text-3xl font-semibold text-alarm-ink">Access ended</h1>
        <p className="mt-3 text-alarm-ink/80">{message || "This conversation has been closed."}</p>
        <p className="mt-8 text-xs text-alarm-ink/60">Protected by Kaaval</p>
      </div>
    </div>
  );
}
