import { NavLink, Outlet } from 'react-router-dom';

export function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-kicker">Blockchain IoT Trust Lab</div>
          <h1>Simulation Console</h1>
          <p>Live trust analytics, run replay, and result comparison for trust-aware consensus experiments.</p>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Live Dashboard
          </NavLink>
          <NavLink to="/results" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Results Browser
          </NavLink>
          <NavLink to="/compare" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Compare Runs
          </NavLink>
        </nav>
      </aside>
      <main className="content-shell">
        <Outlet />
      </main>
    </div>
  );
}
