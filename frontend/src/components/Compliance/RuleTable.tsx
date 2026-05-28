import React, { useMemo } from 'react';
import { Table, Tag, Button, Space, Popconfirm, Tooltip } from 'antd';
import { EditOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useRules, useDeleteRule } from '../../hooks/useCompliance';
import type { Rule, RuleType, RuleSeverity } from '../../types/compliance';

const RULE_TYPE_LABELS: Record<RuleType, string> = {
  number: '合同编号',
  name: '合同名称',
  description: '合同描述',
  file: '合同文件',
};

const SEVERITY_CONFIG: Record<RuleSeverity, { label: string; color: string }> = {
  must: { label: '必须', color: 'red' },
  should: { label: '建议', color: 'gold' },
};

const RULE_TYPE_ORDER: Record<RuleType, number> = {
  number: 0,
  name: 1,
  description: 2,
  file: 3,
};

interface RuleTableProps {
  ruleSetId: string;
  onEdit?: (rule: Rule) => void;
  onCreateClick?: () => void;
}

const RuleTable: React.FC<RuleTableProps> = ({ ruleSetId, onEdit, onCreateClick }) => {
  const { data: rules, isLoading } = useRules(ruleSetId);
  const deleteRule = useDeleteRule();

  // 按 rule_type → order → created_at 排序
  const sorted = useMemo(() => {
    if (!rules) return [];
    return [...rules].sort((a, b) => {
      const typeDiff = (RULE_TYPE_ORDER[a.rule_type] ?? 99) - (RULE_TYPE_ORDER[b.rule_type] ?? 99);
      if (typeDiff !== 0) return typeDiff;
      const orderDiff = a.order - b.order;
      if (orderDiff !== 0) return orderDiff;
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    });
  }, [rules]);

  const columns: ColumnsType<Rule> = [
    {
      title: '序号',
      dataIndex: 'order',
      key: 'order',
      width: 60,
    },
    {
      title: '规则类型',
      dataIndex: 'rule_type',
      key: 'rule_type',
      width: 100,
      render: (val: RuleType) => <Tag>{RULE_TYPE_LABELS[val]}</Tag>,
    },
    {
      title: '规则标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '要求描述',
      dataIndex: 'requirement',
      key: 'requirement',
      ellipsis: true,
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 90,
      render: (val: RuleSeverity) => {
        const cfg = SEVERITY_CONFIG[val];
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => onEdit?.(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除该规则？"
            description="删除后不可恢复"
            onConfirm={() => deleteRule.mutate({ rule_id: record.id, rule_set_id: ruleSetId })}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="删除">
              <Button type="text" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={onCreateClick}>
          新建规则
        </Button>
      </div>
      <Table<Rule>
        rowKey="id"
        columns={columns}
        dataSource={sorted}
        loading={isLoading}
        pagination={false}
        size="middle"
      />
    </div>
  );
};

export default RuleTable;
