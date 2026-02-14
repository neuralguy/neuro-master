import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { AppLayout } from '@/components/layout/AppLayout';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Loader } from '@/components/ui/Loader';

import { HomePage } from '@/pages/app/HomePage';
import GeneratePage from '@/pages/app/GeneratePage';
import { GalleryPage } from '@/pages/app/GalleryPage';
import { BalancePage } from '@/pages/app/BalancePage';
import { ProfilePage } from '@/pages/app/ProfilePage';

import { DashboardPage } from '@/pages/admin/DashboardPage';
import { UsersPage } from '@/pages/admin/UsersPage';
import { ModelsPage } from '@/pages/admin/ModelsPage';
import { LogsPage } from '@/pages/admin/LogsPage';

import { useTelegram } from '@/hooks/useTelegram';
import { useUser } from '@/hooks/useUser';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const AppContent = () => {
  const { isReady } = useTelegram();
  const { user, isLoading } = useUser();

  if (!isReady || isLoading) {
    return <Loader fullScreen text="Загрузка..." />;
  }

  return (
    <Routes>
      {/* Main App Routes */}
      <Route path="/" element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="generate" element={<GeneratePage />} />
        <Route path="gallery" element={<GalleryPage />} />
        <Route path="balance" element={<BalancePage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>

      {/* Admin Routes */}
      {user?.is_admin && (
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="models" element={<ModelsPage />} />
          <Route path="logs" element={<LogsPage />} />
        </Route>
      )}

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
