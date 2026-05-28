import React, { useState } from 'react';
import { Button, Card, Result, Spin, Typography } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useRuleSet } from '../../../hooks/useCompliance';
import RuleSetMetaForm from '../../../components/Compliance/RuleSetMetaForm';
import RuleTable from '../../../components/Compliance/RuleTable';
import RuleCreateEditDrawer from '../../../components/Compliance/RuleCreateEditDrawer';
import type { Rule } from '../../../types/compliance';

const { Title } = Typography;

const RuleSetDetailPage: React.FC = () => {
  const { ruleSetId } = useParams<{ ruleSetId: string }>();
  const navigate = useNavigate();

  const { data: ruleSet, isLoading } = useRuleSet(ruleSetId ?? '');

  // 控制新建/编辑规则抽屉
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<Rule | null>(null);

  const handleCreateRule = () => {
    setEditingRule(null);
    setDrawerOpen(true);
  };

  const handleEditRule = (rule: Rule) => {
    setEditingRule(rule);
    setDrawerOpen(true);
  };

  const handleDrawerClose = () => {
    setDrawerOpen(false);
    setEditingRule(null);
  };

  if (!ruleSetId) {
    return (
      <Result
        status="404"
        title="规则集合 ID 无效"
        extra={
          <Button onClick={() => navigate('/compliance/admin/rule-sets')}>
            返回列表
          </Button>
        }
      />
    );
  }

  if (isLoading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!ruleSet) {
    return (
      <Result
        status="404"
        title="未找到该规则集合"
        extra={
          <Button onClick={() => navigate('/compliance/admin/rule-sets')}>
            返回列表
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: 1100, margin: '0 auto' }}>
      {/* 返回按钮 + 页面标题 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/compliance/admin/rule-sets')}
        >
          返回
        </Button>
        <Title level={3} style={{ margin: 0 }}>
          {ruleSet.name}
        </Title>
      </div>

      {/* 规则集合元数据编辑表单 */}
      <Card title="基本信息" style={{ marginBottom: 24 }}>
        <RuleSetMetaForm ruleSet={ruleSet} />
      </Card>

      {/* 规则列表 */}
      <Card title="规则列表">
        <RuleTable
          ruleSetId={ruleSetId}
          onEdit={handleEditRule}
          onCreateClick={handleCreateRule}
        />
      </Card>

      {/* 新建/编辑规则抽屉 */}
      <RuleCreateEditDrawer
        open={drawerOpen}
        ruleSetId={ruleSetId}
        rule={editingRule}
        onClose={handleDrawerClose}
        onSuccess={handleDrawerClose}
      />
    </div>
  );
};

export default RuleSetDetailPage;
