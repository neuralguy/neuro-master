import { useEffect, useState } from 'react';
import { getTelegram, TelegramWebApp } from '@/utils/telegram';

export const useTelegram = () => {
  const [tg, setTg] = useState<TelegramWebApp | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const telegram = getTelegram();
    
    if (telegram) {
      setTg(telegram);
      telegram.ready();
      telegram.expand();
      setIsReady(true);
      
      // Set theme colors
      document.documentElement.style.setProperty(
        '--tg-theme-bg-color',
        telegram.themeParams.bg_color || '#ffffff'
      );
      document.documentElement.style.setProperty(
        '--tg-theme-text-color',
        telegram.themeParams.text_color || '#000000'
      );
      document.documentElement.style.setProperty(
        '--tg-theme-secondary-bg-color',
        telegram.themeParams.secondary_bg_color || '#f4f4f5'
      );
    } else {
      // Running outside Telegram (dev mode)
      setIsReady(true);
    }
  }, []);

  return {
    tg,
    isReady,
    user: tg?.initDataUnsafe?.user,
    colorScheme: tg?.colorScheme || 'light',
    initData: tg?.initData || '',
  };
};
