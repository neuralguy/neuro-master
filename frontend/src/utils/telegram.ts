// Cached token auth params (saved on first load, before router changes URL)
let _cachedTokenAuth: { uid: string; token: string } | null = null;

export function initTokenAuth(): void {
  const params = new URLSearchParams(window.location.search);
  const uid = params.get('uid');
  const token = params.get('token');
  if (uid && token) {
    _cachedTokenAuth = { uid, token };
  }
}

export function getTokenAuth(): { uid: string; token: string } | null {
  return _cachedTokenAuth;
}

// Telegram WebApp types
declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: {
      id: number;
      first_name: string;
      last_name?: string;
      username?: string;
      language_code?: string;
    };
    auth_date: number;
    hash: string;
  };
  colorScheme: 'light' | 'dark';
  themeParams: {
    bg_color?: string;
    text_color?: string;
    hint_color?: string;
    link_color?: string;
    button_color?: string;
    button_text_color?: string;
    secondary_bg_color?: string;
  };
  isExpanded: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  MainButton: {
    text: string;
    color: string;
    textColor: string;
    isVisible: boolean;
    isActive: boolean;
    isProgressVisible: boolean;
    setText: (text: string) => void;
    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;
    show: () => void;
    hide: () => void;
    enable: () => void;
    disable: () => void;
    showProgress: (leaveActive?: boolean) => void;
    hideProgress: () => void;
  };
  BackButton: {
    isVisible: boolean;
    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;
    show: () => void;
    hide: () => void;
  };
  HapticFeedback: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
    selectionChanged: () => void;
  };
  close: () => void;
  expand: () => void;
  ready: () => void;
  setHeaderColor: (color: string) => void;
  setBackgroundColor: (color: string) => void;
  enableClosingConfirmation: () => void;
  disableClosingConfirmation: () => void;
  openLink: (url: string) => void;
  openTelegramLink: (url: string) => void;
  showAlert: (message: string, callback?: () => void) => void;
  showConfirm: (message: string, callback?: (confirmed: boolean) => void) => void;
  showPopup: (params: {
    title?: string;
    message: string;
    buttons?: Array<{
      id?: string;
      type?: 'default' | 'ok' | 'close' | 'cancel' | 'destructive';
      text?: string;
    }>;
  }, callback?: (buttonId: string) => void) => void;
}

export const getTelegram = (): TelegramWebApp | null => {
  return window.Telegram?.WebApp || null;
};

export const getInitData = (): string => {
  const tg = getTelegram();
  return tg?.initData || '';
};

export const getTelegramUser = () => {
  const tg = getTelegram();
  return tg?.initDataUnsafe?.user || null;
};

export const hapticFeedback = {
  light: () => getTelegram()?.HapticFeedback.impactOccurred('light'),
  medium: () => getTelegram()?.HapticFeedback.impactOccurred('medium'),
  heavy: () => getTelegram()?.HapticFeedback.impactOccurred('heavy'),
  success: () => getTelegram()?.HapticFeedback.notificationOccurred('success'),
  error: () => getTelegram()?.HapticFeedback.notificationOccurred('error'),
  warning: () => getTelegram()?.HapticFeedback.notificationOccurred('warning'),
};

export const showAlert = (message: string) => {
  const tg = getTelegram();
  if (tg) {
    tg.showAlert(message);
  } else {
    alert(message);
  }
};

export const showConfirm = (message: string): Promise<boolean> => {
  return new Promise((resolve) => {
    const tg = getTelegram();
    if (tg) {
      tg.showConfirm(message, resolve);
    } else {
      resolve(confirm(message));
    }
  });
};
