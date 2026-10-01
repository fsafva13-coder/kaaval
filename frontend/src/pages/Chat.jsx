import { useEffect, useRef, useState } from "react";
import BlockedScreen from "../components/BlockedScreen.jsx";
import { chatStatus, newIdentity, sendMessage } from "../api.js";

const WELCOME = { role: "assistant", text: "Welcome to mirae.luxe_ 🌸 How can I help you today?" };

export default function Chat() {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [blocked, setBlocked] = useState(null);
  const [notice, setNotice] = useState(null);
  const endRef = useRef(null);

  useEffect(() => {
    chatStatus().then((r) => {
      if (r.status === 403) setBlocked(r.message);
      else if (r.history?.length) setMessages([WELCOME, ...r.history.map((m) => ({ role: m.role, text: m.text }))]);
    }).catch(() => setNotice("Can't reach the server. Is the backend running?"));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function submit(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setBusy(true);
    try {
      const r = await sendMessage(text);
      if (r.status === 403) return setBlocked(r.message);
      if (r.status === 429 || r.status === 503) return setNotice(r.message);
      setMessages((m) => [...m, { role: "assistant", text: r.reply }]);
    } catch {
      setNotice("Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  if (blocked) return <BlockedScreen message={blocked} />;

  return (
    <div className="min-h-screen flex flex-col max-w-2xl mx-auto">
      <header className="px-6 pt-8 pb-5 border-b border-gold/30 text-center">
        <h1 className="font-serif text-4xl tracking-wide text-rose-dark">mirae.luxe_</h1>
        <p className="mt-1 text-xs uppercase tracking-[0.25em] text-gold">Bouquets · Gift hampers · Dubai</p>
        <p className="mt-3 text-xs text-ink/50">Assistant protected by Kaaval</p>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-6 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                m.role === "user" ? "bg-rose text-white rounded-br-sm" : "bg-white border border-blush rounded-bl-sm"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {busy && <div className="text-xs text-ink/40 px-2">typing…</div>}
        {notice && <div className="text-center text-sm text-rose-dark bg-blush/60 rounded-lg py-2">{notice}</div>}
        <div ref={endRef} />
      </main>

      <form onSubmit={submit} className="p-4 border-t border-gold/30 flex gap-2 bg-ivory sticky bottom-0">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type in English, Manglish, Arabizi…"
          className="flex-1 rounded-full border border-blush bg-white px-4 py-2.5 text-sm outline-none focus:border-rose"
        />
        <button disabled={busy} className="rounded-full bg-rose-dark text-white px-5 text-sm font-medium disabled:opacity-50">
          Send
        </button>
      </form>
      <button
        onClick={() => { newIdentity(); window.location.reload(); }}
        className="text-[11px] text-ink/30 pb-3 hover:text-ink/60"
        title="Demo only: start over as a different customer"
      >
        demo: new customer
      </button>
    </div>
  );
}
