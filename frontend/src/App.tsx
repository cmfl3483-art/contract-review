import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ConfigProvider, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { lazy, Suspense, useEffect } from 'react';
import { queryClient } from './config/queryClient';
import MainLayout from './layouts/MainLayout';
import ErrorBoundary from './components/ErrorBoundary';
import axios from 'axios';
import { API_BASE_URL } from './config/api';
import { useUserStore } from './stores/useUserStore';
import './App.css';

// Lazy load pages for code splitting
const ContractBoard = lazy(() => import('./pages/ContractBoard'));
const ComplianceListPage = lazy(() => import('./pages/Compliance/ComplianceListPage'));
const ComplianceCheckNewPage = lazy(() => import('./pages/Compliance/ComplianceCheckNewPage'));
const ComplianceCheckDetailPage = lazy(() => import('./pages/Compliance/ComplianceCheckDetailPage'));
const RuleSetListPage = lazy(() => import('./pages/Compliance/admin/RuleSetListPage'));
const RuleSetDetailPage = lazy(() => import('./pages/Compliance/admin/RuleSetDetailPage'));

// Loading component for Suspense fallback
const PageLoader = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '100vh' 
  }}>
    <Spin size="large" tip="加载中..." />
  </div>
);

function App() {
  useEffect(() => {
    // Check if user is logged in from localStorage (set by callback page)
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    
    if (token && userStr) {
      try {
        // Parse user data and update store
        const user = JSON.parse(userStr);
        const { setToken, setCurrentUser } = useUserStore.getState();
        setToken(token);
        setCurrentUser(user);
        
        // Clean up old localStorage keys (they're now in zustand store)
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      } catch (error) {
        console.error('Failed to parse user data:', error);
        // Clear invalid data
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    
    // Check if user is logged in from store
    const storeToken = useUserStore.getState().token;
    
    if (!storeToken && !token) {
      // No token, redirect to DingTalk login
      const redirectToLogin = async () => {
        try {
          const response = await axios.get(`${API_BASE_URL}/api/auth/dingtalk/login`);
          if (response.data?.success && response.data?.data?.authUrl) {
            window.location.href = response.data.data.authUrl;
          }
        } catch (error) {
          console.error('Failed to get login URL:', error);
        }
      };
      
      redirectToLogin();
    }
  }, []);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider locale={zhCN}>
          <Router>
            <MainLayout>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/" element={<ContractBoard />} />
                  <Route path="/compliance" element={<ComplianceListPage />} />
                  <Route path="/compliance/check/new" element={<ComplianceCheckNewPage />} />
                  <Route path="/compliance/check/:checkId" element={<ComplianceCheckDetailPage />} />
                  <Route path="/compliance/admin/rule-sets" element={<RuleSetListPage />} />
                  <Route path="/compliance/admin/rule-sets/:ruleSetId" element={<RuleSetDetailPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
            </MainLayout>
          </Router>
        </ConfigProvider>
        {/* React Query Devtools - 仅在开发环境显示 */}
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
