import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import { LayoutDashboard, Users, Bot, ArrowLeft } from 'lucide-react';

const adminNavItems = [
  { to: '/admin', icon: LayoutDashboard, label: 'Дашборд', end: true },
  { to: '/admin/users', icon: Users, label: 'Пользователи' },
  { to: '/admin/models', icon: Bot, label: 'Модели' },
];

export const AdminLayout = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-tg-secondary-bg">
      {/* Header */}
      <header className="bg-tg-bg border-b border-gray-100 px-4 py-3 sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="p-2 rounded-lg hover:bg-tg-secondary-bg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-lg font-semibold">Админ-панель</h1>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-tg-bg border-b border-gray-100 px-2 py-2 overflow-x-auto hide-scrollbar">
        <div className="flex gap-1 min-w-max">
          {adminNavItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors whitespace-nowrap',
                  isActive
                    ? 'bg-tg-button text-tg-button-text'
                    : 'text-tg-hint hover:bg-tg-secondary-bg hover:text-tg-text'
                )
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="p-4">
        <Outlet />
      </main>
    </div>
  );
};

