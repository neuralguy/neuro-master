import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Wallet, ExternalLink, CheckCircle, Clock, Sparkles, AlertCircle } from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Loader } from '@/components/ui/Loader';

import { paymentsApi } from '@/api/payments';
import { userApi } from '@/api/user';
import { useUser } from '@/hooks/useUser';
import { hapticFeedback, showAlert } from '@/utils/telegram';
import { formatTokens, formatDateTime } from '@/utils/format';
import type { PaymentPackage } from '@/types';

const PACKAGE_STYLES: Record<string, { gradient: string; icon: string }> = {
  standard: { gradient: 'from-blue-500 to-blue-600',    icon: '⭐' },
  vip:      { gradient: 'from-purple-500 to-purple-600', icon: '💎' },
  premium:  { gradient: 'from-amber-500 to-orange-500',  icon: '👑' },
  platinum: { gradient: 'from-gray-600 to-gray-800',     icon: '🏆' },
};

export const BalancePage = () => {
  const [pendingPaymentId, setPendingPaymentId] = useState<string | null>(null);
  const [pendingPaymentUrl, setPendingPaymentUrl] = useState<string | null>(null);
  const [pendingPackageName, setPendingPackageName] = useState<string | null>(null);

  const { user, updateBalance } = useUser();

  const { data: packagesData, isLoading: packagesLoading, isError: packagesError, refetch: refetchPackages } = useQuery({
    queryKey: ['payment-packages'],
    queryFn: paymentsApi.getPackages,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['balance-history'],
    queryFn: () => userApi.getHistory(0, 20),
  });

  const createPaymentMutation = useMutation({
    mutationFn: (packageId: string) => paymentsApi.create(packageId),
    onSuccess: (data) => {
      hapticFeedback.success();
      setPendingPaymentId(data.payment_id);
      setPendingPaymentUrl(data.confirmation_url);
      setPendingPackageName(data.package_name);
      window.open(data.confirmation_url, '_blank');
    },
    onError: (error: Error) => {
      hapticFeedback.error();
      showAlert(error.message);
    },
  });

  const checkPaymentMutation = useMutation({
    mutationFn: (paymentId: string) => paymentsApi.check(paymentId),
    onSuccess: (data) => {
      if (data.success && data.new_balance !== null) {
        hapticFeedback.success();
        showAlert('Оплата прошла успешно!');
        updateBalance(data.new_balance);
        setPendingPaymentId(null);
        setPendingPaymentUrl(null);
        setPendingPackageName(null);
      } else {
        hapticFeedback.warning();
        showAlert(data.message);
      }
    },
    onError: (error: Error) => {
      hapticFeedback.error();
      showAlert(error.message);
    },
  });

  const handlePackageSelect = (pkg: PaymentPackage) => {
    hapticFeedback.medium();
    createPaymentMutation.mutate(pkg.id);
  };

  const packages = packagesData?.packages ?? [];

  return (
    <div className="p-4 space-y-4">
      {/* Balance Card */}
      <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
            <Wallet className="w-8 h-8" />
          </div>
          <div>
            <p className="text-sm text-white/70">Ваш баланс</p>
            <p className="text-3xl font-bold">
              {user ? formatTokens(user.balance) : '...'}
            </p>
          </div>
        </div>
      </Card>

      {/* Pending Payment */}
      {pendingPaymentId && (
        <Card className="border-2 border-yellow-400 bg-yellow-50">
          <div className="flex items-center gap-3">
            <Clock className="w-6 h-6 text-yellow-600" />
            <div className="flex-1">
              <p className="font-medium text-yellow-800">
                Ожидание оплаты{pendingPackageName ? ` — ${pendingPackageName}` : ''}
              </p>
              <p className="text-sm text-yellow-600">
                Завершите оплату и нажмите «Проверить»
              </p>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => window.open(pendingPaymentUrl!, '_blank')}
              leftIcon={<ExternalLink className="w-4 h-4" />}
            >
              Оплатить
            </Button>
            <Button
              className="flex-1"
              onClick={() => checkPaymentMutation.mutate(pendingPaymentId)}
              isLoading={checkPaymentMutation.isPending}
              leftIcon={<CheckCircle className="w-4 h-4" />}
            >
              Проверить
            </Button>
          </div>
        </Card>
      )}

      {/* Payment Packages */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-tg-text">Пополнить баланс</h2>

        {packagesLoading ? (
          <Loader text="Загрузка пакетов..." />
        ) : packagesError ? (
          <Card className="text-center py-8">
            <div className="flex flex-col items-center gap-3">
              <AlertCircle className="w-8 h-8 text-red-400" />
              <p className="text-tg-hint">Не удалось загрузить пакеты</p>
              <Button variant="outline" size="sm" onClick={() => refetchPackages()}>
                Попробовать снова
              </Button>
            </div>
          </Card>
        ) : packages.length === 0 ? (
          <Card className="text-center py-8">
            <p className="text-tg-hint">Пакеты недоступны</p>
          </Card>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {packages.map((pkg) => {
              const style = PACKAGE_STYLES[pkg.id] || { gradient: 'from-blue-500 to-blue-600', icon: '⭐' };
              const tokensPerDollar = Math.round(pkg.tokens / pkg.amount);

              return (
                <button
                  key={pkg.id}
                  onClick={() => handlePackageSelect(pkg)}
                  disabled={createPaymentMutation.isPending}
                  className={`bg-gradient-to-br ${style.gradient} text-white rounded-2xl p-4 text-left transition-transform active:scale-95 disabled:opacity-50`}
                >
                  <div className="text-2xl mb-2">{style.icon}</div>
                  <div className="font-bold text-base">{pkg.name}</div>
                  <div className="text-2xl font-bold mt-1">${pkg.amount}</div>
                  <div className="flex items-center gap-1 mt-2 text-sm text-white/80">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{pkg.tokens} токенов</span>
                  </div>
                  {tokensPerDollar > 0 && (
                    <div className="mt-1 text-xs text-white/60">
                      ~{tokensPerDollar} токенов/$
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* History */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-tg-text">История</h2>

        {historyLoading ? (
          <Loader text="Загрузка..." />
        ) : !history || history.items.length === 0 ? (
          <Card className="text-center py-8">
            <p className="text-tg-hint">История пуста</p>
          </Card>
        ) : (
          <div className="space-y-2">
            {history.items.map((item) => (
              <Card key={item.id} padding="sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-tg-text">
                      {item.description}
                    </p>
                    <p className="text-xs text-tg-hint">
                      {formatDateTime(item.created_at)}
                    </p>
                  </div>
                  <div className={`text-lg font-semibold ${
                    item.amount > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {item.amount > 0 ? '+' : ''}{item.amount}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

