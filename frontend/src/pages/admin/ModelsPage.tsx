import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Edit2, Trash2, ToggleLeft, ToggleRight, Coins } from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Loader } from '@/components/ui/Loader';
import { Tabs } from '@/components/ui/Tabs';

import { adminApi } from '@/api/admin';
import { hapticFeedback, showAlert, showConfirm } from '@/utils/telegram';
import type { AIModel, GenerationType } from '@/types';

const tabs = [
  { id: 'all', label: 'Все' },
  { id: 'image', label: 'Картинки' },
  { id: 'video', label: 'Видео' },
];

export const ModelsPage = () => {
  const [activeTab, setActiveTab] = useState('all');
  const [editingModel, setEditingModel] = useState<AIModel | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price_tokens: '',
    price_per_second: '',
    icon: '',
    is_per_second: false,
  });
  const queryClient = useQueryClient();

  const { data: models, isLoading } = useQuery({
    queryKey: ['admin', 'models'],
    queryFn: adminApi.getModels,
  });

  const updateMutation = useMutation({
    mutationFn: ({ modelId, updates }: { modelId: number; updates: any }) =>
      adminApi.updateModel(modelId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
      hapticFeedback.success();
      showAlert('Модель обновлена');
      setEditingModel(null);
    },
    onError: (error: Error) => {
      hapticFeedback.error();
      showAlert(error.message);
    },
  });

  const toggleMutation = useMutation({
    mutationFn: adminApi.toggleModel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
      hapticFeedback.success();
    },
    onError: (error: Error) => {
      hapticFeedback.error();
      showAlert(error.message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteModel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
      hapticFeedback.success();
      showAlert('Модель удалена');
    },
    onError: (error: Error) => {
      hapticFeedback.error();
      showAlert(error.message);
    },
  });

  const handleEdit = (model: AIModel) => {
    setEditingModel(model);
    setFormData({
      name: model.name,
      description: model.description || '',
      price_tokens: model.price_tokens.toString(),
      price_per_second: model.price_per_second != null ? model.price_per_second.toString() : '',
      icon: model.icon || '',
      is_per_second: model.price_per_second != null,
    });
    hapticFeedback.light();
  };

  const handleSave = () => {
    if (!editingModel) return;

    const pps = parseFloat(formData.price_per_second);
    if (isNaN(pps) || pps <= 0) {
      showAlert('Цена за секунду должна быть больше 0');
      return;
    }
    updateMutation.mutate({
      modelId: editingModel.id,
      updates: {
        name: formData.name,
        description: formData.description || null,
        price_per_second: pps,
        icon: formData.icon || null,
      },
    });
  };

  const handleToggle = (model: AIModel) => {
    hapticFeedback.medium();
    toggleMutation.mutate(model.id);
  };

  const handleDelete = async (model: AIModel) => {
    const confirmed = await showConfirm(`Удалить модель "${model.name}"?`);
    if (confirmed) {
      deleteMutation.mutate(model.id);
    }
  };

  if (isLoading) {
    return <Loader fullScreen text="Загрузка моделей..." />;
  }

  const filteredModels = models?.filter((model) => {
    if (activeTab === 'all') return true;
    return model.generation_type === activeTab;
  }) || [];

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'image': return 'Картинки';
      case 'video': return 'Видео';
      default: return type;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-tg-text">Модели</h1>
        <span className="text-sm text-tg-hint">{models?.length || 0} всего</span>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onChange={(tab) => {
          hapticFeedback.light();
          setActiveTab(tab);
        }}
      />

      {/* Models List */}
      {filteredModels.length === 0 ? (
        <Card className="text-center py-8">
          <p className="text-tg-hint">Модели не найдены</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredModels.map((model) => (
            <Card key={model.id} className={!model.is_enabled ? 'opacity-60' : ''}>
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 bg-tg-secondary-bg rounded-xl flex items-center justify-center text-2xl">
                  {model.icon || '🤖'}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-tg-text truncate">{model.name}</h3>
                    <span className={`px-1.5 py-0.5 text-xs rounded ${
                      model.is_enabled 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {model.is_enabled ? 'Вкл' : 'Выкл'}
                    </span>
                  </div>
                  <p className="text-sm text-tg-hint truncate">{model.code}</p>
                  <div className="flex items-center gap-3 mt-1 text-sm">
                    <span className="text-tg-hint">{getTypeLabel(model.generation_type)}</span>
                    <span className="text-tg-button font-medium flex items-center gap-1">
                      <Coins className="w-3 h-3" />
                      {model.price_per_second != null
                        ? `${model.price_per_second}⭐/с`
                        : `${model.price_tokens}⭐`}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggle(model)}
                  >
                    {model.is_enabled ? (
                      <ToggleRight className="w-5 h-5 text-green-600" />
                    ) : (
                      <ToggleLeft className="w-5 h-5 text-gray-400" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEdit(model)}
                  >
                    <Edit2 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(model)}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingModel}
        onClose={() => setEditingModel(null)}
        title="Редактировать модель"
      >
        {editingModel && (
          <div className="space-y-4">
            <Input
              label="Название"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            
            <div>
              <label className="block text-sm font-medium text-tg-text mb-1.5">
                Описание
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-tg-bg text-tg-text resize-none focus:outline-none focus:ring-2 focus:ring-tg-button"
                rows={3}
              />
            </div>
            
            <Input
              label="Цена за 1 секунду (токенов)"
              type="number"
              value={formData.price_per_second}
              onChange={(e) => setFormData({ ...formData, price_per_second: e.target.value })}
              placeholder="например: 1"
            />
            
            <Input
              label="Иконка (emoji)"
              value={formData.icon}
              onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
              placeholder="🎨"
            />

            <div className="flex gap-2">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setEditingModel(null)}
              >
                Отмена
              </Button>
              <Button
                className="flex-1"
                onClick={handleSave}
                isLoading={updateMutation.isPending}
              >
                Сохранить
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

