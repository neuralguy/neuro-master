import { useNavigate } from 'react-router-dom';
import { Sparkles, Image, Video, Smile, ArrowRight, Gift } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { BalanceWidget } from '@/components/shared/BalanceWidget';
import { useUser } from '@/hooks/useUser';
import { hapticFeedback } from '@/utils/telegram';

const features = [
  {
    icon: Image,
    title: 'Изображения',
    description: 'Создавайте уникальные картинки по описанию',
    color: 'bg-purple-100 text-purple-600',
    type: 'image',
  },
  {
    icon: Video,
    title: 'Видео',
    description: 'Генерируйте короткие видео из текста',
    color: 'bg-blue-100 text-blue-600',
    type: 'video',
  },
  {
    icon: Smile,
    title: 'FaceSwap',
    description: 'Меняйте лица на фотографиях',
    color: 'bg-orange-100 text-orange-600',
    type: 'faceswap',
  },
];

export const HomePage = () => {
  const navigate = useNavigate();
  const { user } = useUser();

  const handleFeatureClick = (type: string) => {
    hapticFeedback.medium();
    navigate(`/generate?type=${type}`);
  };

  return (
    <div className="p-4 space-y-4">
      {/* Welcome */}
      <div className="text-center py-4">
        <h1 className="text-2xl font-bold text-tg-text">
          Привет! 👋
        </h1>
        <p className="text-tg-hint mt-1">
          Создавайте контент с помощью ИИ
        </p>
      </div>

      {/* Balance */}
      <BalanceWidget />

      {/* Features */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-tg-text px-1">
          Что создадим?
        </h2>
        
        {features.map((feature) => (
          <Card
            key={feature.type}
            onClick={() => handleFeatureClick(feature.type)}
            className="cursor-pointer hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${feature.color}`}>
                <feature.icon className="w-7 h-7" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-tg-text">{feature.title}</h3>
                <p className="text-sm text-tg-hint mt-0.5">{feature.description}</p>
              </div>
              <ArrowRight className="w-5 h-5 text-tg-hint" />
            </div>
          </Card>
        ))}
      </div>

      {/* Referral Banner */}
      <Card className="bg-gradient-to-r from-green-500 to-emerald-500 text-white">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
            <Gift className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold">Приглашай друзей</h3>
            <p className="text-sm text-white/80">
              Получай 50 токенов за каждого
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              hapticFeedback.light();
              navigate('/profile');
            }}
            className="bg-white/20 hover:bg-white/30 text-white"
          >
            Подробнее
          </Button>
        </div>
      </Card>

      {/* Admin Link */}
      {user?.is_admin && (
        <Button
          variant="outline"
          className="w-full"
          onClick={() => navigate('/admin')}
        >
          Админ-панель
        </Button>
      )}
    </div>
  );
};
