import React from 'react';
import { Button, Typography } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import ComplianceCheckForm from '../../components/Compliance/ComplianceCheckForm';

const { Title } = Typography;

const ComplianceCheckNewPage: React.FC = () => {
  const navigate = useNavigate();

  const handleSuccess = (checkId: string) => {
    navigate(`/compliance/check/${checkId}`);
  };

  return (
    <div style={{ padding: '24px', maxWidth: 800, margin: '0 auto' }}>
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
          新建合规检查
        </Title>
      </div>

      <ComplianceCheckForm onSuccess={handleSuccess} />
    </div>
  );
};

export default ComplianceCheckNewPage;
