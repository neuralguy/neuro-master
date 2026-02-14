export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
};

export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('ru-RU').format(num);
};

export const formatTokens = (tokens: number): string => {
  return `${formatNumber(tokens)} ${pluralize(tokens, 'токен', 'токена', 'токенов')}`;
};

export const formatMoney = (amount: number): string => {
  return `${formatNumber(amount)} ₽`;
};

export const pluralize = (
  count: number,
  one: string,
  few: string,
  many: string
): string => {
  const mod10 = count % 10;
  const mod100 = count % 100;
  
  if (mod100 >= 11 && mod100 <= 19) {
    return many;
  }
  
  if (mod10 === 1) {
    return one;
  }
  
  if (mod10 >= 2 && mod10 <= 4) {
    return few;
  }
  
  return many;
};

export const getStatusColor = (status: string): string => {
  switch (status) {
    case 'success':
      return 'text-green-600 bg-green-100';
    case 'pending':
    case 'processing':
      return 'text-yellow-600 bg-yellow-100';
    case 'failed':
    case 'cancelled':
      return 'text-red-600 bg-red-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
};

export const getStatusText = (status: string): string => {
  switch (status) {
    case 'success':
      return 'Готово';
    case 'pending':
      return 'В очереди';
    case 'processing':
      return 'Генерация...';
    case 'failed':
      return 'Ошибка';
    case 'cancelled':
      return 'Отменено';
    default:
      return status;
  }
};

export const getOperationTypeText = (type: string): string => {
  switch (type) {
    case 'deposit':
      return 'Пополнение';
    case 'generation':
      return 'Генерация';
    case 'referral':
      return 'Реферал';
    case 'welcome':
      return 'Бонус';
    case 'admin':
      return 'Админ';
    case 'refund':
      return 'Возврат';
    default:
      return type;
  }
};
