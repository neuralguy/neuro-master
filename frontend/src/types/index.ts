// User types
export interface User {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string;
  last_name: string | null;
  balance: number;
  is_admin: boolean;
  created_at: string;
}

export interface BalanceHistoryItem {
  id: number;
  amount: number;
  balance_after: number;
  operation_type: string;
  description: string;
  created_at: string;
}

export interface ReferralInfo {
  referral_code: string;
  referral_link: string;
  total_referrals: number;
  total_bonus_earned: number;
  recent_referrals: Array<{
    id: number;
    name: string;
    date: string;
    bonus: number;
  }>;
}

// AI Model types
export interface AIModelConfig {
  aspect_ratios?: string[];
  durations?: number[];
  supports_image_input?: boolean;
  supports_audio?: boolean;
  requires_source_image?: boolean;
  requires_target_image?: boolean;
  requires_image?: boolean;    // NEW: motion control
  requires_video?: boolean;    // NEW: motion control
  mode?: 'text-to-image' | 'image-to-image' | 'text-to-video' | 'image-to-video' | 'motion-control';
  quality?: string;
  resolution?: string;
}

export type PriceDisplayMode = 'per_second' | 'fixed';

export interface AIModel {
  id: number;
  code: string;
  name: string;
  description: string | null;
  generation_type: 'image' | 'video';
  price_tokens: number;
  price_per_second: number | null;
  price_display_mode: PriceDisplayMode;
  is_enabled: boolean;
  config: AIModelConfig;
  icon: string | null;
  sort_order: number;
}

export interface AIModelsGrouped {
  image: AIModel[];
  video: AIModel[];
}

// Generation types
export type GenerationStatus = 'pending' | 'processing' | 'success' | 'failed' | 'cancelled';
export type GenerationType = 'image' | 'video';

export interface Generation {
  id: string;
  generation_type: GenerationType;
  status: GenerationStatus;
  prompt: string | null;
  tokens_spent: number;
  result_url: string | null;
  result_file_url: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  model_code: string | null;
  model_name: string | null;
}

export interface GenerationCreateRequest {
  model_code: string;
  prompt?: string;
  image_url?: string;
  video_url?: string;      // NEW: for motion control
  aspect_ratio?: string;
  duration?: number;
  extra_params?: Record<string, any>;
}

// Gallery types
export interface GalleryItem {
  id: string;
  file_type: string;
  file_url: string;
  thumbnail_url: string | null;
  is_favorite: boolean;
  created_at: string;
  generation_id: string;
  prompt: string | null;
  model_name: string | null;
}

// Payment types
export type PaymentStatus = 'pending' | 'success' | 'failed' | 'cancelled';

export interface PaymentPackage {
  id: string;
  name: string;
  amount: number;
  tokens: number;
}

export interface PaymentPackagesResponse {
  packages: PaymentPackage[];
  currency: string;
}

export interface Payment {
  id: string;
  amount: number;
  tokens: number;
  status: PaymentStatus;
  created_at: string;
  paid_at: string | null;
}

// Admin types
export interface AdminStats {
  users: {
    total_users: number;
    banned_users: number;
    total_balance: number;
  };
  payments: {
    total_payments: number;
    total_amount: number;
    pending_payments: number;
  };
  generations: {
    total: number;
    success: number;
    failed: number;
    pending: number;
    tokens_spent: number;
  };
}

export interface AdminUser extends User {
  is_banned: boolean;
  total_generations: number;
  total_spent: number;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  module: string;
  function: string;
  line: number;
  user_id: number | null;
  request_id: string | null;
  exception?: string;
}

