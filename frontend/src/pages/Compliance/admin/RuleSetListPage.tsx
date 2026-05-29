import React, { useState } from 'react';
import { Button, Modal, Typography } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import RuleSetTable from '../../../components/Compliance/RuleSetTable';
import RuleSetCreateModal from '../../../components/Compliance/RuleSetCreateModal';
import RuleSetMetaForm from '../../../components/Compliance/RuleSetMetaForm';
import type { RuleSet } from '../../../types/compliance';

const { Title } = Typography;

const RuleSetListPage: React.FC = () => {
  const navigate = useNavigate();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editingRuleSet, setEditingRuleSet] = useState<RuleSet | null>(null);

  const handleCreateSuccess = (ruleSetId: string) => {
    navigate(`/compliance/admin/rule-sets/${ruleSetId}`);
  };

  return (
    <div style={{ padding: '24px', maxWidth: 1100, margin: '0 auto' }}>
      {/* 返回按钮 + 页面标题 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/compliance')}
        >
          返回
        </Button>
        <Title level={3} style={{ margin: 0 }}>
          规则管理
        </Title>
      </div>

      {/* 规则集合表格（内含「新建规则集合」按钮） */}
      <RuleSetTable
        onCreateClick={() => setCreateModalOpen(true)}
        onViewDetail={(ruleSetId) => navigate(`/compliance/admin/rule-sets/${ruleSetId}`)}
        onEdit={(ruleSet) => setEditingRuleSet(ruleSet)}
      />

      {/* 新建规则集合弹窗 */}
      <RuleSetCreateModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onSuccess={handleCreateSuccess}
      />

      {/* 编辑规则集合弹窗 */}
      <Modal
        title="编辑规则集合"
        open={editingRuleSet !== null}
        onCancel={() => setEditingRuleSet(null)}
        footer={null}
        destroyOnClose
        width={560}
      >
        {editingRuleSet && (
          <RuleSetMetaForm
            ruleSet={editingRuleSet}
            onSuccess={() => setEditingRuleSet(null)}
          />
        )}
      </Modal>
    </div>
  );
};

export default RuleSetListPage;
