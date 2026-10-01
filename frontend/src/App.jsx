import { useEffect, useState } from "react";
import Chat from "./pages/Chat.jsx";
import Owner from "./pages/Owner.jsx";

// Tiny hash router: #/ = customer chat, #/owner = owner dashboard.
export default function App() {
  const [route, setRoute] = useState(window.location.hash);
  useEffect(() => {
    const onChange = () => setRoute(window.location.hash);
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route.startsWith("#/owner") ? <Owner /> : <Chat />;
}
