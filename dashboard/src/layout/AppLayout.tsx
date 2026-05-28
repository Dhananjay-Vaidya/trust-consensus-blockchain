import { Outlet } from 'react-router-dom';

import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export function AppLayout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-base)' }}>
      <Sidebar />
      <div style={{
        marginLeft: 'var(--sidebar-w)',
        flex: 1, minWidth: 0,
        display: 'flex', flexDirection: 'column',
      }}>
        <TopBar />
        <main style={{
          flex: 1, padding: 20,
          marginTop: 'var(--topbar-h)',
          overflowY: 'auto', overflowX: 'hidden',
        }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
