import React, { useMemo } from 'react';
import { Empty } from 'antd';
import type { Violation, RuleType, RuleSeverity } from '../../types/compliance';
import ViolationItem from './ViolationItem';

const SEVERITY_ORDER: Record<RuleSeverity, number> = {
  must: 0,
  should: 1,
};

const LOCATION_ORDER: Record<RuleType, number> = {
  number: 0,
  name: 1,
  description: 2,
  file: 3,
};

interface ViolationListProps {
  violations: Violation[];
}

const ViolationList: React.FC<ViolationListProps> = ({ violations }) => {
  const sorted = useMemo(() => {
    return [...violations].sort((a, b) => {
      // 先按 severity 排（must < should）
      const severityDiff =
        (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99);
      if (severityDiff !== 0) return severityDiff;
      // 再按 location 排（number < name < description < file）
      return (LOCATION_ORDER[a.location] ?? 99) - (LOCATION_ORDER[b.location] ?? 99);
    });
  }, [violations]);

  if (sorted.length === 0) {
    return (
      <Empty
        description="未发现不符合项"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        style={{ padding: '24px 0' }}
      />
    );
  }

  return (
    <div>
      {sorted.map((v, idx) => (
        <ViolationItem key={`${v.rule_id}-${idx}`} violation={v} />
      ))}
    </div>
  );
};

export default ViolationList;
