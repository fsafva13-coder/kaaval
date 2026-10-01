// Stable IDs for this browser. Blocks are enforced on the server by both IDs.
function stableId(key, prefix) {
  try {
    let v = localStorage.getItem(key);
    if (!v) {
      v = `${prefix}-${crypto.randomUUID().slice(0, 12)}`;
      localStorage.setItem(key, v);
    }
    return v;
  } catch {
    return `${prefix}-${crypto.randomUUID().slice(0, 12)}`;
  }
}

export const senderId = () => stableId("kaaval_sender", "s");
export const deviceId = () => stableId("kaaval_device", "d");

// Demo helper: a "new customer" in a new tab without clearing storage.
export function newIdentity() {
  try {
    localStorage.removeItem("kaaval_sender");
    localStorage.removeItem("kaaval_device");
  } catch {}
}

export async function sendMessage(text) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sender_id: senderId(), device_id: deviceId(), text }),
  });
  const body = await res.json();
  return { status: res.status, ...body };
}

export async function chatStatus() {
  const res = await fetch(
    `/api/chat/status?sender_id=${encodeURIComponent(senderId())}&device_id=${encodeURIComponent(deviceId())}`
  );
  const body = await res.json();
  return { status: res.status, ...body };
}

export async function owner(path, passcode, options = {}) {
  const res = await fetch(`/api/owner/${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", "X-Owner-Passcode": passcode, ...(options.headers || {}) },
  });
  if (!res.ok) throw new Error(res.status === 401 ? "Wrong passcode" : `Error ${res.status}`);
  return res.json();
}
