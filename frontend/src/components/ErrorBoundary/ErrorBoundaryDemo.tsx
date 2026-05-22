/**
 * ErrorBoundary 演示组件
 *
 * 用于开发环境测试 ErrorBoundary 功能
 * 不应在生产环境中使用
 */

import { useState } from 'react';
import { Button, Card, Space, Typography } from 'antd';
import ErrorBoundary from './ErrorBoundary';

const { Title, Paragraph } = Typography;

// 会抛出错误的组件
function BuggyComponent() {
  throw new Error('这是一个测试错误!');
}

// 正常组件
function NormalComponent() {
  return (
    <Card>
      <Title level={4}>正常组件</Title>
      <Paragraph>这个组件运行正常,没有错误。</Paragraph>
    </Card>
  );
}

/**
 * ErrorBoundary 演示页面
 */
export default function ErrorBoundaryDemo() {
  const [showBuggy, setShowBuggy] = useState(false);
  const [showNormal, setShowNormal] = useState(true);

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>ErrorBoundary 演示</Title>
      <Paragraph>点击下面的按钮来测试 ErrorBoundary 的错误捕获功能。</Paragraph>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 控制按钮 */}
        <Card title="控制面板">
          <Space>
            <Button type="primary" danger onClick={() => setShowBuggy(true)} disabled={showBuggy}>
              显示会出错的组件
            </Button>
            <Button onClick={() => setShowBuggy(false)} disabled={!showBuggy}>
              隐藏会出错的组件
            </Button>
            <Button type="default" onClick={() => setShowNormal(!showNormal)}>
              {showNormal ? '隐藏' : '显示'}正常组件
            </Button>
          </Space>
        </Card>

        {/* 正常组件 - 不使用 ErrorBoundary */}
        {showNormal && <NormalComponent />}

        {/* 会出错的组件 - 使用 ErrorBoundary 保护 */}
        {showBuggy && (
          <ErrorBoundary
            onError={(error, errorInfo) => {
              console.log('捕获到错误:', error);
              console.log('错误信息:', errorInfo);
            }}
          >
            <Card title="受保护的组件区域">
              <BuggyComponent />
            </Card>
          </ErrorBoundary>
        )}

        {/* 自定义降级 UI 示例 */}
        <Card title="自定义降级 UI 示例">
          <ErrorBoundary
            fallback={
              <div
                style={{
                  padding: '40px',
                  textAlign: 'center',
                  backgroundColor: '#fff1f0',
                  border: '1px solid #ffccc7',
                  borderRadius: '4px',
                }}
              >
                <Title level={4} style={{ color: '#cf1322' }}>
                  自定义错误提示
                </Title>
                <Paragraph>这是一个自定义的错误降级 UI</Paragraph>
                <Button type="primary" onClick={() => window.location.reload()}>
                  刷新页面
                </Button>
              </div>
            }
          >
            <BuggyComponent />
          </ErrorBoundary>
        </Card>

        {/* 嵌套 ErrorBoundary 示例 */}
        <Card title="嵌套 ErrorBoundary 示例">
          <ErrorBoundary>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Card size="small" title="区域 1 - 正常">
                <Paragraph>这个区域运行正常</Paragraph>
              </Card>

              <ErrorBoundary>
                <Card size="small" title="区域 2 - 会出错">
                  <BuggyComponent />
                </Card>
              </ErrorBoundary>

              <Card size="small" title="区域 3 - 正常">
                <Paragraph>即使区域 2 出错,这个区域仍然可以正常显示</Paragraph>
              </Card>
            </Space>
          </ErrorBoundary>
        </Card>
      </Space>
    </div>
  );
}
