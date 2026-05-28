import { Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from './layout/AppLayout';
import { CompareRunsPage } from './pages/CompareRunsPage';
import { DashboardPage } from './pages/DashboardPage';
import { ResultsBrowserPage } from './pages/ResultsBrowserPage';

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/results" element={<ResultsBrowserPage />} />
        <Route path="/compare" element={<CompareRunsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
