import React from 'react';
import { Button, Divider, Space, Typography } from 'antd';
import { PlusOutlined, SettingOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useUserStore } from '../../stores/useUserStore';
import ComplianceCheckList from '../../components/Compliance/ComplianceCheckList';

const { Title } = Typography;

/** 角色 ∈ {法务, 运营} 时拥有管理员权限 */
function isAdminRole(role: string | undefined): boolean {
  return role === '法务' || role === '运营';
}

const ComplianceListPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentUser } = useUserStore();
  const isAdmin = isAdminRole(currentUser?.role);

  return (
    <div style={{ padding: '24px', maxWidth: 1200, margin: '0 auto' }}>
      {/* 页面标题与操作按钮 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 24,
        }}
      >
        <Title level={3} style={{ margin: 0 }}>
          合规审查
        </Title>
        <Space>
          {isAdmin && (
            <Button
              icon={<SettingOutlined />}
              onClick={() => navigate('/compliance/admin/rule-sets')}
            >
              规则管理
            </Button>
          )}
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/compliance/check/new')}
          >
            新建合规检查
          </Button>
        </Space>
      </div>

      {/* 我的合规检查列表 */}
      <div>
        <Title level={5} style={{ marginBottom: 16 }}>
          我的合规检查
        </Title>
        <ComplianceCheckList
          scope="mine"
          onSelect={(checkId) => navigate(`/compliance/check/${checkId}`)}
        />
      </div>

      {/* 法务/运营额外展示全部合规检查 */}
      {isAdmin && (
        <>
          <Divider />
          <div>
            <Title level={5} style={{ marginBottom: 16 }}>
              全部合规检查
            </Title>
            <ComplianceCheckList
              scope="all"
              onSelect={(checkId) => navigate(`/compliance/check/${checkId}`)}
            />
          </div>
        </>
      )}
    </div>
  );
};

export default ComplianceListPage;
