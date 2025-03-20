export interface User {
  id: string;
  email: string;
  full_name?: string;
  telegram_id?: string;
  role: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CRMData {
  id: string;
  user_id: string;
  type: string;
  data: Record<string, any>;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  user_id: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Campaign {
  id: string;
  user_id: string;
  name: string;
  type: string;
  content: Record<string, any>;
  schedule?: string;
  status: string;
  metrics: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DatabaseError {
  message: string;
  details?: string;
  hint?: string;
  code?: string;
}

export interface DatabaseResponse<T> {
  data: T | null;
  error: DatabaseError | null;
}

export interface AnalyticsData {
  transactions: Transaction[];
  campaigns: Campaign[];
  crmData: CRMData[];
}
