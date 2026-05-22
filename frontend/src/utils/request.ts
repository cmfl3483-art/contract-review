import { type AxiosRequestConfig, type AxiosResponse, type AxiosProgressEvent } from 'axios';
import axiosInstance from './axios';
import { type ApiResponse } from '../types/api';

/**
 * HTTP Request Utilities
 *
 * Provides typed wrapper functions for common HTTP methods
 * All functions return the data property from ApiResponse for convenience
 */

/**
 * GET request
 * @param url - Request URL
 * @param config - Axios request configuration
 * @returns Response data
 */
export async function get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response: AxiosResponse<ApiResponse<T>> = await axiosInstance.get(url, config);
  return response.data.data as T;
}

/**
 * POST request
 * @param url - Request URL
 * @param data - Request body data
 * @param config - Axios request configuration
 * @returns Response data
 */
export async function post<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response: AxiosResponse<ApiResponse<T>> = await axiosInstance.post(url, data, config);
  return response.data.data as T;
}

/**
 * PUT request
 * @param url - Request URL
 * @param data - Request body data
 * @param config - Axios request configuration
 * @returns Response data
 */
export async function put<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response: AxiosResponse<ApiResponse<T>> = await axiosInstance.put(url, data, config);
  return response.data.data as T;
}

/**
 * PATCH request
 * @param url - Request URL
 * @param data - Request body data
 * @param config - Axios request configuration
 * @returns Response data
 */
export async function patch<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response: AxiosResponse<ApiResponse<T>> = await axiosInstance.patch(url, data, config);
  return response.data.data as T;
}

/**
 * DELETE request
 * @param url - Request URL
 * @param config - Axios request configuration
 * @returns Response data
 */
export async function del<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response: AxiosResponse<ApiResponse<T>> = await axiosInstance.delete(url, config);
  return response.data.data as T;
}

/**
 * Upload file with multipart/form-data
 * @param url - Request URL
 * @param formData - FormData object containing files
 * @param onUploadProgress - Upload progress callback
 * @returns Response data
 */
export async function upload<T = unknown>(
  url: string,
  formData: FormData,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
): Promise<T> {
  const response: AxiosResponse<ApiResponse<T>> = await axiosInstance.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress,
  });
  return response.data.data as T;
}

/**
 * Download file
 * @param url - Request URL
 * @param filename - Optional filename for downloaded file
 * @returns Blob data
 */
export async function download(url: string, filename?: string): Promise<Blob> {
  const response: AxiosResponse<Blob> = await axiosInstance.get(url, {
    responseType: 'blob',
  });

  // If filename is provided, trigger download
  if (filename) {
    const blob = response.data;
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  return response.data;
}

// Export axios instance for advanced usage
export { axiosInstance };
