import React from 'react';
import { Select, Tag, Empty } from 'antd';
import { useRuleSets } from '../../hooks/useCompliance';

interface RuleSetSelectorProps {
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
}

const RuleSetSelector: React.FC<RuleSetSelectorProps> = ({ value, onChange, disabled }) => {
  const { data: ruleSets, isLoading } = useRuleSets();

  // 只展示当前生效的规则集合
  const activeRuleSets = (ruleSets ?? []).filter((rs) => rs.is_active);

  return (
    <Select
      value={value}
      onChange={onChange}
      loading={isLoading}
      disabled={disabled}
      placeholder="请选择规则集合"
      allowClear
      style={{ width: '100%' }}
      optionLabelProp="label"
      notFoundContent={
        isLoading ? null : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无生效的规则集合，请联系法务/运营在「规则管理」中启用"
          />
        )
      }
    >
      {activeRuleSets.map((rs) => (
        <Select.Option key={rs.id} value={rs.id} label={rs.name}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>{rs.name}</span>
            <Tag color="green" style={{ margin: 0 }}>
              当前生效
            </Tag>
            <span style={{ color: '#999', fontSize: 12 }}>（{rs.rule_count} 条规则）</span>
          </span>
        </Select.Option>
      ))}
    </Select>
  );
};

export default RuleSetSelector;
