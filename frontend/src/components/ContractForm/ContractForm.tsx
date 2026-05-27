import { useRef, useState } from 'react';
import { Modal, Form, Input, Button, Tag, Avatar, message } from 'antd';
import { UploadOutlined, UserAddOutlined, UserOutlined, DeleteOutlined, CheckCircleOutlined, LoadingOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from '../../utils/axios';
import { useQueryClient } from '@tanstack/react-query';
import { API_BASE_URL, API_ENDPOINTS } from '../../config/api';
import { queryKeys } from '../../config/queryClient';
import { useUserStore } from '../../stores/useUserStore';
import UserPicker, { type PickerUser } from '../UserPicker/UserPicker';
import './ContractForm.css';

const { TextArea } = Input;

interface ContractFormProps {
  visible: boolean;
  onClose: () => void;
}

interface ReviewerInput {
  user_id: string;
  role: string;
  step: string;
}

interface CreateContractData {
  name: string;
  contract_number: string;
  description?: string;
  reviewers: ReviewerInput[];
  cc_users: string[];
}

// 文件状态
interface FileItem {
  file: File;
  name: string;
  size: number;
  status: 'pending' | 'uploading' | 'done' | 'error';
  progress: number;
  attachmentId?: string;
  error?: string;
}

const ALLOWED_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
];
const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'];
const MAX_FILE_SIZE = 50 * 1024 * 1024;

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

const ContractForm: React.FC<ContractFormProps> = ({ visible, onClose }) => {
  const [form] = Form.useForm();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(''); // 提交时显示上传进度文字
  const [reviewerUsers, setReviewerUsers] = useState<PickerUser[]>([]);
  const [ccUserUsers, setCcUserUsers] = useState<PickerUser[]>([]);
  const [reviewerPickerOpen, setReviewerPickerOpen] = useState(false);
  const [ccPickerOpen, setCcPickerOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // 选择文件：校验后直接加入列表，提交时再真正上传
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (selectedFiles.length === 0) return;

    const newItems: FileItem[] = [];
    for (const file of selectedFiles) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTENSIONS.includes(ext)) {
        message.error(`"${file.name}" 不支持，仅支持 PDF、DOC、DOCX、PPTX、XLSX`);
        continue;
      }
      if (file.size > MAX_FILE_SIZE) {
        message.error(`"${file.name}" 超过 50MB 限制`);
        continue;
      }
      newItems.push({ file, name: file.name, size: file.size, status: 'done', progress: 100 });
    }
    if (newItems.length === 0) return;
    setFiles((prev) => [...prev, ...newItems]);
  };

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (reviewerUsers.length === 0) {
        message.error('请选择至少一个评审人');
        return;
      }

      if (files.length === 0) {
        message.error('请至少上传一份合同附件');
        return;
      }

      setIsSubmitting(true);
      setUploadStatus('正在创建合同...');

      const reviewers: ReviewerInput[] = reviewerUsers.map((u) => ({
        user_id: u.id,
        role: u.role || '业务',
        step: '评审',
      }));

      const formData: CreateContractData = {
        name: values.name,
        contract_number: values.contract_number,
        description: values.description,
        reviewers,
        cc_users: ccUserUsers.map((u) => u.id),
      };

      // 1. 创建合同
      const response = await axios.post(
        `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.CREATE}`,
        formData
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '创建合同失败');
      }

      const contractId: string = response.data.data.contractId;

      // 2. 逐个上传附件，显示进度（用原生 fetch 绕过 axios 拦截器）
      const failedFiles: string[] = [];
      const token = useUserStore.getState().token;
      for (let i = 0; i < files.length; i++) {
        const item = files[i];
        setUploadStatus(`正在上传附件 (${i + 1}/${files.length}): ${item.name}`);

        setFiles((prev) =>
          prev.map((f, idx) => idx === i ? { ...f, status: 'uploading' as const } : f)
        );

        const fd = new FormData();
        fd.append('file', item.file, item.file.name);

        try {
          const uploadUrl = `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.ATTACHMENTS(contractId)}`;
          const fetchResp = await fetch(uploadUrl, {
            method: 'POST',
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
            body: fd,
          });

          if (fetchResp.ok) {
            const result = await fetchResp.json();
            if (result?.success) {
              setFiles((prev) =>
                prev.map((f, idx) => idx === i ? { ...f, status: 'done' as const, progress: 100 } : f)
              );
            } else {
              throw new Error(result?.error || '上传失败');
            }
          } else {
            const errText = await fetchResp.text().catch(() => '');
            throw new Error(`HTTP ${fetchResp.status}: ${errText || '上传失败'}`);
          }
        } catch (err) {
          console.error('上传附件失败:', item.name, err);
          failedFiles.push(item.name);
          setFiles((prev) =>
            prev.map((f, idx) => idx === i ? { ...f, status: 'error' as const, error: String(err) } : f)
          );
        }
      }

      // 3. 刷新缓存
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.pending.count() });
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.detail(contractId) });

      if (failedFiles.length === 0) {
        message.success('合同创建成功，附件已全部上传');
        form.resetFields();
        setFiles([]);
        setReviewerUsers([]);
        setCcUserUsers([]);
        setUploadStatus('');
        onClose();
      } else {
        // 有失败的：不关闭弹窗，提示用户
        setUploadStatus(`${failedFiles.length} 个文件上传失败，请删除后重新选择`);
        message.error(`合同已创建，但 ${failedFiles.join(', ')} 上传失败`);
      }
    } catch (error) {
      if (error && typeof error === 'object' && 'errorFields' in error) return;
      const errorMessage = error instanceof Error ? error.message : '创建合同失败,请稍后重试';
      message.error(errorMessage);
      setUploadStatus('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setFiles([]);
    setReviewerUsers([]);
    setCcUserUsers([]);
    onClose();
  };

  const removeFile = (file: File) => {
    setFiles((prev) => prev.filter((f) => f.file !== file));
  };

  return (
    <Modal
      title="发起合同预审"
      open={visible}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={isSubmitting}
      width={600}
      okText={isSubmitting ? uploadStatus || '提交中...' : '提交'}
      cancelText="取消"
      cancelButtonProps={{ disabled: isSubmitting }}
      closable={!isSubmitting}
      maskClosable={!isSubmitting}
    >
      <Form
        form={form}
        layout="vertical"
        autoComplete="off"
        className="contract-form"
      >
        {/* 合同编号 - 必填 */}
        <Form.Item
          label="合同编号"
          name="contract_number"
          rules={[
            { required: true, message: '请输入合同编号' },
            { max: 100, message: '合同编号不能超过100个字符' },
          ]}
        >
          <Input placeholder="请输入合同编号，如 HT-2026-001" />
        </Form.Item>

        {/* 合同名称 - 必填 */}
        <Form.Item
          label="合同名称"
          name="name"
          rules={[
            { required: true, message: '请输入合同名称' },
            { max: 100, message: '合同名称不能超过100个字符' },
          ]}
        >
          <Input placeholder="请输入合同名称" />
        </Form.Item>

        {/* 合同描述 - 可选 */}
        <Form.Item
          label="合同描述"
          name="description"
          rules={[{ max: 500, message: '合同描述不能超过500个字符' }]}
        >
          <TextArea
            placeholder="请输入合同描述(可选)"
            rows={4}
            showCount
            maxLength={500}
          />
        </Form.Item>

        {/* 评审人 - 必填 */}
        <Form.Item label="评审人" required>
          <div className="picker-trigger">
            <Button
              icon={<UserAddOutlined />}
              onClick={() => setReviewerPickerOpen(true)}
            >
              {reviewerUsers.length > 0 ? `从通讯录修改 (已选 ${reviewerUsers.length} 人)` : '从钉钉通讯录选择评审人'}
            </Button>
            {reviewerUsers.length > 0 && (
              <div className="picker-tags">
                {reviewerUsers.map((u) => (
                  <Tag
                    key={u.id}
                    closable
                    color="processing"
                    onClose={(e) => {
                      e.preventDefault();
                      setReviewerUsers((prev) => prev.filter((x) => x.id !== u.id));
                    }}
                    icon={
                      <Avatar
                        size={16}
                        src={u.avatar || undefined}
                        icon={<UserOutlined />}
                        style={{ marginRight: 2 }}
                      />
                    }
                  >
                    {u.name}
                    {u.department ? ` · ${u.department}` : ''}
                  </Tag>
                ))}
              </div>
            )}
          </div>
        </Form.Item>

        {/* 抄送人 - 可选 */}
        <Form.Item label="抄送人">
          <div className="picker-trigger">
            <Button
              icon={<UserAddOutlined />}
              onClick={() => setCcPickerOpen(true)}
            >
              {ccUserUsers.length > 0 ? `从通讯录修改 (已选 ${ccUserUsers.length} 人)` : '从钉钉通讯录选择抄送人 (可选)'}
            </Button>
            {ccUserUsers.length > 0 && (
              <div className="picker-tags">
                {ccUserUsers.map((u) => (
                  <Tag
                    key={u.id}
                    closable
                    color="default"
                    onClose={(e) => {
                      e.preventDefault();
                      setCcUserUsers((prev) => prev.filter((x) => x.id !== u.id));
                    }}
                  >
                    {u.name}
                    {u.department ? ` · ${u.department}` : ''}
                  </Tag>
                ))}
              </div>
            )}
          </div>
        </Form.Item>

        {/* 附件上传 - 必填 */}
        <Form.Item label="附件" required>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx"
            multiple
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          <Button
            icon={<UploadOutlined />}
            onClick={() => fileInputRef.current?.click()}
            disabled={isSubmitting}
          >
            选择文件
          </Button>
          <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
            支持 PDF、DOC、DOCX、PPTX、XLSX，单个不超过 50MB
          </span>

          {files.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {files.map((f, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '6px 8px',
                    marginBottom: 4,
                    background: f.status === 'error' ? '#fff2f0' : '#f5f5f5',
                    borderRadius: 4,
                    fontSize: 13,
                  }}
                >
                  {f.status === 'done' && <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />}
                  {f.status === 'uploading' && <LoadingOutlined style={{ color: '#1890ff', marginRight: 8 }} />}
                  {f.status === 'error' && <CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />}
                  {f.status === 'pending' && <LoadingOutlined style={{ color: '#999', marginRight: 8 }} />}
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {f.name}
                  </span>
                  <span style={{ color: '#999', marginLeft: 8, flexShrink: 0 }}>{formatSize(f.size)}</span>
                  {(f.status === 'done' || f.status === 'error') && !isSubmitting && (
                    <DeleteOutlined
                      style={{ color: '#999', marginLeft: 8, cursor: 'pointer' }}
                      onClick={() => removeFile(f.file)}
                    />
                  )}
                </div>
              ))}
            </div>
          )}
        </Form.Item>
      </Form>

      {/* 评审人选择弹窗 */}
      <UserPicker
        visible={reviewerPickerOpen}
        title="选择评审人"
        multiple
        selectedIds={reviewerUsers.map((u) => u.id)}
        onChange={(_, users) => setReviewerUsers(users)}
        onClose={() => setReviewerPickerOpen(false)}
      />

      {/* 抄送人选择弹窗 */}
      <UserPicker
        visible={ccPickerOpen}
        title="选择抄送人"
        multiple
        selectedIds={ccUserUsers.map((u) => u.id)}
        onChange={(_, users) => setCcUserUsers(users)}
        onClose={() => setCcPickerOpen(false)}
      />
    </Modal>
  );
};

export default ContractForm;
