import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import {
  Graph,
  ChartLine,
  Flask,
  Stack,
  FolderOpen,
  Scales,
  Blueprint,
  Export,
  BookOpen,
} from "@phosphor-icons/react";
import { apiClient } from "../api/client";
const groups = [
  {
    label: "Workspace",
    items: [
      { icon: Graph, label: "Live simulation", to: "/" },
      { icon: ChartLine, label: "Metrics explorer", to: "/metrics" },
      { icon: Flask, label: "Attack laboratory", to: "/attack-lab" },
      { icon: Stack, label: "Scenario library", to: "/scenarios" },
    ],
  },
  {
    label: "Research",
    items: [
      { icon: FolderOpen, label: "Experiment results", to: "/experiments" },
      { icon: Scales, label: "Compare runs", to: "/compare" },
      { icon: Blueprint, label: "System architecture", to: "/explainer" },
      { icon: Export, label: "Export & present", to: "/export" },
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
        <span className="brand-mark">
          <Graph size={25} weight="bold" />
        </span>
        <span>
          <strong>
            TDCB<span className="brand-divider"> / </span>Lab
          </strong>
          <small>Trust & consensus research</small>
        </span>
      </NavLink>
      <nav aria-label="Main navigation">
        {groups.map((group) => (
          <div className="nav-group" key={group.label}>
            <div className="nav-label">{group.label}</div>
            {group.items.map(({ icon: Icon, label, to }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `nav-item${isActive ? " active" : ""}`
                }
                title={label}
              >
                <Icon size={19} />
                <span>{label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <NavLink to="/explainer" className="research-note">
          <BookOpen size={20} />
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
