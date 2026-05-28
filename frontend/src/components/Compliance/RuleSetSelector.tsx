import React from 'react';
import { Select, Tag } from 'antd';
import { useRuleSets } from '../../hooks/useCompliance';

interface RuleSetSelectorProps {
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
}

const RuleSetSelector: React.FC<RuleSetSelectorProps> = ({ value, onChange, disabled }) => {
  const { data: ruleSets, isLoading } = useRuleSets();

  return (
    <Select
      value={value}
      onChange={onChange}
      loading={isLoading}
      disabled={disabled}
      placeholder="请选择规则集合（默认使用当前生效规则集）"
      allowClear
      style={{ width: '100%' }}
      optionLabelProp="label"
    >
      {(ruleSets ?? []).map((rs) => (
        <Select.Option key={rs.id} value={rs.id} label={rs.name}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>{rs.name}</span>
            {rs.is_active && (
              <Tag color="green" style={{ margin: 0 }}>
                当前生效
              </Tag>
            )}
            <span style={{ color: '#999', fontSize: 12 }}>（{rs.rule_count} 条规则）</span>
          </span>
        </Select.Option>
      ))}
    </Select>
  );
};

export default RuleSetSelector;
