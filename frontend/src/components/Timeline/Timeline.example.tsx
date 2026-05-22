import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Select, Card } from 'antd';
import Timeline from './Timeline';

// Create a query client for the examples
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 5 * 60 * 1000,
    },
  },
});

/**
 * Example 1: Basic Timeline Usage
 *
 * 展示基础的 Timeline 组件用法
 */
export function BasicTimelineExample() {
  const contractId = 'contract-123';

  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ height: '600px', border: '1px solid #d9d9d9', borderRadius: '4px' }}>
        <Timeline contractId={contractId} />
      </div>
    </QueryClientProvider>
  );
}

/**
 * Example 2: Timeline with Contract Selector
 *
 * 展示带合同选择器的 Timeline 组件
 */
export function TimelineWithSelectorExample() {
  const [selectedContractId, setSelectedContractId] = useState<string>('contract-1');

  const contracts = [
    { id: 'contract-1', name: '采购合同 - 2025-001' },
    { id: 'contract-2', name: '销售合同 - 2025-002' },
    { id: 'contract-3', name: '服务合同 - 2025-003' },
  ];

  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <Card>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>选择合同:</span>
            <Select
              style={{ width: 300 }}
              value={selectedContractId}
              onChange={setSelectedContractId}
              options={contracts.map((c) => ({ label: c.name, value: c.id }))}
            />
          </div>
        </Card>

        <div style={{ height: '600px', border: '1px solid #d9d9d9', borderRadius: '4px' }}>
          <Timeline contractId={selectedContractId} />
        </div>
      </div>
    </QueryClientProvider>
  );
}

/**
 * Example 3: Timeline in Layout
 *
 * 展示在布局中使用 Timeline 组件
 */
export function TimelineInLayoutExample() {
  const [selectedContractId, setSelectedContractId] = useState<string>('contract-1');

  const contracts = [
    { id: 'contract-1', name: '采购合同 - 2025-001', status: '进行中' },
    { id: 'contract-2', name: '销售合同 - 2025-002', status: '已完成' },
    { id: 'contract-3', name: '服务合同 - 2025-003', status: '进行中' },
  ];

  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ display: 'flex', height: '600px', gap: '16px' }}>
        {/* Left Sidebar - Contract List */}
        <div
          style={{
            width: '280px',
            border: '1px solid #d9d9d9',
            borderRadius: '4px',
            padding: '16px',
            overflowY: 'auto',
          }}
        >
          <h3 style={{ marginTop: 0 }}>合同列表</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {contracts.map((contract) => (
              <Card
                key={contract.id}
                size="small"
                hoverable
                onClick={() => setSelectedContractId(contract.id)}
                style={{
                  cursor: 'pointer',
                  borderLeft:
                    selectedContractId === contract.id ? '3px solid #1890ff' : '3px solid transparent',
                  backgroundColor: selectedContractId === contract.id ? '#e6f7ff' : 'white',
                }}
              >
                <div style={{ fontSize: '14px', fontWeight: 500 }}>{contract.name}</div>
                <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px' }}>
                  {contract.status}
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Main Content - Timeline */}
        <div style={{ flex: 1, border: '1px solid #d9d9d9', borderRadius: '4px' }}>
          <Timeline contractId={selectedContractId} />
        </div>
      </div>
    </QueryClientProvider>
  );
}

/**
 * Example 4: Timeline with Custom Height
 *
 * 展示自定义高度的 Timeline 组件
 */
export function TimelineWithCustomHeightExample() {
  const contractId = 'contract-123';
  const [height, setHeight] = useState<number>(400);

  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <Card>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>高度:</span>
            <Select
              style={{ width: 150 }}
              value={height}
              onChange={setHeight}
              options={[
                { label: '300px', value: 300 },
                { label: '400px', value: 400 },
                { label: '500px', value: 500 },
                { label: '600px', value: 600 },
              ]}
            />
          </div>
        </Card>

        <div style={{ height: `${height}px`, border: '1px solid #d9d9d9', borderRadius: '4px' }}>
          <Timeline contractId={contractId} />
        </div>
      </div>
    </QueryClientProvider>
  );
}

/**
 * Example 5: Multiple Timelines
 *
 * 展示多个 Timeline 组件并排显示
 */
export function MultipleTimelinesExample() {
  const contracts = [
    { id: 'contract-1', name: '采购合同 - 2025-001' },
    { id: 'contract-2', name: '销售合同 - 2025-002' },
  ];

  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ display: 'flex', gap: '16px' }}>
        {contracts.map((contract) => (
          <div
            key={contract.id}
            style={{ flex: 1, border: '1px solid #d9d9d9', borderRadius: '4px' }}
          >
            <div
              style={{
                padding: '12px 16px',
                borderBottom: '1px solid #d9d9d9',
                fontWeight: 500,
                backgroundColor: '#fafafa',
              }}
            >
              {contract.name}
            </div>
            <div style={{ height: '500px' }}>
              <Timeline contractId={contract.id} />
            </div>
          </div>
        ))}
      </div>
    </QueryClientProvider>
  );
}

// Export all examples
export default {
  BasicTimelineExample,
  TimelineWithSelectorExample,
  TimelineInLayoutExample,
  TimelineWithCustomHeightExample,
  MultipleTimelinesExample,
};
