import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Wallet, ExternalLink, CheckCircle, Clock, AlertCircle } from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Loader } from '@/components/ui/Loader';

import { paymentsApi } from '@/api/payments';
import { userApi } from '@/api/user';
import { useUser } from '@/hooks/useUser';
import { hapticFeedback, showAlert } from '@/utils/telegram';
import { formatMoney, formatTokens, formatDateTime, getOperationTypeText } from '@/utils/format';

export const BalancePage = () => {
  const [customAmount, setCustomAmount] = useState('');
  const [pendingPaymentId, setPendingPaymentId] = useState<string | null>(null);
  const [pendingPaymentUrl, setPendingPaymentUrl] = useState<string | null>(null);
  
  const { user, updateBalance } = useUser();

  // Fetch payment packages
  const { data: packages } = useQuery({
    queryKey: ['payment-packages'],
    queryFn: paymentsApi.getPackages,
  });

  // Fetch balance history
  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['balance-history'],
    queryFn: () => userApi.getHistory(0, 20),
  });

  // Create payment mutation
  const createPaymentMutation = useMutation({
    mutationFn: paymentsApi.create,
    onSuccess: (data) => {
      hapticFeedback.success();
      setPendingPaymentId(data.payment_id);
      setPendingPaymentUrl(data.confirmation_url);
      window.open(data.confirmation_url, '_blank');
    },
    onError: (error: Error) => {
      hapticFeedback.error();
      showAlert(error.message);
    },
  });

  // Check payment mutation
  const checkPaymentMutation = useMutation({
    mutationFn: (paymentId: string) => paymentsApi.check(paymentId),
    onSuccess: (data) => {
      if (data.success && data.new_balance !== null) {
        hapticFeedback.success();
        showAlert('Оплата прошла успешно!');
        updateBalance(data.new_balance);
        setPendingPaymentId(null);
        setPendingPaymentUrl(null);
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

  const handlePayment = (amount: number) => {
    hapticFeedback.medium();
    createPaymentMutation.mutate(amount);
  };

  const handleCustomPayment = () => {
    const amount = parseInt(customAmount);
    if (isNaN(amount) || amount < (packages?.min_amount || 50)) {
      showAlert(`Минимальная сумма: ${packages?.min_amount || 50} ₽`);
      return;
    }
    if (amount > (packages?.max_amount || 50000)) {
      showAlert(`Максимальная сумма: ${packages?.max_amount || 50000} ₽`);
      return;
    }
    handlePayment(amount);
  };

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
              <p className="font-medium text-yellow-800">Ожидание оплаты</p>
              <p className="text-sm text-yellow-600">
                Завершите оплату и нажмите "Проверить"
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
        <h2 className="text-lg font-semibold text-tg-text">Пополнить</h2>
        
        <div className="grid grid-cols-3 gap-2">
          {packages?.packages.map((amount) => (
            <Button
              key={amount}
              variant="outline"
              onClick={() => handlePayment(amount)}
              disabled={createPaymentMutation.isPending}
            >
              {formatMoney(amount)}
            </Button>
          ))}
        </div>

        <div className="flex gap-2">
          <Input
            type="number"
            placeholder="Другая сумма"
            value={customAmount}
            onChange={(e) => setCustomAmount(e.target.value)}
            className="flex-1"
          />
          <Button
            onClick={handleCustomPayment}
            disabled={createPaymentMutation.isPending || !customAmount}
          >
            Оплатить
          </Button>
        </div>

        <p className="text-xs text-tg-hint text-center">
          1 токен = 1 ₽ • Минимум {packages?.min_amount || 50} ₽
        </p>
      </div>

      {/* History */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-tg-text">История</h2>
        
        {historyLoading ? (
          <Loader text="Загрузка..." />
        ) : history?.items.length === 0 ? (
          <Card className="text-center py-8">
            <p className="text-tg-hint">История пуста</p>
          </Card>
        ) : (
          <div className="space-y-2">
            {history?.items.map((item) => (
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
