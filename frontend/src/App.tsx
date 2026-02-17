import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

import { AppLayout } from '@/components/layout/AppLayout';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Loader } from '@/components/ui/Loader';

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

function getInitialRoute(): string {
  const params = new URLSearchParams(window.location.search);

  const page = params.get('page');
  if (page === 'profile') return '/profile';
  if (page === 'gallery') return '/gallery';
  if (page === 'balance') return '/balance';

  const tab = params.get('tab');
  if (tab === 'video') return '/generate?type=video';

  return '/generate?type=image';
}

const AppContent = () => {
  const { isReady } = useTelegram();
  const { user, isLoading, error } = useUser();
  const [initialRoute] = useState(() => getInitialRoute());

  if (!isReady) {
    return <Loader fullScreen text="Загрузка..." />;
  }

  if (isLoading) {
    return <Loader fullScreen text="Авторизация..." />;
  }

  if (error || !user) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-tg-bg z-50 p-6">
        <div className="text-center max-w-sm">
          <p className="text-lg font-semibold text-tg-text mb-2">
            Не удалось авторизоваться
          </p>
          <p className="text-sm text-tg-hint mb-4">
            {error || 'Нет данных пользователя'}
          </p>
          <p className="text-xs text-tg-hint">
            Попробуйте написать /start боту и открыть приложение заново
          </p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to={initialRoute} replace />} />
        <Route path="generate" element={<GeneratePage />} />
        <Route path="gallery" element={<GalleryPage />} />
        <Route path="balance" element={<BalancePage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>

      {user?.is_admin && (
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="models" element={<ModelsPage />} />
          <Route path="logs" element={<LogsPage />} />
        </Route>
      )}

      <Route path="*" element={<Navigate to="/generate" replace />} />
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

