import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { apiClient } from "../api/client";
const groups = [
  {
    label: "Part I — Workspace",
    items: [
      { label: "Live simulation", to: "/" },
      { label: "Metrics explorer", to: "/metrics" },
      { label: "Attack laboratory", to: "/attack-lab" },
      { label: "Scenario library", to: "/scenarios" },
    ],
  },
  {
    label: "Part II — Research",
    items: [
      { label: "Experiment results", to: "/experiments" },
      { label: "Compare runs", to: "/compare" },
      { label: "System architecture", to: "/explainer" },
      { label: "Export & present", to: "/export" },
    ],
  },
];
export function Sidebar() {
  const [online, setOnline] = useState<boolean | null>(null);
  useEffect(() => {
    let active = true;
    const check = async () => {
      try {
        const { data } = await apiClient.get("/health");
        if (active) setOnline(data.status === "ok");
      } catch {
        if (active) setOnline(false);
      }
    };
    void check();
    const timer = setInterval(check, 15000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);
  return (
    <aside className="sidebar">
      <NavLink to="/" className="brand" aria-label="TDCB research workspace">
        <span>
          <strong>TDCB Laboratory</strong>
          <small>Notebook on trust &amp; consensus</small>
        </span>
      </NavLink>
      <nav aria-label="Main navigation">
        {groups.map((group) => (
          <div className="nav-group" key={group.label}>
            <div className="nav-label">{group.label}</div>
            {group.items.map(({ label, to }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `nav-item${isActive ? " active" : ""}`
                }
                title={label}
              >
                <span>{label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <NavLink to="/explainer" className="research-note">
          <span>
            Understand the model<small>Architecture & methodology</small>
          </span>
        </NavLink>
        <div className="api-status" role="status">
          <span
            className={`status-dot ${online === true ? "online" : online === false ? "offline" : ""}`}
          />
          <span>
            {online === null
              ? "Connecting to engine"
              : online
                ? "Simulation engine online"
                : "Engine unavailable"}
          </span>
        </div>
      </div>
    </aside>
  );
}
