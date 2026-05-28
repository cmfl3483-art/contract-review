import React, { useState } from 'react';
import { Table, Tag, Select, Space, Tooltip } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useComplianceChecks } from '../../hooks/useCompliance';
import type { ComplianceCheckSummary, ComplianceCheckStatus } from '../../types/compliance';

interface ComplianceCheckListProps {
  scope?: 'mine' | 'all';
  onSelect?: (checkId: string) => void;
}

const STATUS_LABELS: Record<ComplianceCheckStatus, { label: string; color: string; icon: React.ReactNode }> = {
  pending: { label: '检查中', color: 'processing', icon: <ClockCircleOutlined /> },
  completed: { label: '已完成', color: 'success', icon: <CheckCircleOutlined /> },
  failed: { label: '失败', color: 'error', icon: <CloseCircleOutlined /> },
};

function ScoreTag({ score }: { score: number | null }) {
  if (score === null) return <span style={{ color: '#999' }}>—</span>;
  if (score >= 90) return <Tag color="green">{score}</Tag>;
  if (score >= 70) return <Tag color="blue">{score}</Tag>;
  if (score >= 50) return <Tag color="gold">{score}</Tag>;
  return <Tag color="red">{score}</Tag>;
}

const ComplianceCheckList: React.FC<ComplianceCheckListProps> = ({ scope = 'mine', onSelect }) => {
  const [statusFilter, setStatusFilter] = useState<ComplianceCheckStatus | undefined>(undefined);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading } = useComplianceChecks({
    page,
    page_size: pageSize,
    status: statusFilter,
    // scope 通过后端角色鉴权控制，前端传 scope 参数供后端区分
    ...(scope === 'all' ? { scope: 'all' } : {}),
  } as Parameters<typeof useComplianceChecks>[0]);

  const columns: ColumnsType<ComplianceCheckSummary> = [
    {
      title: '合同名称初稿',
      dataIndex: 'name_draft',
      key: 'name_draft',
      ellipsis: true,
      render: (val: string | null) => val || <span style={{ color: '#999' }}>（未填写）</span>,
    },
    {
      title: '规则集合',
      dataIndex: 'rule_set_name',
      key: 'rule_set_name',
      ellipsis: true,
      render: (val: string | null) => val || <span style={{ color: '#999' }}>—</span>,
    },
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,
    },
    {
      title: '截断',
      dataIndex: 'text_truncated',
      key: 'text_truncated',
      width: 60,
      render: (val: boolean) =>
        val ? (
          <Tooltip title="文件过长已截断，可能影响检查准确性">
            <WarningOutlined style={{ color: '#faad14' }} />
          </Tooltip>
        ) : null,
    },
    {
      title: '违规数',
      dataIndex: 'violation_count',
      key: 'violation_count',
      width: 80,
      render: (val: number | null) =>
        val === null ? <span style={{ color: '#999' }}>—</span> : <Tag color={val > 0 ? 'red' : 'green'}>{val}</Tag>,
    },
    {
      title: '合规评分',
      dataIndex: 'compliance_score',
      key: 'compliance_score',
      width: 90,
      render: (val: number | null) => <ScoreTag score={val} />,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (val: ComplianceCheckStatus) => {
        const s = STATUS_LABELS[val];
        return (
          <Tag icon={s.icon} color={s.color}>
            {s.label}
          </Tag>
        );
      },
    },
    {
      title: '提交时间',
      dataIndex: 'requested_at',
      key: 'requested_at',
      width: 160,
      render: (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm'),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ color: '#666' }}>状态筛选：</span>
        <Select
          value={statusFilter}
          onChange={(v) => { setStatusFilter(v); setPage(1); }}
          allowClear
          placeholder="全部状态"
          style={{ width: 140 }}
          options={[
            { label: '检查中', value: 'pending' },
            { label: '已完成', value: 'completed' },
            { label: '失败', value: 'failed' },
          ]}
        />
        {scope === 'all' && (
          <Tag color="blue" style={{ marginLeft: 'auto' }}>
            全部记录
          </Tag>
        )}
      </div>

      <Table<ComplianceCheckSummary>
        rowKey="id"
        columns={columns}
        dataSource={data?.items ?? []}
        loading={isLoading}
        onRow={(record) => ({
          onClick: () => onSelect?.(record.id),
          style: onSelect ? { cursor: 'pointer' } : undefined,
        })}
        pagination={{
          current: page,
          pageSize,
          total: data?.total ?? 0,
          onChange: (p) => setPage(p),
          showSizeChanger: false,
          showTotal: (total) => `共 ${total} 条`,
        }}
        size="middle"
      />
    </div>
  );
};

export default ComplianceCheckList;
