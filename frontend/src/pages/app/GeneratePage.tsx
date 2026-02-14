import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Upload, X, ChevronDown, ImageIcon, VideoIcon, Paperclip, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { modelsApi } from '@/api/models';
import { generationApi } from '@/api/generation';
import { uploadApi } from '@/api/upload';
import { useUser } from '@/hooks/useUser';
import { useTelegram } from '@/hooks/useTelegram';
import type { AIModel, GenerationType, AIModelsGrouped } from '@/types';

export default function GeneratePage() {
  const { user, updateBalance } = useUser();
  const { tg } = useTelegram();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeType, setActiveType] = useState<GenerationType>('image');
  const [selectedModel, setSelectedModel] = useState<AIModel | null>(null);
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('1:1');
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const [isRatioDropdownOpen, setIsRatioDropdownOpen] = useState(false);

  const { data: modelsGrouped, isLoading } = useQuery<AIModelsGrouped>({
    queryKey: ['models', 'grouped'],
    queryFn: modelsApi.getGrouped,
  });

  // Определяем есть ли загруженное фото
  const hasImage = !!uploadedImage;

  // Фильтрация моделей по типу и наличию фото
  const currentModels = (() => {
    if (!modelsGrouped) return [];

    if (activeType === 'video') {
      const allVideoModels = modelsGrouped.video || [];
      
      if (hasImage) {
        return allVideoModels.filter(m => 
          m.code.includes('-i2v') || m.config?.mode === 'image-to-video'
        );
      } else {
        return allVideoModels.filter(m => 
          !m.code.includes('-i2v') && m.config?.mode !== 'image-to-video'
        );
      }
    }

    if (activeType === 'image') {
      const allImageModels = modelsGrouped.image || [];
      
      if (hasImage) {
        return allImageModels.filter(m => 
          m.code.includes('-edit') || m.config?.mode === 'image-to-image'
        );
      } else {
        return allImageModels.filter(m => 
          !m.code.includes('-edit') && m.config?.mode !== 'image-to-image'
        );
      }
    }

    return [];
  })();

  // Автовыбор модели при смене списка
  useEffect(() => {
    if (currentModels.length > 0) {
      const exists = selectedModel && currentModels.find(m => m.id === selectedModel.id);
      if (!exists) {
        setSelectedModel(currentModels[0]);
      }
    } else {
      setSelectedModel(null);
    }
  }, [currentModels, hasImage, activeType]);

  // Сброс aspect ratio при смене модели
  useEffect(() => {
    if (selectedModel?.config?.aspect_ratios?.length) {
      setAspectRatio(selectedModel.config.aspect_ratios[0]);
    } else {
      setAspectRatio('1:1');
    }
  }, [selectedModel]);

  const generation = useMutation({
    mutationFn: (request: { model_code: string; prompt?: string; image_url?: string; aspect_ratio?: string }) => 
      generationApi.create(request),
    onSuccess: () => {
      tg?.HapticFeedback?.notificationOccurred('success');
      alert('Генерация запущена! Результат появится в галерее.');
      if (user && selectedModel) {
        updateBalance(user.balance - selectedModel.price_tokens);
      }
      setPrompt('');
      setUploadedImage(null);
      setUploadedImageUrl(null);
    },
    onError: (error: Error) => {
      tg?.HapticFeedback?.notificationOccurred('error');
      alert(error.message || 'Ошибка генерации');
    },
  });

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      alert('Файл слишком большой. Максимум 10MB');
      return;
    }

    // Показываем превью сразу
    const reader = new FileReader();
    reader.onload = (event) => {
      setUploadedImage(event.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Загружаем на сервер
    setIsUploading(true);
    try {
      const response = await uploadApi.uploadFile(file);
      setUploadedImageUrl(response.url);
    } catch (error) {
      alert('Ошибка загрузки изображения');
      setUploadedImage(null);
    } finally {
      setIsUploading(false);
    }
  };

  const removeImage = () => {
    setUploadedImage(null);
    setUploadedImageUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async () => {
    if (!selectedModel) {
      alert('Выберите модель');
      return;
    }

    if (!hasImage && !prompt.trim()) {
      alert('Введите описание');
      return;
    }

    if (hasImage && !uploadedImageUrl) {
      alert('Дождитесь загрузки изображения');
      return;
    }

    if (user && selectedModel && user.balance < selectedModel.price_tokens) {
      alert('Недостаточно токенов');
      return;
    }

    generation.mutate({
      model_code: selectedModel.code,
      prompt: prompt.trim() || undefined,
      image_url: uploadedImageUrl || undefined,
      aspect_ratio: aspectRatio,
    });
  };

  const handleTypeChange = (type: GenerationType) => {
    setActiveType(type);
    setUploadedImage(null);
    setUploadedImageUrl(null);
    setSelectedModel(null);
  };

  const aspectRatios = selectedModel?.config?.aspect_ratios || ['1:1', '16:9', '9:16'];

  const getDisplayName = (model: AIModel) => {
    return model.name;
  };

  // Закрытие dropdown при клике вне
  useEffect(() => {
    const handleClickOutside = () => {
      setIsModelDropdownOpen(false);
      setIsRatioDropdownOpen(false);
    };
    if (isModelDropdownOpen || isRatioDropdownOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [isModelDropdownOpen, isRatioDropdownOpen]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Табы Фото/Видео */}
      <div className="bg-gray-100 dark:bg-gray-800 p-1.5 rounded-2xl flex gap-1">
        <button
          onClick={() => handleTypeChange('image')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all ${
            activeType === 'image'
              ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <ImageIcon className="w-5 h-5" />
          Изображение
        </button>
        <button
          onClick={() => handleTypeChange('video')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all ${
            activeType === 'video'
              ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <VideoIcon className="w-5 h-5" />
          Видео
        </button>
      </div>

      {/* Превью загруженного изображения */}
      {uploadedImage && (
        <div className="relative bg-gray-100 dark:bg-gray-800 rounded-2xl p-3">
          <div className="flex items-center justify-center">
            <img 
              src={uploadedImage} 
              alt="Uploaded" 
              className="max-w-full max-h-48 w-auto h-auto object-contain rounded-xl" 
            />
          </div>
          {isUploading && (
            <div className="absolute inset-0 bg-black/50 rounded-2xl flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-white animate-spin" />
            </div>
          )}
          <button
            onClick={removeImage}
            className="absolute top-2 right-2 p-2 bg-black/60 hover:bg-black/80 rounded-full text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Основная карточка ввода */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm">
        {/* Поле ввода с кнопкой загрузки */}
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={hasImage ? 'Опишите желаемые изменения...' : 'Опишите что хотите создать...'}
            className="w-full h-32 p-4 pr-12 bg-transparent text-gray-900 dark:text-white placeholder-gray-400 resize-none border-0 focus:ring-0 text-sm rounded-t-2xl"
          />
          
          {/* Кнопка загрузки фото */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className={`absolute bottom-3 right-3 p-2.5 rounded-xl transition-colors ${
              hasImage 
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400' 
                : 'bg-gray-100 dark:bg-gray-800 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Paperclip className="w-5 h-5" />}
          </button>
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
        </div>

        {/* Разделитель */}
        <div className="border-t border-gray-100 dark:border-gray-800" />

        {/* Контролы */}
        <div className="p-3 flex gap-2">
          {/* Выбор модели */}
          {currentModels.length > 0 && (
            <div className="relative flex-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsModelDropdownOpen(!isModelDropdownOpen);
                  setIsRatioDropdownOpen(false);
                }}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <span className="flex items-center gap-2 text-gray-900 dark:text-white">
                  {selectedModel?.icon && <span>{selectedModel.icon}</span>}
                  <span className="truncate font-medium">{selectedModel ? getDisplayName(selectedModel) : 'Модель'}</span>
                </span>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isModelDropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {isModelDropdownOpen && (
                <div 
                  className="absolute bottom-full left-0 right-0 mb-2 bg-white dark:bg-gray-800 rounded-xl shadow-xl z-[100] max-h-56 overflow-y-auto border border-gray-200 dark:border-gray-700"
                  onClick={(e) => e.stopPropagation()}
                >
                  {currentModels.map((model) => (
                    <button
                      key={model.id}
                      onClick={() => {
                        setSelectedModel(model);
                        setIsModelDropdownOpen(false);
                      }}
                      className={`w-full flex items-center gap-2 p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 text-sm transition-colors ${
                        selectedModel?.id === model.id ? 'bg-blue-50 dark:bg-blue-900/30' : ''
                      }`}
                    >
                      {model.icon && <span className="text-lg">{model.icon}</span>}
                      <span className="flex-1 text-gray-900 dark:text-white font-medium">{getDisplayName(model)}</span>
                      <span className="text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-lg">{model.price_tokens}⭐</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Выбор соотношения */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsRatioDropdownOpen(!isRatioDropdownOpen);
                setIsModelDropdownOpen(false);
              }}
              className="flex items-center justify-between gap-2 p-3 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors min-w-[80px]"
            >
              <span className="text-gray-900 dark:text-white font-medium">{aspectRatio}</span>
              <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isRatioDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {isRatioDropdownOpen && (
              <div 
                className="absolute bottom-full right-0 mb-2 bg-white dark:bg-gray-800 rounded-xl shadow-xl z-[100] overflow-hidden border border-gray-200 dark:border-gray-700 min-w-[100px]"
                onClick={(e) => e.stopPropagation()}
              >
                {aspectRatios.map((ratio) => (
                  <button
                    key={ratio}
                    onClick={() => {
                      setAspectRatio(ratio);
                      setIsRatioDropdownOpen(false);
                    }}
                    className={`w-full p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 text-sm transition-colors ${
                      aspectRatio === ratio ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' : 'text-gray-900 dark:text-white'
                    }`}
                  >
                    {ratio}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Кнопка генерации */}
      <Button
        onClick={handleSubmit}
        disabled={generation.isPending || !selectedModel || isUploading}
        className="w-full py-4 text-base font-semibold rounded-2xl"
        size="lg"
      >
        {generation.isPending ? 'Генерация...' : 'Сгенерировать'}
      </Button>
    </div>
  );
}

