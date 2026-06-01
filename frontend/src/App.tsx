import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import MainLayout from './layouts/MainLayout';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import ChatPage from './pages/ChatPage';
import InterviewResult from './pages/InterviewResult';
import ProfilePage from './pages/ProfilePage';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';
import ErrorBoundary from './components/ErrorBoundary';
import AdminInterviewTypes from './pages/admin/AdminInterviewTypes';
import AdminQuestions from './pages/admin/AdminQuestions';
import AdminGenerationJobs from './pages/admin/AdminGenerationJobs';

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <MainLayout>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Protected Routes */}
              <Route element={<ProtectedRoute />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/interviews/:id" element={<ChatPage />} />
                <Route path="/interviews/:id/result" element={<InterviewResult />} />
                <Route element={<AdminRoute />}>
                  <Route path="/admin/interview-types" element={<AdminInterviewTypes />} />
                  <Route path="/admin/questions" element={<AdminQuestions />} />
                  <Route path="/admin/question-generation-jobs" element={<AdminGenerationJobs />} />
                </Route>
                {/* Redirect legacy or unknown routes to dashboard if logged in, else landing */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Routes>
          </MainLayout>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
