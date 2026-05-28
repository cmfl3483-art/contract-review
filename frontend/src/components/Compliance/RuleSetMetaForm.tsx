import React, { useEffect } from 'react';
import { Form, Input, Switch, Button, message, Space } from 'antd';
import { useUpdateRuleSet } from '../../hooks/useCompliance';
import type { RuleSet, UpdateRuleSetDto } from '../../types/compliance';

const { TextArea } = Input;

interface RuleSetMetaFormProps {
  ruleSet: RuleSet;
  onSuccess?: () => void;
}

const RuleSetMetaForm: React.FC<RuleSetMetaFormProps> = ({ ruleSet, onSuccess }) => {
  const [form] = Form.useForm<UpdateRuleSetDto>();
  const updateRuleSet = useUpdateRuleSet();

  useEffect(() => {
    form.setFieldsValue({
      name: ruleSet.name,
      description: ruleSet.description ?? '',
      is_active: ruleSet.is_active,
    });
  }, [ruleSet, form]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await updateRuleSet.mutateAsync({ id: ruleSet.id, ...values });
      message.success('规则集合信息已更新');
      onSuccess?.();
    } catch (error) {
      if (error && typeof error === 'object' && 'errorFields' in error) return;
      const msg = error instanceof Error ? error.message : '更新失败，请稍后重试';
      message.error(msg);
    }
  };

  return (
    <Form form={form} layout="vertical" autoComplete="off">
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
      >
        <Switch />
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          onClick={handleSave}
          loading={updateRuleSet.isPending}
        >
          保存
        </Button>
      </Form.Item>
    </Form>
  );
};

export default RuleSetMetaForm;
