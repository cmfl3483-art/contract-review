import React, { useEffect, useRef, useState } from 'react';
import { Button, Descriptions, Divider, Result, Spin, Tag, Typography } from 'antd';
import { ArrowLeftOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { useComplianceCheckPolling, useRecheckCompliance } from '../../hooks/useCompliance';
import TruncatedNotice from '../../components/Compliance/TruncatedNotice';
import ComplianceSuggestions from '../../components/Compliance/ComplianceSuggestions';
import ViolationList from '../../components/Compliance/ViolationList';
import { getComplianceErrorText } from '../../components/Compliance/ErrorMessageMap';

const { Title, Text } = Typography;

/** 轮询上限：90 秒 */
const POLLING_TIMEOUT_MS = 90 * 1000;

const ComplianceCheckDetailPage: React.FC = () => {
  const { checkId } = useParams<{ checkId: string }>();
  const navigate = useNavigate();

  // 控制轮询是否启用
  const [pollingEnabled, setPollingEnabled] = useState(true);
  // 记录轮询开始时间
  const pollingStartRef = useRef<number>(Date.now());

  const { data: check, isLoading } = useComplianceCheckPolling(
    checkId ?? '',
    pollingEnabled && !!checkId
  );

  const recheck = useRecheckCompliance();

  // 90s 轮询上限：累计超过 90s 后停止轮询
  useEffect(() => {
    if (!pollingEnabled) return;
    if (check?.status !== 'pending') return;

    const elapsed = Date.now() - pollingStartRef.current;
    if (elapsed >= POLLING_TIMEOUT_MS) {
      setPollingEnabled(false);
      return;
    }

    // 设置剩余时间的定时器
    const remaining = POLLING_TIMEOUT_MS - elapsed;
    const timer = setTimeout(() => {
      setPollingEnabled(false);
    }, remaining);

    return () => clearTimeout(timer);
  }, [check?.status, pollingEnabled]);

  // 当状态不再是 pending 时停止轮询
  useEffect(() => {
    if (check?.status && check.status !== 'pending') {
      setPollingEnabled(false);
    }
  }, [check?.status]);

  const handleRecheck = () => {
    if (!checkId) return;
    // 重置轮询状态
    pollingStartRef.current = Date.now();
    setPollingEnabled(true);
    recheck.mutate(checkId);
  };

  if (!checkId) {
    return (
      <Result
        status="404"
        title="检查 ID 无效"
        extra={
          <Button onClick={() => navigate('/compliance')}>返回列表</Button>
        }
      />
    );
  }

  if (isLoading && !check) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!check) {
    return (
      <Result
        status="404"
        title="未找到该合规检查记录"
        extra={
          <Button onClick={() => navigate('/compliance')}>返回列表</Button>
        }
      />
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: 900, margin: '0 auto' }}>
      {/* 返回按钮 */}
      <div style={{ marginBottom: 16 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/compliance')}
        >
          返回列表
        </Button>
      </div>

      {/* 元数据区域 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={4} style={{ marginBottom: 16 }}>
          合规检查详情
        </Title>
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="文件名">{check.file_name}</Descriptions.Item>
          <Descriptions.Item label="规则集合">
            {check.rule_set_name ?? <Text type="secondary">—</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="提交时间">
            {dayjs(check.requested_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="完成时间">
            {check.completed_at
              ? dayjs(check.completed_at).format('YYYY-MM-DD HH:mm:ss')
              : <Text type="secondary">—</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="提交人">
            {check.requested_by.name}
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            {check.status === 'pending' && <Tag color="processing">检查中</Tag>}
            {check.status === 'completed' && <Tag color="success">已完成</Tag>}
            {check.status === 'failed' && <Tag color="error">失败</Tag>}
          </Descriptions.Item>
          {check.name_draft && (
            <Descriptions.Item label="合同名称初稿" span={2}>
              {check.name_draft}
            </Descriptions.Item>
          )}
        </Descriptions>
      </div>

      {/* 文件截断提示 */}
      <TruncatedNotice show={check.text_truncated} />

      {/* pending 状态：AI 检查中 */}
      {check.status === 'pending' && (
        <div style={{ textAlign: 'center', padding: '48px 0' }}>
          <Spin size="large" tip="AI 检查中，请稍候…" />
          {!pollingEnabled && (
            <div style={{ marginTop: 24 }}>
              <Text type="secondary">检查时间较长，请稍后刷新页面查看结果</Text>
            </div>
          )}
        </div>
      )}

      {/* completed 状态：展示结果 */}
      {check.status === 'completed' && (
        <>
          <ComplianceSuggestions result={check} />
          <Divider />
          <Title level={5} style={{ marginBottom: 16 }}>
            违规项列表
          </Title>
          <ViolationList violations={check.violations} />
        </>
      )}

      {/* failed 状态：展示错误文案 + 重新检查按钮 */}
      {check.status === 'failed' && (
        <Result
          status="error"
          title="合规检查失败"
          subTitle={getComplianceErrorText(check.error_message)}
          extra={
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              loading={recheck.isPending}
              onClick={handleRecheck}
            >
              重新检查
            </Button>
          }
        />
      )}
    </div>
  );
};

export default ComplianceCheckDetailPage;
