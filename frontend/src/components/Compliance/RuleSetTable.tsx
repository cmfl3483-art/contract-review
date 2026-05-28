import React from 'react';
import { Table, Tag, Button, Space, Popconfirm, Tooltip } from 'antd';
import { EditOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useRuleSets, useDeleteRuleSet } from '../../hooks/useCompliance';
import type { RuleSet } from '../../types/compliance';

interface RuleSetTableProps {
  onEdit?: (ruleSet: RuleSet) => void;
  onViewDetail?: (ruleSetId: string) => void;
  onCreateClick?: () => void;
}

const RuleSetTable: React.FC<RuleSetTableProps> = ({ onEdit, onViewDetail, onCreateClick }) => {
  const { data: ruleSets, isLoading } = useRuleSets();
  const deleteRuleSet = useDeleteRuleSet();

  const columns: ColumnsType<RuleSet> = [
    {
      title: '规则集合名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record) => (
        <Space>
          <span
            style={onViewDetail ? { cursor: 'pointer', color: '#1677ff' } : undefined}
            onClick={() => onViewDetail?.(record.id)}
          >
            {name}
          </span>
          {record.is_active && (
            <Tag color="green" style={{ margin: 0 }}>
              当前生效
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (val: string | null) => val || <span style={{ color: '#999' }}>—</span>,
    },
    {
      title: '规则数',
      dataIndex: 'rule_count',
      key: 'rule_count',
      width: 80,
      render: (val: number) => <Tag>{val}</Tag>,
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
      width: 120,
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
            title="确认删除该规则集合？"
            description={record.is_active ? '当前生效的规则集合无法删除' : '删除后不可恢复，关联规则将一并删除'}
            onConfirm={() => deleteRuleSet.mutate(record.id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true, disabled: record.is_active }}
            disabled={record.is_active}
          >
            <Tooltip title={record.is_active ? '当前生效规则集合不可删除' : '删除'}>
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
                disabled={record.is_active}
              />
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
          新建规则集合
        </Button>
      </div>
      <Table<RuleSet>
        rowKey="id"
        columns={columns}
        dataSource={ruleSets ?? []}
        loading={isLoading}
        pagination={false}
        size="middle"
      />
    </div>
  );
};

export default RuleSetTable;
