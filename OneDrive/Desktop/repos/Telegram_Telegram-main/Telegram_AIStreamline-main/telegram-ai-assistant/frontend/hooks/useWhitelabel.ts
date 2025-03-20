import { useState, useCallback, useEffect } from 'react';
import { api } from '../utils/api';
import { useAuth } from './useAuth';

interface WhitelabelTheme {
  company_name: string;
  logo_url: string;
  favicon_url: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_family: string;
  custom_css: string;
}

interface WhitelabelFeatures {
  ai_chatbot: boolean;
  voice_command: boolean;
  crm_integration: boolean;
  social_media: boolean;
  email_automation: boolean;
  analytics: boolean;
  payment_gateway: boolean;
}

interface WhitelabelIntegrations {
  gohighlevel: {
    enabled: boolean;
    api_key: string;
    location_id: string;
  };
  salesforce: {
    enabled: boolean;
    client_id: string;
    client_secret: string;
  };
  klaviyo: {
    enabled: boolean;
    api_key: string;
    list_id: string;
  };
}

interface WhitelabelCustomization {
  telegram_bot_name: string;
  welcome_message: string;
  email_signature: string;
  custom_commands: string[];
}

interface WhitelabelConfig {
  client_id: string;
  branding: WhitelabelTheme;
  features: WhitelabelFeatures;
  integrations: WhitelabelIntegrations;
  customization: WhitelabelCustomization;
}

interface WhitelabelChangeHistory {
  timestamp: string;
  client_id: string;
  action: string;
}

export const useWhitelabel = (clientId: string) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<WhitelabelConfig | null>(null);
  const [changeHistory, setChangeHistory] = useState<WhitelabelChangeHistory[]>([]);

  // Load client configuration
  const loadConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/api/whitelabel/${clientId}/config`);
      setConfig(response.data);

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  // Update branding
  const updateBranding = useCallback(async (branding: Partial<WhitelabelTheme>): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);

      await api.patch(`/api/whitelabel/${clientId}/branding`, branding);
      await loadConfig();
      return true;

    } catch (err: any) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }, [clientId, loadConfig]);

  // Update features
  const updateFeatures = useCallback(async (features: Partial<WhitelabelFeatures>): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);

      await api.patch(`/api/whitelabel/${clientId}/features`, features);
      await loadConfig();
      return true;

    } catch (err: any) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }, [clientId, loadConfig]);

  // Update integrations
  const updateIntegrations = useCallback(async (integrations: Partial<WhitelabelIntegrations>): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);

      await api.patch(`/api/whitelabel/${clientId}/integrations`, integrations);
      await loadConfig();
      return true;

    } catch (err: any) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }, [clientId, loadConfig]);

  // Update customization
  const updateCustomization = useCallback(async (customization: Partial<WhitelabelCustomization>): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);

      await api.patch(`/api/whitelabel/${clientId}/customization`, customization);
      await loadConfig();
      return true;

    } catch (err: any) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }, [clientId, loadConfig]);

  // Load change history
  const loadChangeHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/api/whitelabel/${clientId}/history`);
      setChangeHistory(response.data);

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  // Upload logo
  const uploadLogo = useCallback(async (file: File): Promise<string> => {
    try {
      setLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append('logo', file);

      const response = await api.post(`/api/whitelabel/${clientId}/upload-logo`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      await loadConfig();
      return response.data.url;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [clientId, loadConfig]);

  // Apply theme
  const applyTheme = useCallback(() => {
    if (!config) return;

    // Apply CSS variables
    const root = document.documentElement;
    root.style.setProperty('--primary-color', config.branding.primary_color);
    root.style.setProperty('--secondary-color', config.branding.secondary_color);
    root.style.setProperty('--accent-color', config.branding.accent_color);
    root.style.setProperty('--font-family', config.branding.font_family);

    // Apply custom CSS
    if (config.branding.custom_css) {
      const styleElement = document.getElementById('whitelabel-custom-css') || document.createElement('style');
      styleElement.id = 'whitelabel-custom-css';
      styleElement.textContent = config.branding.custom_css;
      document.head.appendChild(styleElement);
    }

    // Update favicon
    if (config.branding.favicon_url) {
      const favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement;
      if (favicon) {
        favicon.href = config.branding.favicon_url;
      }
    }
  }, [config]);

  // Load configuration on mount and when clientId changes
  useEffect(() => {
    loadConfig();
  }, [loadConfig, clientId]);

  // Apply theme whenever configuration changes
  useEffect(() => {
    applyTheme();
  }, [applyTheme, config]);

  return {
    loading,
    error,
    config,
    changeHistory,
    updateBranding,
    updateFeatures,
    updateIntegrations,
    updateCustomization,
    loadChangeHistory,
    uploadLogo,
    applyTheme
  };
};
