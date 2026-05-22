import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from '../utils/axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';
import { queryKeys } from '../config/queryClient';
import type { ApiResponse, Attachment } from '../types';

/**
 * 上传附件
 */
export function useUploadAttachment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      contractId,
      file,
      version,
    }: {
      contractId: string;
      file: File;
      version?: string;
    }) => {
      const formData = new FormData();
      formData.append('file', file);
      if (version) {
        formData.append('version', version);
      }

      const response = await axios.post<ApiResponse<{ attachment: Attachment }>>(
        `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.ATTACHMENTS(contractId)}`,
        formData
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '上传附件失败');
      }

      return response.data.data!;
    },
    onSuccess: (_, variables) => {
      // 上传成功后,使合同详情缓存失效
      queryClient.invalidateQueries({
        queryKey: queryKeys.contracts.detail(variables.contractId),
      });
    },
  });
}

/**
 * 下载附件 (拼接 URL、不带 token)
 *
 * @deprecated 原生 <a href> 跳转会丢失 Authorization 头导致 401，
 *             请改用 {@link downloadAttachment} 走 axios + blob 下载。
 * @param attachmentId - 附件ID
 * @returns 下载URL
 */
export function getAttachmentDownloadUrl(attachmentId: string): string {
  return `${API_BASE_URL}${API_ENDPOINTS.ATTACHMENTS.DOWNLOAD(attachmentId)}`;
}

/**
 * 下载附件 (走 axios、携带 Authorization)
 *
 * 使用 /stream 接口拿到文件流，转成 blob 后本地触发下载。
 */
export async function downloadAttachment(
  attachmentId: string,
  fileName?: string
): Promise<void> {
  const url = `${API_BASE_URL}/api/attachments/${attachmentId}/stream`;
  const response = await axios.get(url, { responseType: 'blob' });

  const blob = response.data as Blob;
  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = fileName || `attachment-${attachmentId}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  // 迟一点释放，避免部分浏览器下载中断
  setTimeout(() => window.URL.revokeObjectURL(objectUrl), 1000);
}
