import React, { useState } from 'react';
import { Button, Typography } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import RuleSetTable from '../../../components/Compliance/RuleSetTable';
import RuleSetCreateModal from '../../../components/Compliance/RuleSetCreateModal';

const { Title } = Typography;

const RuleSetListPage: React.FC = () => {
  const navigate = useNavigate();
  const [createModalOpen, setCreateModalOpen] = useState(false);

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
      />

      {/* 新建规则集合弹窗 */}
      <RuleSetCreateModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onSuccess={handleCreateSuccess}
      />
    </div>
  );
};

export default RuleSetListPage;
