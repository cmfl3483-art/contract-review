import React from 'react';
import { Card, Tag, Typography, Space } from 'antd';
import type { Violation } from '../../types/compliance';

const { Text, Paragraph } = Typography;

const SEVERITY_CONFIG = {
  must: { label: '必须', color: 'red' },
  should: { label: '建议', color: 'gold' },
} as const;

const LOCATION_LABELS: Record<string, string> = {
  number: '合同编号',
  name: '合同名称',
  description: '合同描述',
  file: '合同文件',
};

interface ViolationItemProps {
  violation: Violation;
}

const ViolationItem: React.FC<ViolationItemProps> = ({ violation }) => {
  const severityConfig = SEVERITY_CONFIG[violation.severity];
  const locationLabel = LOCATION_LABELS[violation.location] ?? violation.location;

  return (
    <Card
      size="small"
      style={{ marginBottom: 12 }}
      bodyStyle={{ padding: '12px 16px' }}
    >
      {/* 标题行：规则名称 + 严重程度 + 位置 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
        <Text strong style={{ fontSize: 14 }}>
          {violation.rule_title}
        </Text>
        <Tag color={severityConfig.color} style={{ margin: 0 }}>
          {severityConfig.label}
        </Tag>
        <Tag color="default" style={{ margin: 0 }}>
          {locationLabel}
        </Tag>
      </div>

      {/* 原文片段 */}
      {violation.excerpt && (
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            原文片段：
          </Text>
          <Paragraph
            style={{
              margin: '4px 0 0',
              padding: '6px 10px',
              background: '#f5f5f5',
              borderRadius: 4,
              fontSize: 13,
              fontStyle: 'italic',
            }}
          >
            {violation.excerpt}
          </Paragraph>
        </div>
      )}

      {/* 违反描述 */}
      {violation.description && (
        <div style={{ marginBottom: 6 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            违反描述：
          </Text>
          <Paragraph style={{ margin: '2px 0 0', fontSize: 13 }}>
            {violation.description}
          </Paragraph>
        </div>
      )}

      {/* 修改建议 */}
      {violation.suggestion && (
        <div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            修改建议：
          </Text>
          <Paragraph style={{ margin: '2px 0 0', fontSize: 13, color: '#1677ff' }}>
            {violation.suggestion}
          </Paragraph>
        </div>
      )}
    </Card>
  );
};

export default ViolationItem;
