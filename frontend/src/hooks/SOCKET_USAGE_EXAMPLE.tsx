/**
 * Socket.IO 使用示例
 * Socket.IO Usage Examples
 *
 * 这个文件展示了如何在不同场景下使用 Socket.IO 客户端
 */

import { useEffect } from 'react';
import { useSocket, useContractRoom, useSocketEvents, useSocketIntegration } from './useSocket';
import { useSelectedContractStore } from '../stores/useSelectedContractStore';
import { onContractUpdated, onReviewAdded, onCommentAdded, isConnected } from '../config/socket';

/**
 * 示例 1: 在 App 根组件中使用 (推荐)
 * 使用 useSocketIntegration 一次性完成所有配置
 */
export function AppWithSocket() {
  const selectedContractId = useSelectedContractStore((state) => state.selectedContractId);

  // 一行代码完成所有 Socket.IO 配置
  const { isConnected: connected } = useSocketIntegration(selectedContractId);

  return (
    <div>
      {/* 显示连接状态 */}
      <div style={{ position: 'fixed', top: 10, right: 10 }}>
        {connected ? (
          <span style={{ color: 'green' }}>🟢 实时连接已建立</span>
        ) : (
          <span style={{ color: 'red' }}>🔴 连接已断开</span>
        )}
      </div>

      {/* 其他组件 */}
      <div>{/* 应用内容 */}</div>
    </div>
  );
}

/**
 * 示例 2: 只管理连接 (不需要房间和事件监听)
 */
export function SimpleSocketConnection() {
  const { isConnected: connected } = useSocket();

  return (
    <div>
      <p>连接状态: {connected ? '已连接' : '未连接'}</p>
    </div>
  );
}

/**
 * 示例 3: 在合同详情组件中使用
 * 自动加入和离开合同房间
 */
export function ContractDetailWithSocket({ contractId }: { contractId: string }) {
  // 自动加入合同房间
  useContractRoom(contractId);

  return (
    <div>
      <h2>合同详情</h2>
      <p>合同 ID: {contractId}</p>
      {/* 合同详情内容 */}
    </div>
  );
}

/**
 * 示例 4: 只监听事件 (不需要房间管理)
 */
export function EventListenerComponent() {
  // 监听所有事件并自动刷新 React Query 缓存
  useSocketEvents();

  return <div>{/* 组件内容 */}</div>;
}

/**
 * 示例 5: 手动监听特定事件
 * 适用于需要自定义处理逻辑的场景
 */
export function CustomEventHandler() {
  useEffect(() => {
    // 监听合同更新事件
    const unsubscribeContractUpdated = onContractUpdated((data) => {
      console.log('合同更新:', data);
      // 自定义处理逻辑
      // 例如: 显示通知、更新本地状态等
    });

    // 监听评审添加事件
    const unsubscribeReviewAdded = onReviewAdded((data) => {
      console.log('新增评审:', data);
      // 自定义处理逻辑
    });

    // 监听评论添加事件
    const unsubscribeCommentAdded = onCommentAdded((data) => {
      console.log('新增评论:', data);
      // 自定义处理逻辑
    });

    // 清理函数: 取消所有事件监听
    return () => {
      unsubscribeContractUpdated();
      unsubscribeReviewAdded();
      unsubscribeCommentAdded();
    };
  }, []);

  return <div>{/* 组件内容 */}</div>;
}

/**
 * 示例 6: 检查连接状态
 */
export function ConnectionStatus() {
  const connected = isConnected();

  return (
    <div>
      {connected ? (
        <div style={{ color: 'green' }}>
          <span>✓</span> 实时通信已启用
        </div>
      ) : (
        <div style={{ color: 'orange' }}>
          <span>⚠</span> 实时通信未连接
        </div>
      )}
    </div>
  );
}

/**
 * 示例 7: 在时间线组件中使用
 * 实时更新评论和回复
 */
export function TimelineWithRealtime({ contractId }: { contractId: string }) {
  // 加入合同房间
  useContractRoom(contractId);

  useEffect(() => {
    // 监听评论添加事件
    const unsubscribe = onCommentAdded((data) => {
      console.log('收到新评论:', data);
      // React Query 会自动刷新数据
      // 这里可以添加额外的 UI 反馈,如显示通知
    });

    return unsubscribe;
  }, []);

  return (
    <div>
      <h3>评审时间线</h3>
      {/* 时间线内容 */}
    </div>
  );
}

/**
 * 示例 8: 在合同列表组件中使用
 * 实时更新待办数量
 */
export function ContractListWithRealtime() {
  useEffect(() => {
    // 监听待办数量变化
    // 注意: 这个事件是发送给特定用户的,不需要加入房间
    // useSocketEvents 已经处理了这个事件,这里只是演示
  }, []);

  return (
    <div>
      <h3>合同列表</h3>
      {/* 列表内容 */}
    </div>
  );
}

/**
 * 示例 9: 完整的应用结构
 */
export function CompleteAppStructure() {
  const selectedContractId = useSelectedContractStore((state) => state.selectedContractId);

  // 在根组件使用 useSocketIntegration
  const { isConnected: connected } = useSocketIntegration(selectedContractId);

  return (
    <div>
      {/* 顶部导航栏 */}
      <header>
        <h1>合同预审看板系统</h1>
        <ConnectionStatus />
      </header>

      {/* 主要内容区域 */}
      <main>
        {/* 左侧: 合同列表 */}
        <aside>
          <ContractListWithRealtime />
        </aside>

        {/* 中间: 合同详情和时间线 */}
        <section>
          {selectedContractId && (
            <>
              <ContractDetailWithSocket contractId={selectedContractId} />
              <TimelineWithRealtime contractId={selectedContractId} />
            </>
          )}
        </section>

        {/* 右侧: AI 顾问 */}
        <aside>{/* AI 顾问组件 */}</aside>
      </main>

      {/* 底部状态栏 */}
      <footer>
        <p>连接状态: {connected ? '已连接' : '未连接'}</p>
      </footer>
    </div>
  );
}

/**
 * 最佳实践总结
 *
 * 1. 在 App 根组件使用 useSocketIntegration
 *    - 自动管理连接、房间和事件监听
 *    - 一行代码完成所有配置
 *
 * 2. 在需要实时更新的组件使用 useContractRoom
 *    - 自动加入和离开合同房间
 *    - 组件卸载时自动清理
 *
 * 3. 使用 React Query 的自动刷新机制
 *    - useSocketEvents 会自动失效相关缓存
 *    - 不需要手动更新状态
 *
 * 4. 只在需要自定义处理时手动监听事件
 *    - 大多数情况下 useSocketEvents 已经足够
 *    - 手动监听适用于显示通知、播放声音等场景
 *
 * 5. 使用 isConnected() 检查连接状态
 *    - 可以在 UI 中显示连接状态
 *    - 可以在连接断开时显示提示
 */
