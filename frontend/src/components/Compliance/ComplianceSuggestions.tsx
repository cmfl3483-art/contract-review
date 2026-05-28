import React from 'react';
import { Card, Button, Tag, message, Space, Typography } from 'antd';
import { CopyOutlined } from '@ant-design/icons';
import type { ComplianceCheckResult, ComplianceCheckStatus } from '../../types/compliance';

const { Text, Paragraph } = Typography;

interface ScoreBadgeProps {
  score: number;
}

function ScoreBadge({ score }: ScoreBadgeProps) {
  if (score >= 90) {
    return (
      <Tag color="green" style={{ fontSize: 14, padding: '2px 10px' }}>
        优秀
      </Tag>
    );
  }
  if (score >= 70) {
    return (
      <Tag color="blue" style={{ fontSize: 14, padding: '2px 10px' }}>
        良好
      </Tag>
    );
  }
  if (score >= 50) {
    return (
      <Tag color="gold" style={{ fontSize: 14, padding: '2px 10px' }}>
        待改进
      </Tag>
    );
  }
  return (
    <Tag color="red" style={{ fontSize: 14, padding: '2px 10px' }}>
      不合规
    </Tag>
  );
}

interface ComplianceSuggestionsProps {
  result: Pick<
    ComplianceCheckResult,
    'status' | 'compliance_score' | 'suggested_name' | 'suggested_description'
  >;
}

const ComplianceSuggestions: React.FC<ComplianceSuggestionsProps> = ({ result }) => {
  const { status, compliance_score, suggested_name, suggested_description } = result;

  const handleCopy = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      message.success(`${label}已复制到剪贴板`);
    } catch {
      message.error('复制失败，请手动复制');
    }
  };

  return (
    <div>
      {/* 合规评分 */}
      {status === 'completed' && compliance_score !== null && (
        <Card
          size="small"
          style={{ marginBottom: 16, background: '#fafafa' }}
          bodyStyle={{ padding: '12px 16px' }}
        >
          <Space align="center" size={12}>
            <Text strong style={{ fontSize: 15 }}>
              合规评分：{compliance_score}/100
            </Text>
            <ScoreBadge score={compliance_score} />
          </Space>
        </Card>
      )}

      {/* 建议合同名称 */}
      {suggested_name && (
        <Card
          size="small"
          title="建议合同名称"
          style={{ marginBottom: 12 }}
          extra={
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCopy(suggested_name, '建议合同名称')}
            >
              复制
            </Button>
          }
        >
          <Paragraph style={{ margin: 0 }}>{suggested_name}</Paragraph>
        </Card>
      )}

      {/* 建议合同描述 */}
      {suggested_description && (
        <Card
          size="small"
          title="建议合同描述"
          style={{ marginBottom: 12 }}
          extra={
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCopy(suggested_description, '建议合同描述')}
            >
              复制
            </Button>
          }
        >
          <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
            {suggested_description}
          </Paragraph>
        </Card>
      )}
    </div>
  );
};

export default ComplianceSuggestions;
