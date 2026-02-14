import { NavLink } from 'react-router-dom';
import { clsx } from 'clsx';
import { Sparkles, Image, Wallet, User } from 'lucide-react';
import { hapticFeedback } from '@/utils/telegram';

const navItems = [
  { to: '/generate', icon: Sparkles, label: 'Создать' },
  { to: '/gallery', icon: Image, label: 'Галерея' },
  { to: '/balance', icon: Wallet, label: 'Баланс' },
  { to: '/profile', icon: User, label: 'Профиль' },
];

export const Navigation = () => {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-tg-bg border-t border-gray-100 safe-area-bottom z-30">
      <div className="flex items-center justify-around px-2 py-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => hapticFeedback.light()}
            className={({ isActive }) =>
              clsx(
                'flex flex-col items-center justify-center py-2 px-3 rounded-xl transition-colors min-w-[64px]',
                isActive
                  ? 'text-tg-button'
                  : 'text-tg-hint hover:text-tg-text'
              )
            }
          >
            <Icon className="w-6 h-6" />
            <span className="text-xs mt-1">{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
};

