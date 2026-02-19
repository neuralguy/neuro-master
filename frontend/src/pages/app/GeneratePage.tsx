// frontend/src/pages/app/GeneratePage.tsx

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { X, ChevronDown, ImageIcon, VideoIcon, Paperclip, Loader2, Gift, Film } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { modelsApi } from '@/api/models';
import { generationApi } from '@/api/generation';
import { uploadApi } from '@/api/upload';
import { useUser } from '@/hooks/useUser';
import { useTelegram } from '@/hooks/useTelegram';
import type { AIModel, GenerationType, AIModelsGrouped } from '@/types';

// ── helpers ──────────────────────────────────────────────

function getFilteredModelIds(
  allModels: AIModel[],
  activeType: GenerationType,
  hasImage: boolean,
): number[] {
  let filtered: AIModel[];

  if (activeType === 'video') {
    if (hasImage) {
      filtered = allModels.filter(m => {
        const mode = m.config?.mode;
        return mode === 'image-to-video' || mode === 'motion-control' || m.code.includes('-i2v');
      });
    } else {
      filtered = allModels.filter(m => {
        const mode = m.config?.mode;
        if (mode === 'motion-control') return true;
        if (mode === 'image-to-video') return false;
        if (m.code.includes('-i2v')) return false;
        return true;
      });
    }
  } else if (activeType === 'image') {
    if (hasImage) {
      filtered = allModels.filter(m =>
        m.code.includes('-edit') || m.config?.mode === 'image-to-image'
      );
    } else {
      filtered = allModels.filter(m =>
        !m.code.includes('-edit') && m.config?.mode !== 'image-to-image'
      );
    }
  } else {
    filtered = [];
  }

  return filtered.map(m => m.id);
}

/** Stable stringified key so we can compare in useMemo */
function idsKey(ids: number[]): string {
  return ids.join(',');
}

// ── component ────────────────────────────────────────────

export default function GeneratePage() {
  const { user, updateBalance } = useUser();
  const { tg } = useTelegram();
  const navigate = useNavigate();
  const imageInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const [searchParams] = useSearchParams();

  const initialType = (searchParams.get('type') === 'video' ? 'video' : 'image') as GenerationType;

  const [activeType, setActiveType] = useState<GenerationType>(initialType);
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('1:1');

  // Image upload
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [isUploadingImage, setIsUploadingImage] = useState(false);

  // Video upload
  const [uploadedVideo, setUploadedVideo] = useState<string | null>(null);
  const [uploadedVideoUrl, setUploadedVideoUrl] = useState<string | null>(null);
  const [isUploadingVideo, setIsUploadingVideo] = useState(false);

  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const [isRatioDropdownOpen, setIsRatioDropdownOpen] = useState(false);

  const { data: modelsGrouped, isLoading } = useQuery<AIModelsGrouped>({
    queryKey: ['models', 'grouped'],
    queryFn: modelsApi.getGrouped,
  });

  const hasImage = !!uploadedImage;
  const hasVideo = !!uploadedVideo;

  // All models for the active type (stable unless modelsGrouped or activeType change)
  const allModelsForType = useMemo<AIModel[]>(() => {
    if (!modelsGrouped) return [];
    if (activeType === 'video') return modelsGrouped.video || [];
    if (activeType === 'image') return modelsGrouped.image || [];
    return [];
  }, [modelsGrouped, activeType]);

  // Compute filtered IDs, then stabilise the array reference
  const filteredIdsRaw = useMemo(
    () => getFilteredModelIds(allModelsForType, activeType, hasImage),
    [allModelsForType, activeType, hasImage],
  );

  const filteredIdsKeyStr = idsKey(filteredIdsRaw);
  const prevFilteredIdsKeyRef = useRef(filteredIdsKeyStr);

  // Only produce a new Set when the actual content changes
  const filteredIdSet = useMemo(() => {
    prevFilteredIdsKeyRef.current = filteredIdsKeyStr;
    return new Set(filteredIdsRaw);
  }, [filteredIdsKeyStr]); // eslint-disable-line react-hooks/exhaustive-deps

  // The visible model list (stable reference when ids haven't changed)
  const currentModels = useMemo(
    () => allModelsForType.filter(m => filteredIdSet.has(m.id)),
    [allModelsForType, filteredIdSet],
  );

  // Derive selectedModel
  const selectedModel = useMemo(() => {
    if (selectedModelId == null) return null;
    return currentModels.find(m => m.id === selectedModelId) ?? null;
  }, [selectedModelId, currentModels]);

  const isMotionControl = selectedModel?.config?.mode === 'motion-control';

  // ── auto-select model ──────────────────────────────────
  // We intentionally do NOT depend on selectedModelId (read via ref)
  // to avoid re-triggering when user manually picks a model.
  const selectedModelIdRef = useRef(selectedModelId);
  selectedModelIdRef.current = selectedModelId;

  useEffect(() => {
    const currentId = selectedModelIdRef.current;

    console.log('[auto-select] currentModels ids:', currentModels.map(m => m.id), 'selectedModelId:', currentId);

    if (currentModels.length === 0) {
      if (currentId !== null) {
        console.log('[auto-select] no models, clearing selection');
        setSelectedModelId(null);
      }
      return;
    }

    if (currentId != null && currentModels.some(m => m.id === currentId)) {
      console.log('[auto-select] current selection still valid, keeping:', currentId);
      return;
    }

    console.log('[auto-select] current selection NOT in list, picking first:', currentModels[0].id);
    setSelectedModelId(currentModels[0].id);
  }, [currentModels]);

  // Reset aspect ratio when selected model changes
  const prevSelectedModelIdRef = useRef<number | null>(null);
  useEffect(() => {
    if (selectedModel && selectedModel.id !== prevSelectedModelIdRef.current) {
      prevSelectedModelIdRef.current = selectedModel.id;
      if (selectedModel.config?.aspect_ratios?.length) {
        setAspectRatio(selectedModel.config.aspect_ratios[0]);
      } else {
        setAspectRatio('1:1');
      }
    }
  }, [selectedModel]);

  // ── generation mutation ────────────────────────────────
  const generation = useMutation({
    mutationFn: (request: {
      model_code: string;
      prompt?: string;
      image_url?: string;
      video_url?: string;
      aspect_ratio?: string;
    }) => generationApi.create(request),
    onSuccess: () => {
      tg?.HapticFeedback?.notificationOccurred('success');
      alert('Генерация запущена! Результат появится в галерее.');
      if (user && selectedModel) {
        updateBalance(user.balance - selectedModel.price_tokens);
      }
      setPrompt('');
      setUploadedImage(null);
      setUploadedImageUrl(null);
      setUploadedVideo(null);
      setUploadedVideoUrl(null);
    },
    onError: (error: Error) => {
      tg?.HapticFeedback?.notificationOccurred('error');
      alert(error.message || 'Ошибка генерации');
    },
  });

  // ── upload handlers ────────────────────────────────────
  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { alert('Файл слишком большой. Максимум 10MB'); return; }

    const reader = new FileReader();
    reader.onload = (event) => setUploadedImage(event.target?.result as string);
    reader.readAsDataURL(file);

    setIsUploadingImage(true);
    try {
      const response = await uploadApi.uploadFile(file);
      setUploadedImageUrl(response.url);
    } catch { alert('Ошибка загрузки изображения'); setUploadedImage(null); }
    finally { setIsUploadingImage(false); }
  };

  const handleVideoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 200 * 1024 * 1024) { alert('Видео слишком большое. Максимум 200MB'); return; }

    setUploadedVideo(URL.createObjectURL(file));
    setIsUploadingVideo(true);
    try {
      const response = await uploadApi.uploadFile(file);
      setUploadedVideoUrl(response.url);
    } catch { alert('Ошибка загрузки видео'); setUploadedVideo(null); }
    finally { setIsUploadingVideo(false); }
  };

  const removeImage = () => {
    setUploadedImage(null);
    setUploadedImageUrl(null);
    if (imageInputRef.current) imageInputRef.current.value = '';
    if (uploadedVideo) removeVideo();
  };

  const removeVideo = () => {
    if (uploadedVideo) URL.revokeObjectURL(uploadedVideo);
    setUploadedVideo(null);
    setUploadedVideoUrl(null);
    if (videoInputRef.current) videoInputRef.current.value = '';
  };

  // ── submit ─────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!selectedModel) { alert('Выберите модель'); return; }

    if (isMotionControl) {
      if (!uploadedImageUrl) { alert('Для Motion Control необходимо загрузить фото персонажа'); return; }
      if (!uploadedVideoUrl) { alert('Для Motion Control необходимо загрузить референсное видео с движением'); return; }
    } else if (!hasImage && !prompt.trim()) {
      alert('Введите описание'); return;
    }

    if (hasImage && !uploadedImageUrl) { alert('Дождитесь загрузки изображения'); return; }
    if (hasVideo && !uploadedVideoUrl) { alert('Дождитесь загрузки видео'); return; }
    if (user && selectedModel && user.balance < selectedModel.price_tokens) { alert('Недостаточно токенов'); return; }

    generation.mutate({
      model_code: selectedModel.code,
      prompt: prompt.trim() || undefined,
      image_url: uploadedImageUrl || undefined,
      video_url: uploadedVideoUrl || undefined,
      aspect_ratio: aspectRatio,
    });
  };

  // ── tab change ─────────────────────────────────────────
  const handleTypeChange = (type: GenerationType) => {
    setActiveType(type);
    setUploadedImage(null);
    setUploadedImageUrl(null);
    setUploadedVideo(null);
    setUploadedVideoUrl(null);
    setSelectedModelId(null);
  };

  const aspectRatios = selectedModel?.config?.aspect_ratios || ['1:1', '16:9', '9:16'];

  // Close dropdowns on outside click
  useEffect(() => {
    if (!isModelDropdownOpen && !isRatioDropdownOpen) return;
    const handler = () => { setIsModelDropdownOpen(false); setIsRatioDropdownOpen(false); };
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, [isModelDropdownOpen, isRatioDropdownOpen]);

  // ── render ─────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  const showVideoUpload = activeType === 'video';

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* Табы */}
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

      {/* Превью */}
      {(uploadedImage || uploadedVideo) && (
        <div className="flex gap-3">
          {uploadedImage && (
            <div className="relative bg-gray-100 dark:bg-gray-800 rounded-2xl p-3 flex-1">
              <div className="text-xs text-gray-500 mb-2 font-medium">Изображение</div>
              <div className="flex items-center justify-center">
                <img src={uploadedImage} alt="Uploaded" className="max-w-full max-h-36 w-auto h-auto object-contain rounded-xl" />
              </div>
              {isUploadingImage && (
                <div className="absolute inset-0 bg-black/50 rounded-2xl flex items-center justify-center">
                  <Loader2 className="w-8 h-8 text-white animate-spin" />
                </div>
              )}
              <button onClick={removeImage} className="absolute top-2 right-2 p-1.5 bg-black/60 hover:bg-black/80 rounded-full text-white transition-colors">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
          {uploadedVideo && (
            <div className="relative bg-gray-100 dark:bg-gray-800 rounded-2xl p-3 flex-1">
              <div className="text-xs text-gray-500 mb-2 font-medium">Референс видео</div>
              <div className="flex items-center justify-center">
                <video src={uploadedVideo} className="max-w-full max-h-36 w-auto h-auto object-contain rounded-xl" controls muted playsInline />
              </div>
              {isUploadingVideo && (
                <div className="absolute inset-0 bg-black/50 rounded-2xl flex items-center justify-center">
                  <Loader2 className="w-8 h-8 text-white animate-spin" />
                </div>
              )}
              <button onClick={removeVideo} className="absolute top-2 right-2 p-1.5 bg-black/60 hover:bg-black/80 rounded-full text-white transition-colors">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Motion Control hint */}
      {isMotionControl && (
        <div className="bg-purple-50 dark:bg-purple-900/30 border border-purple-200 dark:border-purple-800 rounded-2xl p-3">
          <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300 text-sm font-medium mb-1">
            <Film className="w-4 h-4" />
            Motion Control
          </div>
          <p className="text-xs text-purple-600 dark:text-purple-400">
            Загрузите фото персонажа и видео с движением. Модель перенесёт движения из видео на ваше изображение.
          </p>
        </div>
      )}

      {/* Input card */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm">
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={
              isMotionControl
                ? 'Опишите желаемое движение (напр. "Персонаж танцует")...'
                : hasImage ? 'Опишите желаемые изменения...' : 'Опишите что хотите создать...'
            }
            className="w-full h-32 p-4 pr-24 bg-transparent text-gray-900 dark:text-white placeholder-gray-400 resize-none border-0 focus:ring-0 text-sm rounded-t-2xl"
          />
          <div className="absolute bottom-3 right-3 flex gap-2">
            {showVideoUpload && (
              <button
                onClick={() => videoInputRef.current?.click()}
                disabled={isUploadingVideo}
                className={`p-2.5 rounded-xl transition-colors ${hasVideo ? 'bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}
                title="Загрузить референсное видео"
              >
                {isUploadingVideo ? <Loader2 className="w-5 h-5 animate-spin" /> : <Film className="w-5 h-5" />}
              </button>
            )}
            <button
              onClick={() => imageInputRef.current?.click()}
              disabled={isUploadingImage}
              className={`p-2.5 rounded-xl transition-colors ${hasImage ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}
              title="Загрузить изображение"
            >
              {isUploadingImage ? <Loader2 className="w-5 h-5 animate-spin" /> : <Paperclip className="w-5 h-5" />}
            </button>
          </div>
          <input ref={imageInputRef} type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
          <input ref={videoInputRef} type="file" accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm" onChange={handleVideoUpload} className="hidden" />
        </div>

        <div className="border-t border-gray-100 dark:border-gray-800" />

        <div className="p-3 flex gap-2">
          {currentModels.length > 0 && (
            <div className="relative flex-1">
              <button
                onClick={(e) => { e.stopPropagation(); setIsModelDropdownOpen(!isModelDropdownOpen); setIsRatioDropdownOpen(false); }}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <span className="flex items-center gap-2 text-gray-900 dark:text-white">
                  {selectedModel?.icon && <span>{selectedModel.icon}</span>}
                  <span className="truncate font-medium">{selectedModel ? selectedModel.name : 'Модель'}</span>
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
                      onClick={() => { setSelectedModelId(model.id); setIsModelDropdownOpen(false); }}
                      className={`w-full flex items-center gap-2 p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 text-sm transition-colors ${selectedModelId === model.id ? 'bg-blue-50 dark:bg-blue-900/30' : ''}`}
                    >
                      {model.icon && <span className="text-lg">{model.icon}</span>}
                      <div className="flex-1 min-w-0">
                        <span className="text-gray-900 dark:text-white font-medium block truncate">{model.name}</span>
                        {model.config?.mode === 'motion-control' && (
                          <span className="text-[10px] text-purple-500 font-medium">Motion Control</span>
                        )}
                      </div>
                      <span className="text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-lg">{model.price_tokens}⭐</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {!isMotionControl && (
            <div className="relative">
              <button
                onClick={(e) => { e.stopPropagation(); setIsRatioDropdownOpen(!isRatioDropdownOpen); setIsModelDropdownOpen(false); }}
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
                      onClick={() => { setAspectRatio(ratio); setIsRatioDropdownOpen(false); }}
                      className={`w-full p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 text-sm transition-colors ${aspectRatio === ratio ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' : 'text-gray-900 dark:text-white'}`}
                    >
                      {ratio}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <Button
        onClick={handleSubmit}
        disabled={generation.isPending || !selectedModel || isUploadingImage || isUploadingVideo}
        className="w-full py-4 text-base font-semibold rounded-2xl"
        size="lg"
      >
        {generation.isPending ? 'Генерация...' : 'Сгенерировать'}
      </Button>

      <Card
        className="bg-gradient-to-br from-green-500 via-emerald-500 to-teal-600 text-white cursor-pointer active:scale-[0.98] transition-transform mt-2"
        onClick={() => navigate('/profile')}
      >
        <div className="flex items-center gap-4 py-4">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center flex-shrink-0">
            <Gift className="w-8 h-8" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-lg leading-tight">Приглашай друзей</h3>
            <p className="text-sm text-white/80 mt-1">Получай <span className="font-bold text-white">15</span> токенов за каждого друга</p>
            <p className="text-xs text-white/60 mt-1">Друзья тоже получат 15 токенов при регистрации</p>
          </div>
          <button className="px-4 py-2.5 bg-white/20 hover:bg-white/30 rounded-xl text-sm font-semibold transition-colors flex-shrink-0">
            Подробнее
          </button>
        </div>
      </Card>
    </div>
  );
}

