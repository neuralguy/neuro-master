import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Heart, Trash2, Download, ImageIcon, Video, Star } from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Tabs } from '@/components/ui/Tabs';
import { Loader } from '@/components/ui/Loader';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';

import { galleryApi } from '@/api/gallery';
import { hapticFeedback, showConfirm } from '@/utils/telegram';
import { formatDateTime } from '@/utils/format';
import type { GalleryItem } from '@/types';

const tabs = [
  { id: 'all', label: 'Все' },
  { id: 'image', label: 'Фото' },
  { id: 'video', label: 'Видео' },
  { id: 'favorites', label: '⭐' },
];

export const GalleryPage = () => {
  const [activeTab, setActiveTab] = useState('all');
  const [selectedItem, setSelectedItem] = useState<GalleryItem | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['gallery', activeTab],
    queryFn: () => galleryApi.getAll(
      0,
      50,
      activeTab !== 'all' && activeTab !== 'favorites' ? activeTab : undefined,
      activeTab === 'favorites'
    ),
  });

  const toggleFavoriteMutation = useMutation({
    mutationFn: galleryApi.toggleFavorite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery'] });
      hapticFeedback.success();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: galleryApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery'] });
      setSelectedItem(null);
      hapticFeedback.success();
    },
  });

  const handleDelete = async (id: string) => {
    const confirmed = await showConfirm('Удалить это изображение?');
    if (confirmed) {
      deleteMutation.mutate(id);
    }
  };

  const handleDownload = (item: GalleryItem) => {
    window.open(item.file_url, '_blank');
  };

  if (isLoading) {
    return <Loader fullScreen text="Загрузка галереи..." />;
  }

  const items = data?.items || [];

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold text-tg-text">Галерея</h1>

      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onChange={(tab) => {
          hapticFeedback.light();
          setActiveTab(tab);
        }}
      />

      {items.length === 0 ? (
        <Card className="text-center py-12">
          <ImageIcon className="w-12 h-12 text-tg-hint mx-auto mb-3" />
          <p className="text-tg-hint">Пока ничего нет</p>
          <p className="text-sm text-tg-hint mt-1">
            Созданные изображения появятся здесь
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {items.map((item) => (
            <Card
              key={item.id}
              padding="none"
              className="overflow-hidden cursor-pointer"
              onClick={() => setSelectedItem(item)}
            >
              <div className="aspect-square bg-tg-secondary-bg relative">
                {item.file_type === 'video' ? (
                  <video
                    src={item.file_url}
                    poster={item.thumbnail_url || undefined}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <img
                    src={item.thumbnail_url || item.file_url}
                    alt={item.prompt || ''}
                    className="w-full h-full object-cover"
                  />
                )}
                
                {item.is_favorite && (
                  <div className="absolute top-2 right-2 w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
                    <Star className="w-4 h-4 text-white fill-current" />
                  </div>
                )}
                
                {item.file_type === 'video' && (
                  <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/50 rounded text-xs text-white">
                    <Video className="w-3 h-3 inline mr-1" />
                    Видео
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      <Modal
        isOpen={!!selectedItem}
        onClose={() => setSelectedItem(null)}
        title="Детали"
        size="full"
      >
        {selectedItem && (
          <div className="space-y-4">
            <div className="aspect-square bg-tg-secondary-bg rounded-xl overflow-hidden">
              {selectedItem.file_type === 'video' ? (
                <video
                  src={selectedItem.file_url}
                  className="w-full h-full object-contain"
                  controls
                  autoPlay
                />
              ) : (
                <img
                  src={selectedItem.file_url}
                  alt={selectedItem.prompt || ''}
                  className="w-full h-full object-contain"
                />
              )}
            </div>

            {selectedItem.prompt && (
              <p className="text-sm text-tg-text">{selectedItem.prompt}</p>
            )}

            <p className="text-xs text-tg-hint">
              {formatDateTime(selectedItem.created_at)}
              {selectedItem.model_name && ` • ${selectedItem.model_name}`}
            </p>

            <div className="flex gap-2">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => toggleFavoriteMutation.mutate(selectedItem.id)}
                leftIcon={<Heart className={selectedItem.is_favorite ? 'fill-current text-red-500' : ''} />}
              >
                {selectedItem.is_favorite ? 'В избранном' : 'В избранное'}
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => handleDownload(selectedItem)}
                leftIcon={<Download />}
              >
                Скачать
              </Button>
              <Button
                variant="danger"
                onClick={() => handleDelete(selectedItem.id)}
                isLoading={deleteMutation.isPending}
              >
                <Trash2 className="w-5 h-5" />
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
