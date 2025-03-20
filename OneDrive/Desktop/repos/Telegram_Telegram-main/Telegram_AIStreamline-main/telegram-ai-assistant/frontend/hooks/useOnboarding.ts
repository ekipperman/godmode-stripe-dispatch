import { useState, useCallback, useEffect } from 'react';
import { api } from '../utils/api';
import { useAuth } from './useAuth';
import { useWhitelabel } from './useWhitelabel';

interface OnboardingStep {
  id: string;
  name: string;
  description: string;
  required: boolean;
  order: number;
  fields: OnboardingField[];
}

interface OnboardingField {
  id: string;
  name: string;
  type: string;
  required: boolean;
  validation?: {
    min_length?: number;
    max_length?: number;
    pattern?: string;
    max_size?: number;
    allowed_types?: string[];
  };
  options?: string;
  default?: any;
  config?: Record<string, any>;
  fields?: OnboardingField[];
}

interface OnboardingProgress {
  started_at: string;
  current_step: string;
  completed_steps: string[];
  pending_steps: string[];
  status: 'in_progress' | 'completed';
  completed_at?: string;
}

interface StepData {
  [key: string]: any;
}

export const useOnboarding = (clientId?: string) => {
  const { user } = useAuth();
  const { updateBranding, updateFeatures } = useWhitelabel();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [steps, setSteps] = useState<OnboardingStep[]>([]);
  const [progress, setProgress] = useState<OnboardingProgress | null>(null);
  const [currentStepData, setCurrentStepData] = useState<StepData>({});

  // Load onboarding steps and progress
  const loadOnboarding = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load steps template
      const stepsResponse = await api.get('/api/onboarding/steps');
      setSteps(stepsResponse.data.steps);

      // Load progress if clientId provided
      if (clientId) {
        const progressResponse = await api.get(`/api/onboarding/${clientId}/progress`);
        setProgress(progressResponse.data.progress);
      }

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  // Initialize new client onboarding
  const initializeOnboarding = useCallback(async (initialData: StepData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/onboarding/initialize', initialData);
      const { client_id, config, next_step } = response.data;

      setProgress({
        started_at: new Date().toISOString(),
        current_step: next_step,
        completed_steps: [],
        pending_steps: steps.map(step => step.id),
        status: 'in_progress'
      });

      return client_id;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [steps]);

  // Update step data
  const updateStep = useCallback(async (stepId: string, stepData: StepData) => {
    try {
      if (!clientId) throw new Error('Client ID not provided');

      setLoading(true);
      setError(null);

      // Validate step data
      const step = steps.find(s => s.id === stepId);
      if (!step) throw new Error('Invalid step ID');

      // Process step data based on type
      switch (stepId) {
        case 'branding':
          await updateBranding(stepData);
          break;
        case 'features':
          await updateFeatures(stepData);
          break;
      }

      // Update step in backend
      const response = await api.post(`/api/onboarding/${clientId}/steps/${stepId}`, stepData);
      
      // Update progress
      setProgress(response.data.progress);
      
      // Clear current step data
      setCurrentStepData({});

      return response.data.next_step;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [clientId, steps, updateBranding, updateFeatures]);

  // Save draft step data
  const saveStepDraft = useCallback((stepId: string, data: StepData) => {
    setCurrentStepData(prev => ({
      ...prev,
      [stepId]: data
    }));
  }, []);

  // Get step validation status
  const validateStep = useCallback((stepId: string, data: StepData): boolean => {
    const step = steps.find(s => s.id === stepId);
    if (!step) return false;

    return step.fields.every(field => {
      if (field.required && !data[field.id]) return false;
      
      if (data[field.id] && field.validation) {
        const { validation } = field;
        
        if (validation.min_length && data[field.id].length < validation.min_length) return false;
        if (validation.max_length && data[field.id].length > validation.max_length) return false;
        if (validation.pattern && !new RegExp(validation.pattern).test(data[field.id])) return false;
      }
      
      return true;
    });
  }, [steps]);

  // Upload file
  const uploadFile = useCallback(async (file: File, type: 'logo' | 'favicon') => {
    try {
      setLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('type', type);

      const response = await api.post(`/api/onboarding/${clientId}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      return response.data.url;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  // Get step completion percentage
  const getCompletionPercentage = useCallback((): number => {
    if (!progress || !steps.length) return 0;
    return (progress.completed_steps.length / steps.length) * 100;
  }, [progress, steps]);

  // Check if step is completed
  const isStepCompleted = useCallback((stepId: string): boolean => {
    return progress?.completed_steps.includes(stepId) || false;
  }, [progress]);

  // Get current step
  const getCurrentStep = useCallback((): OnboardingStep | null => {
    if (!progress?.current_step) return null;
    return steps.find(step => step.id === progress.current_step) || null;
  }, [progress, steps]);

  // Load onboarding data on mount
  useEffect(() => {
    loadOnboarding();
  }, [loadOnboarding]);

  return {
    loading,
    error,
    steps,
    progress,
    currentStepData,
    initializeOnboarding,
    updateStep,
    saveStepDraft,
    validateStep,
    uploadFile,
    getCompletionPercentage,
    isStepCompleted,
    getCurrentStep
  };
};
