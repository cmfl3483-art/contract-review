import React, { useEffect } from 'react';
import { Drawer, Form, Input, Select, InputNumber, Button, message, Space } from 'antd';
import { useCreateRule, useUpdateRule } from '../../hooks/useCompliance';
import type { Rule, CreateRuleDto, UpdateRuleDto, RuleType, RuleSeverity } from '../../types/compliance';

const { TextArea } = Input;

const RULE_TYPE_OPTIONS: { label: string; value: RuleType }[] = [
  { label: '合同编号', value: 'number' },
  { label: '合同名称', value: 'name' },
  { label: '合同描述', value: 'description' },
  { label: '合同文件', value: 'file' },
];

const SEVERITY_OPTIONS: { label: string; value: RuleSeverity }[] = [
  { label: '必须（must）', value: 'must' },
  { label: '建议（should）', value: 'should' },
];

interface RuleCreateEditDrawerProps {
  open: boolean;
  ruleSetId: string;
  /** 传入时为编辑模式，不传为创建模式 */
  rule?: Rule | null;
  onClose: () => void;
  onSuccess?: () => void;
}

type FormValues = {
  rule_type: RuleType;
  title: string;
  requirement: string;
  severity: RuleSeverity;
  order: number;
};

const RuleCreateEditDrawer: React.FC<RuleCreateEditDrawerProps> = ({
  open,
  ruleSetId,
  rule,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm<FormValues>();
  const createRule = useCreateRule();
  const updateRule = useUpdateRule();

  const isEdit = !!rule;

  useEffect(() => {
    if (open) {
      if (rule) {
        form.setFieldsValue({
          rule_type: rule.rule_type,
          title: rule.title,
          requirement: rule.requirement,
          severity: rule.severity,
          order: rule.order,
        });
      } else {
        form.resetFields();
        form.setFieldsValue({ severity: 'must', order: 0 });
      }
    }
  }, [open, rule, form]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      if (isEdit && rule) {
        const dto: UpdateRuleDto = {
          rule_id: rule.id,
          ...values,
        };
        await updateRule.mutateAsync(dto);
        message.success('规则已更新');
      } else {
        const dto: CreateRuleDto = {
          rule_set_id: ruleSetId,
          ...values,
        };
        await createRule.mutateAsync(dto);
        message.success('规则已创建');
      }

      onSuccess?.();
      onClose();
    } catch (error) {
      if (error && typeof error === 'object' && 'errorFields' in error) return;
      const msg = error instanceof Error ? error.message : '操作失败，请稍后重试';
      message.error(msg);
    }
  };

  const isPending = createRule.isPending || updateRule.isPending;

  return (
    <Drawer
      title={isEdit ? '编辑规则' : '新建规则'}
      open={open}
      onClose={onClose}
      width={520}
      destroyOnClose
      footer={
        <div style={{ textAlign: 'right' }}>
          <Space>
            <Button onClick={onClose} disabled={isPending}>
              取消
            </Button>
            <Button type="primary" onClick={handleSave} loading={isPending}>
              {isEdit ? '保存' : '创建'}
            </Button>
          </Space>
        </div>
      }
    >
      <Form form={form} layout="vertical" autoComplete="off">
        {/* 规则类型 */}
        <Form.Item
          label="规则类型"
          name="rule_type"
          rules={[{ required: true, message: '请选择规则类型' }]}
        >
          <Select options={RULE_TYPE_OPTIONS} placeholder="请选择规则类型" />
        </Form.Item>

        {/* 规则标题 */}
        <Form.Item
          label="规则标题"
          name="title"
          rules={[
            { required: true, message: '请输入规则标题' },
            { min: 1, max: 100, message: '标题长度为 1-100 个字符' },
          ]}
        >
          <Input placeholder="请输入规则标题" maxLength={100} showCount />
        </Form.Item>

        {/* 要求描述 */}
        <Form.Item
          label="要求描述"
          name="requirement"
          rules={[
            { required: true, message: '请输入要求描述' },
            { min: 1, max: 2000, message: '要求描述长度为 1-2000 个字符' },
          ]}
        >
          <TextArea
            placeholder="请详细描述该规则的合规要求"
            maxLength={2000}
            showCount
            rows={5}
          />
        </Form.Item>

        {/* 严重程度 */}
        <Form.Item
          label="严重程度"
          name="severity"
          rules={[{ required: true, message: '请选择严重程度' }]}
        >
          <Select options={SEVERITY_OPTIONS} placeholder="请选择严重程度" />
        </Form.Item>

        {/* 排序序号 */}
        <Form.Item
          label="排序序号"
          name="order"
          rules={[{ required: true, message: '请输入排序序号' }]}
        >
          <InputNumber
            min={0}
            max={9999}
            placeholder="0"
            style={{ width: '100%' }}
          />
        </Form.Item>
      </Form>
    </Drawer>
  );
};

export default RuleCreateEditDrawer;
