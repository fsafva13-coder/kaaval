import { useEffect, useState } from "react";
import { owner } from "../api.js";

const STATE_STYLE = {
  trusted: "bg-emerald-50 text-emerald-700",
  caution: "bg-amber-50 text-amber-700",
  challenged: "bg-orange-100 text-orange-800",
  blocked: "bg-red-100 text-red-800",
};

export default function Owner() {
  const [pass, setPass] = useState("");
  const [authed, setAuthed] = useState(false);
  const [error, setError] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [senders, setSenders] = useState([]);
  const [budget, setBudget] = useState(null);

  async function load(p = pass) {
    const [a, s, b] = await Promise.all([owner("alerts", p), owner("senders", p), owner("budget", p)]);
    setAlerts(a);
    setSenders(s);
    setBudget(b);
  }

  async function login(e) {
    e.preventDefault();
    try {
      await load(pass);
      setAuthed(true);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    if (!authed) return;
    const t = setInterval(() => load().catch(() => {}), 3000);
    return () => clearInterval(t);
  }, [authed]);

  async function unblock(senderId) {
    await owner("unblock", pass, { method: "POST", body: JSON.stringify({ sender_id: senderId }) });
    load();
  }

  if (!authed) {
    return (
      <form onSubmit={login} className="min-h-screen flex flex-col items-center justify-center gap-3 px-6">
        <h1 className="font-serif text-3xl text-rose-dark">Kaaval · Owner</h1>
        <input type="password" value={pass} onChange={(e) => setPass(e.target.value)} placeholder="Owner passcode"
          className="rounded-lg border border-blush bg-white px-4 py-2 text-sm w-64" />
        <button className="rounded-lg bg-rose-dark text-white px-4 py-2 text-sm">Open dashboard</button>
        {error && <p className="text-sm text-red-700">{error}</p>}
      </form>
    );
  }

  const open = alerts.filter((a) => !a.resolved);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="font-serif text-3xl text-rose-dark">Kaaval · Owner dashboard</h1>
          <p className="text-sm text-ink/60">mirae.luxe_ assistant · updates every 3 seconds</p>
        </div>
        {budget && <Budget b={budget} />}
      </header>

      <section>
        <h2 className="font-semibold mb-3">Fraud alerts ({open.length})</h2>
        {open.length === 0 && <p className="text-sm text-ink/50">No active alerts. Every customer is being served.</p>}
        <div className="space-y-4">
          {open.map((a) => (
            <article key={a.id} className="rounded-xl border border-red-200 bg-white p-5">
              <div className="flex justify-between gap-4 flex-wrap">
                <div>
                  <p className="text-xs uppercase tracking-wider text-red-700 font-semibold">Blocked · {a.sender_id}</p>
                  <p className="mt-2 text-sm">{a.verdict.explanation_en}</p>
                  <p className="mt-1 text-sm text-ink/70" lang="ml">{a.verdict.explanation_ml}</p>
                </div>
                <button onClick={() => unblock(a.sender_id)}
                  className="h-fit rounded-lg border border-ink/20 px-3 py-1.5 text-sm hover:bg-ink/5">
                  Unblock
                </button>
              </div>
              <div className="mt-4">
                <p className="text-xs font-semibold text-ink/60 mb-1">Evidence</p>
                <ul className="space-y-1">
                  {(a.verdict.evidence || []).map((e, i) => {
                    const ev = typeof e === "string" ? { quote: e } : e;
                    return (
                      <li key={i} className="text-sm bg-red-50 border-l-2 border-red-400 px-3 py-1.5">
                        <span>“{ev.quote}”</span>
                        {ev.language && ev.language !== "english" && (
                          <span className="ml-2 rounded-full bg-white border border-red-200 px-2 py-0.5 text-[11px] text-red-800 align-middle">
                            {ev.language}
                          </span>
                        )}
                        {ev.english && (
                          <p className="mt-0.5 text-xs text-ink/60">
                            {ev.english_kind === "translation" ? "In English: " : "What it asks: "}
                            {ev.english}
                          </p>
                        )}
                      </li>
                    );
                  })}
                </ul>
                {a.verdict.tactics?.length > 0 && (
                  <p className="mt-3 text-xs text-ink/60">Signals: {a.verdict.tactics.join(", ")}</p>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2 className="font-semibold mb-3">Customers</h2>
        <div className="overflow-x-auto rounded-xl border border-blush bg-white">
          <table className="w-full text-sm">
            <thead className="text-left text-ink/60 border-b border-blush">
              <tr><th className="p-3">Sender</th><th className="p-3">Trust state</th><th className="p-3">Refusals</th><th className="p-3">Signals</th></tr>
            </thead>
            <tbody>
              {senders.map((s) => (
                <tr key={s.sender_id} className="border-b border-blush/50 last:border-0">
                  <td className="p-3 font-mono text-xs">{s.sender_id}</td>
                  <td className="p-3"><span className={`rounded-full px-2.5 py-0.5 text-xs ${STATE_STYLE[s.state]}`}>{s.state}</span></td>
                  <td className="p-3">{s.refusals}</td>
                  <td className="p-3 text-xs text-ink/60">{JSON.parse(s.signals).join(", ") || "none"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Budget({ b }) {
  const pct = Math.min(100, (b.spent_usd / b.cap_usd) * 100);
  return (
    <div className="w-64">
      <div className="flex justify-between text-xs text-ink/60">
        <span>Credits used{b.mock ? " (mock mode)" : ""}</span>
        <span>${b.spent_usd.toFixed(2)} / ${b.cap_usd}</span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-blush">
        <div className={`h-2 rounded-full ${b.paused ? "bg-red-600" : b.warning ? "bg-amber-500" : "bg-rose"}`} style={{ width: `${pct}%` }} />
      </div>
      {b.warning && <p className="mt-1 text-xs text-amber-700">{b.paused ? "Paused: cap reached" : "Warning: nearing cap"}</p>}
    </div>
  );
}
