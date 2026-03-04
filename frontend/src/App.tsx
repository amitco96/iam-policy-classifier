import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ClassifyPage from './pages/ClassifyPage';
import BatchPage from './pages/BatchPage';
import HistoryPage from './pages/HistoryPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 overflow-auto bg-slate-50">
          <Routes>
            <Route path="/" element={<ClassifyPage />} />
            <Route path="/batch" element={<BatchPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
