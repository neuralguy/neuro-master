import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

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

/**
 * Read deep-link params from URL (?tab=image, ?tab=video, ?page=profile, etc.)
 * and return the initial route the app should navigate to.
 */
function getInitialRoute(): string {
  const params = new URLSearchParams(window.location.search);

  const page = params.get('page');
  if (page === 'profile') {
    return '/profile';
  }
  if (page === 'gallery') {
    return '/gallery';
  }
  if (page === 'balance') {
    return '/balance';
  }

  const tab = params.get('tab');
  if (tab === 'video') {
    return '/generate?type=video';
  }

  // По умолчанию — генерация изображений
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

  if (error) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-tg-bg z-50 p-4">
        <div className="text-center">
          <p className="text-lg font-semibold text-tg-text mb-2">Ошибка авторизации</p>
          <p className="text-sm text-tg-hint mb-4">{error}</p>
          <p className="text-xs text-tg-hint">
            Попробуйте открыть приложение заново из бота
          </p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Main App Routes */}
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to={initialRoute} replace />} />
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

