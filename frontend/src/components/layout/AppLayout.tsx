import { Outlet } from 'react-router-dom';
import { Navigation } from './Navigation';

export const AppLayout = () => {
  return (
    <div className="min-h-screen bg-tg-secondary-bg">
      <main className="pb-20">
        <Outlet />
      </main>
      <Navigation />
    </div>
  );
};
