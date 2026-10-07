import { Navigate, Route, Routes } from 'react-router-dom';
import StudentLayout from '@/layouts/StudentLayout';
import AdminLayout from '@/layouts/AdminLayout';
import Login from '@/pages/Login';
import Teaching from '@/pages/student/Teaching';
import PracticeSetup from '@/pages/student/PracticeSetup';
import PracticeRunner from '@/pages/student/PracticeRunner';
import Report from '@/pages/student/Report';
import Settings from '@/pages/student/Settings';
import Cards from '@/pages/student/Cards';
import KnowledgePage from '@/pages/admin/KnowledgePage';
import QuestionsPage from '@/pages/admin/QuestionsPage';
import StudentsPage from '@/pages/admin/StudentsPage';
import DatabasePage from '@/pages/admin/DatabasePage';
import NotFound from '@/pages/NotFound';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<StudentLayout />}>
        <Route index element={<Navigate to="/teaching" replace />} />
        <Route path="/home" element={<Navigate to="/teaching" replace />} />
        <Route path="/teaching" element={<Teaching />} />
        <Route path="/teaching/:sessionId" element={<Teaching />} />
        <Route path="/practice" element={<Navigate to="/practice/new" replace />} />
        <Route path="/practice/new" element={<PracticeSetup />} />
        <Route path="/practice/:sessionId" element={<PracticeRunner />} />
        <Route path="/report" element={<Report />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/cards" element={<Cards />} />
      </Route>

      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="/admin/knowledge" replace />} />
        <Route path="knowledge" element={<KnowledgePage />} />
        <Route path="questions" element={<QuestionsPage />} />
        <Route path="students" element={<StudentsPage />} />
        <Route path="db" element={<DatabasePage />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
