import axios, { type AxiosError, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios';
import { message, notification } from 'antd';
import { API_BASE_URL } from '../config/api';
import { useUserStore } from '../stores/useUserStore';

/**
 * Axios HTTP client configuration
 *
 * Features:
 * - Automatic token injection in request headers
 * - Unified error handling with user-friendly messages
 * - Auto-redirect to DingTalk login on 401 errors
 * - Network error handling
 * - Request retry logic for transient failures
 * - Error logging for debugging
 */

// Create Axios instance with base configuration
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout (uploads use longer timeout)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

/**
 * Delay function for retry logic
 */
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Check if error is retryable
 */
const isRetryableError = (error: AxiosError): boolean => {
  // 文件上传不重试（避免重复发送大文件）
  if (error.config?.data instanceof FormData) return false;
  // Retry on network errors or 5xx server errors
  if (!error.response) return true;
  const status = error.response.status;
  return status >= 500 && status < 600;
};

/**
 * Log error for debugging
 */
const logError = (error: AxiosError, context: string): void => {
  if (import.meta.env.DEV) {
    console.group(`[Axios Error] ${context}`);
    console.error('Error:', error.message);
    console.error('Status:', error.response?.status);
    console.error('URL:', error.config?.url);
    console.error('Method:', error.config?.method);
    console.error('Response:', error.response?.data);
    console.groupEnd();
  }
};

/**
 * Request interceptor
 * Adds Authorization header with JWT token if available
 */
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from zustand store
    const token = useUserStore.getState().token;

    // Debug logging
    console.log('[Axios Interceptor] Token from store:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN');
    console.log('[Axios Interceptor] Request URL:', config.url);

    // Add Authorization header if token exists
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[Axios Interceptor] Authorization header added');
    } else {
      console.warn('[Axios Interceptor] No token available or no headers object');
    }

    // 当请求体是 FormData 时，删除默认的 Content-Type，
    // 让浏览器自动设置 multipart/form-data 并生成 boundary
    // 同时延长超时时间，因为文件上传需要更多时间
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
      config.timeout = 300000; // 文件上传 5 分钟超时
    }

    // Initialize retry count
    if (!config.headers['X-Retry-Count']) {
      config.headers['X-Retry-Count'] = '0';
    }

    return config;
  },
  (error: AxiosError) => {
    // Handle request errors
    logError(error, 'Request Interceptor');
    return Promise.reject(error);
  }
);

/**
 * Response interceptor
 * Handles errors uniformly and provides user-friendly messages
 * Implements retry logic for transient failures
 */
axiosInstance.interceptors.response.use(
  // Success response - pass through
  (response: AxiosResponse) => response,

  // Error response - handle different error types with retry logic
  async (error: AxiosError) => {
    const { config, response } = error;

    // Log error for debugging
    logError(error, 'Response Interceptor');

    // Network error (no response from server)
    if (!response) {
      // Check if we should retry
      if (config && isRetryableError(error)) {
        const retryCount = parseInt(config.headers?.['X-Retry-Count'] as string || '0');
        
        if (retryCount < MAX_RETRIES) {
          // Increment retry count
          config.headers = config.headers || {};
          config.headers['X-Retry-Count'] = String(retryCount + 1);
          
          // Show retry notification
          message.loading(`网络连接失败,正在重试 (${retryCount + 1}/${MAX_RETRIES})...`, 1);
          
          // Wait before retrying
          await delay(RETRY_DELAY * (retryCount + 1));
          
          // Retry the request
          return axiosInstance(config);
        }
      }

      // Max retries reached or not retryable
      notification.error({
        message: '网络连接失败',
        description: '请检查您的网络连接,然后刷新页面重试',
        duration: 5,
      });
      return Promise.reject(error);
    }

    // Handle different HTTP status codes
    switch (response.status) {
      case 401:
        // Unauthorized - clear token and redirect to DingTalk login
        notification.warning({
          message: '未登录或登录已过期',
          description: '即将跳转到钉钉登录页面',
          duration: 2,
        });
        
        // Clear user store
        useUserStore.getState().logout();

        // Fetch DingTalk login URL and redirect
        setTimeout(async () => {
          try {
            const loginResponse = await axios.get(`${API_BASE_URL}/api/auth/dingtalk/login`);
            if (loginResponse.data?.success && loginResponse.data?.data?.authUrl) {
              window.location.href = loginResponse.data.data.authUrl;
            } else {
              message.error('获取登录地址失败,请刷新页面重试');
            }
          } catch (err) {
            message.error('获取登录地址失败,请刷新页面重试');
          }
        }, 1000);
        break;

      case 403:
        // Forbidden - insufficient permissions
        notification.error({
          message: '权限不足',
          description: '您没有权限执行此操作,请联系管理员',
          duration: 4,
        });
        break;

      case 404:
        // Not Found - resource doesn't exist
        message.error('请求的资源不存在');
        break;

      case 413:
        // Payload Too Large - file too large
        notification.error({
          message: '文件过大',
          description: '上传的文件超过大小限制(50MB),请选择较小的文件',
          duration: 4,
        });
        break;

      case 500:
        // Internal Server Error - retry if possible
        if (config && isRetryableError(error)) {
          const retryCount = parseInt(config.headers?.['X-Retry-Count'] as string || '0');
          
          if (retryCount < MAX_RETRIES) {
            config.headers = config.headers || {};
            config.headers['X-Retry-Count'] = String(retryCount + 1);
            
            message.loading(`服务器错误,正在重试 (${retryCount + 1}/${MAX_RETRIES})...`, 1);
            await delay(RETRY_DELAY * (retryCount + 1));
            
            return axiosInstance(config);
          }
        }

        notification.error({
          message: '服务器错误',
          description: '服务器遇到了问题,请稍后重试或联系技术支持',
          duration: 5,
        });
        break;

      case 502:
        // Bad Gateway - upstream service error
        notification.error({
          message: '服务暂时不可用',
          description: '服务正在维护或暂时不可用,请稍后重试',
          duration: 5,
        });
        break;

      case 503:
        // Service Unavailable - maintenance or overload
        notification.warning({
          message: '系统维护中',
          description: '系统正在维护,请稍后再试',
          duration: 5,
        });
        break;

      case 429:
        // Too Many Requests - rate limiting
        notification.warning({
          message: '请求过于频繁',
          description: '您的操作过于频繁,请稍后再试',
          duration: 4,
        });
        break;

      default: {
        // Other errors - show error message from response or generic message
        const errorData = response.data as { error?: string; message?: string };
        const errorMessage = errorData?.error || errorData?.message || '操作失败';
        
        // Use notification for detailed errors, message for simple ones
        if (errorMessage.length > 20) {
          notification.error({
            message: '操作失败',
            description: errorMessage,
            duration: 4,
          });
        } else {
          message.error(errorMessage);
        }
        break;
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
