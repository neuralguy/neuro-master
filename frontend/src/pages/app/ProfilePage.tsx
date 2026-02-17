import { useQuery } from '@tanstack/react-query';
import { User, Copy, Share2, Gift, Calendar, Hash, Shield } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Loader } from '@/components/ui/Loader';

import { userApi } from '@/api/user';
import { useUser } from '@/hooks/useUser';
import { hapticFeedback, showAlert, getTelegram } from '@/utils/telegram';
import { formatDate, formatTokens } from '@/utils/format';

export const ProfilePage = () => {
  const { user } = useUser();
  const navigate = useNavigate();

  const { data: referralInfo, isLoading } = useQuery({
    queryKey: ['referral-info'],
    queryFn: userApi.getReferralInfo,
  });

  const handleCopyLink = () => {
    if (referralInfo?.referral_link) {
      navigator.clipboard.writeText(referralInfo.referral_link);
      hapticFeedback.success();
      showAlert('Ссылка скопирована!');
    }
  };

  const handleShare = () => {
    if (referralInfo?.referral_link) {
      const tg = getTelegram();
      if (tg) {
        tg.openTelegramLink(
          `https://t.me/share/url?url=${encodeURIComponent(referralInfo.referral_link)}&text=${encodeURIComponent('🎁 Присоединяйся! Получи 15 бесплатных токенов для генерации AI контента!')}`
        );
      }
      hapticFeedback.medium();
    }
  };

  if (isLoading) {
    return <Loader fullScreen text="Загрузка..." />;
  }

  return (
    <div className="p-4 space-y-4">
      {/* Profile Card */}
      <Card>
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-tg-secondary-bg rounded-2xl flex items-center justify-center">
            <User className="w-8 h-8 text-tg-hint" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-tg-text">
              {user?.first_name} {user?.last_name}
            </h1>
            {user?.username && (
              <p className="text-tg-hint">@{user.username}</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="text-center p-3 bg-tg-secondary-bg rounded-xl">
            <p className="text-2xl font-bold text-tg-text">
              {user ? formatTokens(user.balance) : '...'}
            </p>
            <p className="text-xs text-tg-hint mt-1">Баланс</p>
          </div>
          <div className="text-center p-3 bg-tg-secondary-bg rounded-xl">
            <p className="text-2xl font-bold text-tg-text">
              {referralInfo?.total_referrals || 0}
            </p>
            <p className="text-xs text-tg-hint mt-1">Приглашено</p>
          </div>
        </div>
      </Card>

      {/* Admin Panel Button */}
      {user?.is_admin && (
        <Card
          className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white cursor-pointer active:scale-[0.98] transition-transform"
          onClick={() => {
            hapticFeedback.medium();
            navigate('/admin');
          }}
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-lg">Админ-панель</h3>
              <p className="text-sm text-white/70">Управление приложением</p>
            </div>
          </div>
        </Card>
      )}

      {/* User Info */}
      <Card>
        <h2 className="text-lg font-semibold text-tg-text mb-3">Информация</h2>
        
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <Hash className="w-5 h-5 text-tg-hint" />
            <div>
              <p className="text-xs text-tg-hint">ID</p>
              <p className="text-tg-text">{user?.telegram_id}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-tg-hint" />
            <div>
              <p className="text-xs text-tg-hint">Регистрация</p>
              <p className="text-tg-text">
                {user ? formatDate(user.created_at) : '...'}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Referral */}
      <Card className="bg-gradient-to-r from-green-500 to-emerald-500 text-white">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
            <Gift className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Приглашай друзей</h2>
            <p className="text-sm text-white/80">
              Получай <span className="font-bold text-white">15</span> токенов за каждого
            </p>
          </div>
        </div>

        {/* Описание */}
        <div className="bg-white/10 rounded-xl p-3 mb-4 text-sm text-white/90 leading-relaxed">
          <p className="font-semibold text-white mb-1">✨ Делитесь доступом — получайте доход</p>
          <p>
            Приглашайте друзей и получайте 15 токенов за каждого, кто присоединится по вашей ссылке.
          </p>
          <p className="mt-2">
            Ваши друзья получают также 15 токенов и инструмент для создания сильного визуала,
            а вы — токены, которые можно инвестировать в генерацию эффектных фото и видео.
          </p>
          <p className="mt-2 font-medium text-white">
            Это не просто приглашение — это способ монетизировать своё окружение и усиливать свой контент.
          </p>
        </div>

        <div className="bg-white/10 rounded-xl p-3 mb-4">
          <p className="text-xs text-white/70 mb-1">Твоя ссылка</p>
          <p className="text-sm break-all">{referralInfo?.referral_link}</p>
        </div>

        <div className="flex gap-2">
          <Button
            variant="secondary"
            className="flex-1 bg-white/20 hover:bg-white/30 text-white"
            onClick={handleCopyLink}
            leftIcon={<Copy className="w-4 h-4" />}
          >
            Копировать
          </Button>
          <Button
            variant="secondary"
            className="flex-1 bg-white/20 hover:bg-white/30 text-white"
            onClick={handleShare}
            leftIcon={<Share2 className="w-4 h-4" />}
          >
            Поделиться
          </Button>
        </div>

        {referralInfo && referralInfo.total_bonus_earned > 0 && (
          <div className="mt-4 pt-4 border-t border-white/20">
            <p className="text-sm text-white/70">
              Заработано: <span className="font-semibold text-white">
                {formatTokens(referralInfo.total_bonus_earned)}
              </span>
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};

