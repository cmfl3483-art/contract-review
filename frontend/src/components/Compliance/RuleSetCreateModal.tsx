import React, { useEffect } from 'react';
import { Modal, Form, Input, Switch, message } from 'antd';
import { useCreateRuleSet } from '../../hooks/useCompliance';
import type { CreateRuleSetDto } from '../../types/compliance';

const { TextArea } = Input;

interface RuleSetCreateModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (ruleSetId: string) => void;
}

const RuleSetCreateModal: React.FC<RuleSetCreateModalProps> = ({ open, onClose, onSuccess }) => {
  const [form] = Form.useForm<CreateRuleSetDto>();
  const createRuleSet = useCreateRuleSet();

  useEffect(() => {
    if (!open) {
      form.resetFields();
    }
  }, [open, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      const result = await createRuleSet.mutateAsync(values);
      message.success('规则集合创建成功');
      onSuccess?.(result.id);
      onClose();
    } catch (error) {
      if (error && typeof error === 'object' && 'errorFields' in error) return;
      const msg = error instanceof Error ? error.message : '创建失败，请稍后重试';
      message.error(msg);
    }
  };

  return (
    <Modal
      title="新建规则集合"
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={createRuleSet.isPending}
      okText="创建"
      cancelText="取消"
      width={520}
      destroyOnClose
    >
      <Form form={form} layout="vertical" autoComplete="off" style={{ marginTop: 16 }}>
        <Form.Item
          label="规则集合名称"
          name="name"
          rules={[
            { required: true, message: '请输入规则集合名称' },
            { min: 1, max: 100, message: '名称长度为 1-100 个字符' },
          ]}
        >
          <Input placeholder="请输入规则集合名称" maxLength={100} showCount />
        </Form.Item>

        <Form.Item
          label="描述"
          name="description"
          rules={[{ max: 1000, message: '描述不能超过 1000 个字符' }]}
        >
          <TextArea
            placeholder="请输入规则集合描述（可选）"
            maxLength={1000}
            showCount
            rows={3}
          />
        </Form.Item>

        <Form.Item
          label="设为当前生效规则集"
          name="is_active"
          valuePropName="checked"
          initialValue={false}
        >
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default RuleSetCreateModal;
