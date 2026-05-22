import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Button, Result } from 'antd';
import './ErrorBoundary.css';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

/**
 * ErrorBoundary 组件
 *
 * 用于捕获子组件树中的 JavaScript 错误,记录错误并显示降级 UI
 *
 * 增强功能:
 * - 错误计数和频率检测
 * - 自动恢复尝试
 * - 详细的错误日志
 * - 用户友好的错误提示
 *
 * @example
 * ```tsx
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 *
 * @example 自定义错误处理
 * ```tsx
 * <ErrorBoundary
 *   onError={(error, errorInfo) => {
 *     // 上报到监控系统
 *     reportError(error, errorInfo);
 *   }}
 *   onReset={() => {
 *     // 重置应用状态
 *     resetAppState();
 *   }}
 * >
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 *
 * @example 自定义降级 UI
 * ```tsx
 * <ErrorBoundary fallback={<div>自定义错误提示</div>}>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private errorTimestamps: number[] = [];
  private readonly MAX_ERROR_FREQUENCY = 3; // 最大错误频率
  private readonly ERROR_WINDOW = 10000; // 10秒内的错误窗口

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  /**
   * 当子组件抛出错误时调用
   * 用于更新 state 以显示降级 UI
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * 检查错误频率是否过高
   */
  private checkErrorFrequency(): boolean {
    const now = Date.now();
    
    // 清理旧的错误时间戳
    this.errorTimestamps = this.errorTimestamps.filter(
      timestamp => now - timestamp < this.ERROR_WINDOW
    );
    
    // 添加当前错误时间戳
    this.errorTimestamps.push(now);
    
    // 检查是否超过频率限制
    return this.errorTimestamps.length >= this.MAX_ERROR_FREQUENCY;
  }

  /**
   * 捕获错误后调用
   * 用于记录错误信息和上报
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 检查错误频率
    const isHighFrequency = this.checkErrorFrequency();
    
    // 记录错误到控制台
    console.group('[ErrorBoundary] Component Error');
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Error Count:', this.state.errorCount + 1);
    console.error('High Frequency:', isHighFrequency);
    console.error('Component Stack:', errorInfo.componentStack);
    console.groupEnd();

    // 更新 state 保存错误信息
    this.setState(prevState => ({
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // 调用自定义错误处理函数
    if (this.props.onError) {
      try {
        this.props.onError(error, errorInfo);
      } catch (callbackError) {
        console.error('[ErrorBoundary] Error in onError callback:', callbackError);
      }
    }

    // TODO: 未来可以在这里上报错误到监控系统
    // 例如: Sentry, LogRocket, 或自定义监控服务
    // reportErrorToMonitoring(error, errorInfo, {
    //   errorCount: this.state.errorCount + 1,
    //   isHighFrequency,
    // });
  }

  /**
   * 重置错误状态,尝试重新渲染
   */
  handleReset = (): void => {
    // 调用自定义重置回调
    if (this.props.onReset) {
      try {
        this.props.onReset();
      } catch (callbackError) {
        console.error('[ErrorBoundary] Error in onReset callback:', callbackError);
      }
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  /**
   * 刷新页面
   */
  handleRefresh = (): void => {
    window.location.reload();
  };

  /**
   * 获取错误提示信息
   */
  private getErrorMessage(): { title: string; subTitle: string } {
    const { errorCount } = this.state;
    
    if (errorCount >= this.MAX_ERROR_FREQUENCY) {
      return {
        title: '页面遇到了严重问题',
        subTitle: '页面反复出现错误,建议刷新页面或清除浏览器缓存后重试。如果问题持续存在,请联系技术支持。',
      };
    }
    
    if (errorCount > 1) {
      return {
        title: '组件加载失败',
        subTitle: '页面遇到了一些问题。建议刷新页面重试,如果问题持续存在,请联系技术支持。',
      };
    }
    
    return {
      title: '组件加载失败',
      subTitle: '抱歉,页面遇到了一些问题。您可以尝试刷新页面或返回首页。',
    };
  }

  render(): ReactNode {
    const { hasError, error, errorCount } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      // 如果提供了自定义降级 UI,使用它
      if (fallback) {
        return fallback;
      }

      const { title, subTitle } = this.getErrorMessage();
      const showRetry = errorCount < this.MAX_ERROR_FREQUENCY;

      // 默认降级 UI
      return (
        <div className="error-boundary">
          <Result
            status="error"
            title={title}
            subTitle={subTitle}
            extra={[
              <Button type="primary" key="refresh" onClick={this.handleRefresh}>
                刷新页面
              </Button>,
              showRetry && (
                <Button key="reset" onClick={this.handleReset}>
                  重试
                </Button>
              ),
            ].filter(Boolean)}
          >
            {/* 开发环境显示详细错误信息 */}
            {import.meta.env.DEV && error && (
              <div className="error-details">
                <details>
                  <summary>错误详情 (仅开发环境显示)</summary>
                  <pre className="error-stack">
                    <strong>错误次数:</strong> {errorCount}
                    {'\n\n'}
                    <strong>错误信息:</strong> {error.toString()}
                    {'\n\n'}
                    <strong>错误堆栈:</strong>
                    {'\n'}
                    {error.stack}
                  </pre>
                </details>
              </div>
            )}
          </Result>
        </div>
      );
    }

    return children;
  }
}

export default ErrorBoundary;
