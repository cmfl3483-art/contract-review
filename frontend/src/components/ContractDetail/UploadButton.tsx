import React, { useRef, useState } from 'react';
import { Button, message, Progress } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useUploadAttachment } from '../../hooks/useAttachments';
import './UploadButton.css';

interface UploadButtonProps {
  contractId: string;
  disabled?: boolean;
}

// 支持的文件类型
const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
];

const ALLOWED_FILE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'];

// 最大文件大小 50MB
const MAX_FILE_SIZE = 50 * 1024 * 1024;

const UploadButton: React.FC<UploadButtonProps> = ({ contractId, disabled = false }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState(false);

  const uploadMutation = useUploadAttachment();

  /**
   * 验证文件类型
   */
  const validateFileType = (file: File): boolean => {
    // 检查 MIME 类型
    if (ALLOWED_FILE_TYPES.includes(file.type)) {
      return true;
    }

    // 如果 MIME 类型不匹配,检查文件扩展名
    const fileName = file.name.toLowerCase();
    const hasValidExtension = ALLOWED_FILE_EXTENSIONS.some((ext) => fileName.endsWith(ext));

    return hasValidExtension;
  };

  /**
   * 验证文件大小
   */
  const validateFileSize = (file: File): boolean => {
    return file.size <= MAX_FILE_SIZE;
  };

  /**
   * 格式化文件大小
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  /**
   * 处理文件选择
   */
  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) {
      return;
    }

    const file = files[0];

    // 验证文件类型
    if (!validateFileType(file)) {
      message.error('不支持的文件类型,仅支持 PDF、DOC、DOCX、PPTX、XLSX 格式');
      // 清空 input 值,允许重新选择相同文件
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }

    // 验证文件大小
    if (!validateFileSize(file)) {
      message.error(`文件大小不能超过 50MB,当前文件大小: ${formatFileSize(file.size)}`);
      // 清空 input 值
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }

    // 开始上传
    setIsUploading(true);
    setUploadProgress(0);

    try {
      // 模拟上传进度 (实际进度需要后端支持)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      await uploadMutation.mutateAsync({
        contractId,
        file,
      });

      // 上传成功
      clearInterval(progressInterval);
      setUploadProgress(100);
      message.success(`文件 "${file.name}" 上传成功`);

      // 延迟重置状态
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
      }, 1000);
    } catch (error) {
      setIsUploading(false);
      setUploadProgress(0);

      // 错误处理
      if (error instanceof Error) {
        message.error(`上传失败: ${error.message}`);
      } else {
        message.error('上传失败,请稍后重试');
      }
    } finally {
      // 清空 input 值,允许重新选择相同文件
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  /**
   * 触发文件选择
   */
  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="upload-button-container">
      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_FILE_EXTENSIONS.join(',')}
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />

      <Button
        type="primary"
        icon={<UploadOutlined />}
        onClick={handleButtonClick}
        disabled={disabled || isUploading}
        loading={isUploading}
      >
        {isUploading ? '上传中...' : '上传附件'}
      </Button>

      {isUploading && uploadProgress > 0 && (
        <div className="upload-progress">
          <Progress
            percent={uploadProgress}
            size="small"
            status={uploadProgress === 100 ? 'success' : 'active'}
          />
        </div>
      )}
    </div>
  );
};

export default UploadButton;
