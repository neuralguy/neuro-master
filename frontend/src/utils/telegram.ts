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

// ============================================================
// Token auth cache — saved ONCE before React Router changes URL
// ============================================================
let _cachedTokenAuth: { uid: string; token: string } | null = null;
let _tokenAuthInitialized = false;

/**
 * Must be called ONCE at app startup, BEFORE BrowserRouter mounts,
 * because the router will strip query params from the URL.
 */
export function initTokenAuth(): void {
  if (_tokenAuthInitialized) return;
  _tokenAuthInitialized = true;

  const params = new URLSearchParams(window.location.search);
  const uid = params.get('uid');
  const token = params.get('token');

  if (uid && token) {
    // Сохраняем в sessionStorage, чтобы пережить перезагрузку страницы
    _cachedTokenAuth = { uid, token };
    sessionStorage.setItem('tg_uid', uid);
    sessionStorage.setItem('tg_token', token);
    console.log('[auth] Token auth cached from URL', { uid, tokenLen: token.length });
  } else {
    // Параметров нет в URL — пробуем восстановить из sessionStorage (после reload)
    const storedUid = sessionStorage.getItem('tg_uid');
    const storedToken = sessionStorage.getItem('tg_token');
    if (storedUid && storedToken) {
      _cachedTokenAuth = { uid: storedUid, token: storedToken };
      console.log('[auth] Token auth restored from sessionStorage', { uid: storedUid });
    } else {
      console.log('[auth] No token auth params in URL or sessionStorage');
    }
  }
}

/**
 * Returns cached token auth, or null.
 */
export function getTokenAuth(): { uid: string; token: string } | null {
  return _cachedTokenAuth;
}

// ============================================================
// Telegram WebApp helpers
// ============================================================

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

