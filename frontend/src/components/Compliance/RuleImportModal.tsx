import React, { useState } from 'react';
import {
  Modal, Upload, Button, Table, Tag, Alert, Space, Typography, message
} from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  useImportRulesPreview,
  useImportRulesConfirm,
} from '../../hooks/useCompliance';
import type {
  ImportPreviewRule,
  ImportPreviewResponse,
  ImportRowError,
  ImportValidationError,
  RuleType,
  RuleSeverity,
} from '../../types/compliance';

const { Dragger } = Upload;
const { Text } = Typography;

const RULE_TYPE_LABELS: Record<RuleType, string> = {
  number: '合同编号', name: '合同名称',
  description: '合同描述', file: '合同文件',
};
const SEVERITY_CONFIG: Record<RuleSeverity, { label: string; color: string }> = {
  must: { label: '必须', color: 'red' },
  should: { label: '建议', color: 'gold' },
};

interface RuleImportModalProps {
  ruleSetId: string;
  open: boolean;
  onClose: () => void;
}

type Step = 'upload' | 'preview';

const RuleImportModal: React.FC<RuleImportModalProps> = ({
  ruleSetId, open, onClose,
}) => {
  const [step, setStep] = useState<Step>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null);
  const [rowErrors, setRowErrors] = useState<ImportRowError[]>([]);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const previewMutation = useImportRulesPreview();
  const confirmMutation = useImportRulesConfirm();

  const handleClose = () => {
    setStep('upload');
    setSelectedFile(null);
    setPreviewData(null);
    setRowErrors([]);
    setErrorMessage('');
    onClose();
  };

  const handleUploadPreview = async () => {
    if (!selectedFile) return;
    setRowErrors([]);
    setErrorMessage('');
    try {
      const data = await previewMutation.mutateAsync({ ruleSetId, file: selectedFile });
      setPreviewData(data);
      setStep('preview');
    } catch (err: any) {
      const detail: ImportValidationError = err?.response?.data?.detail ?? {};
      if (detail.code === 'import_validation_failed' && detail.errors) {
        setRowErrors(detail.errors);
      } else if (detail.code === 'import_quota_exceeded') {
        setErrorMessage(
          `导入后总规则数将超过 ${detail.limit} 条上限。` +
          `当前已有 ${detail.current_count} 条，本次导入 ${detail.import_count} 条。` +
          `请减少导入条数或先删除部分现有规则。`
        );
      } else {
        setErrorMessage(detail.message || '上传失败，请重试');
      }
    }
  };

  const handleConfirm = async () => {
    if (!previewData) return;
    try {
      const result = await confirmMutation.mutateAsync({
        ruleSetId,
        previewSessionToken: previewData.preview_session_token,
      });
      message.success(`成功导入 ${result.imported_count} 条规则`);
      handleClose();
    } catch (err: any) {
      const detail: ImportValidationError = err?.response?.data?.detail ?? {};
      if (detail.code === 'import_preview_expired') {
        message.error('预览已过期，请重新上传 Excel 文件');
        setStep('upload');
        setPreviewData(null);
      } else if (detail.code === 'import_transaction_failed') {
        message.error('导入失败，数据未写入，请稍后重试');
      } else {
        message.error(detail.message || '导入失败，请重试');
      }
    }
  };

  const previewColumns: ColumnsType<ImportPreviewRule> = [
    { title: 'Excel 行号', dataIndex: 'row_number', key: 'row_number', width: 90 },
    {
      title: '规则类型', dataIndex: 'rule_type', key: 'rule_type', width: 100,
      render: (v: RuleType) => <Tag>{RULE_TYPE_LABELS[v]}</Tag>,
    },
    { title: '规则标题', dataIndex: 'title', key: 'title', ellipsis: true },
    {
      title: '严重程度', dataIndex: 'severity', key: 'severity', width: 90,
      render: (v: RuleSeverity) => {
        const cfg = SEVERITY_CONFIG[v];
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    { title: '排序', dataIndex: 'order', key: 'order', width: 60 },
  ];

  const uploadFooter = (
    <Space>
      <Button onClick={handleClose}>取消</Button>
      <Button
        type="primary"
        loading={previewMutation.isPending}
        disabled={!selectedFile}
        onClick={handleUploadPreview}
      >
        上传并预览
      </Button>
    </Space>
  );

  const previewFooter = (
    <Space>
      <Button onClick={() => { setStep('upload'); setPreviewData(null); }}>
        返回重新上传
      </Button>
      <Button
        type="primary"
        loading={confirmMutation.isPending}
        onClick={handleConfirm}
      >
        确认导入
      </Button>
    </Space>
  );

  return (
    <Modal
      title={step === 'upload' ? '批量导入规则' : `预览确认（共 ${previewData?.total_count ?? 0} 条）`}
      open={open}
      onCancel={handleClose}
      footer={step === 'upload' ? uploadFooter : previewFooter}
      width={step === 'preview' ? 800 : 520}
      destroyOnClose
    >
      {step === 'upload' && (
        <>
          <Dragger
            accept=".xlsx"
            maxCount={1}
            beforeUpload={(file) => { setSelectedFile(file); return false; }}
            onRemove={() => setSelectedFile(null)}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">点击或拖拽 .xlsx 文件到此区域</p>
            <p className="ant-upload-hint">仅支持 .xlsx 格式，文件大小不超过 5 MB</p>
          </Dragger>
          {errorMessage && (
            <Alert style={{ marginTop: 12 }} type="error" message={errorMessage} showIcon />
          )}
          {rowErrors.length > 0 && (
            <Alert
              style={{ marginTop: 12 }}
              type="error"
              message={`共 ${rowErrors.length} 行数据校验失败`}
              description={
                <ul style={{ margin: 0, paddingLeft: 16 }}>
                  {rowErrors.map((e, i) => (
                    <li key={i}><Text type="danger">{e.message}</Text></li>
                  ))}
                </ul>
              }
              showIcon
            />
          )}
        </>
      )}
      {step === 'preview' && previewData && (
        <Table<ImportPreviewRule>
          rowKey="row_number"
          columns={previewColumns}
          dataSource={previewData.rules}
          pagination={{ pageSize: 20, showSizeChanger: false }}
          size="small"
          scroll={{ y: 400 }}
        />
      )}
    </Modal>
  );
};

export default RuleImportModal;
