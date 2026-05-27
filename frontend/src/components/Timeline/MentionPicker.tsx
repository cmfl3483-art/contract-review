import React, { useEffect, useRef, useState } from 'react';
import { useMentionableUsers } from '../../hooks/useMentionableUsers';
import type { MentionableUser } from '../../types';

interface MentionPickerProps {
  query: string;                          // 搜索关键词
  contractId: string;                     // 合同 ID（用于限定候选人范围：发起人/评审人/抄送人）
  onSelect: (user: { id: string; name: string }) => void;
  onClose: () => void;
}

const MentionPicker: React.FC<MentionPickerProps> = ({
  query,
  contractId,
  onSelect,
  onClose,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // 200ms debounce
  const [debouncedQuery, setDebouncedQuery] = useState(query);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 200);
    return () => clearTimeout(timer);
  }, [query]);

  // 点击外部区域关闭
  useEffect(() => {
    const handleMouseDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleMouseDown);
    return () => document.removeEventListener('mousedown', handleMouseDown);
  }, [onClose]);

  // 改用合同维度的候选人接口（限定为发起人 + 评审人 + 抄送人并集）
  // TanStack Query 默认行为保证仅渲染最新一次请求的响应，丢弃过期请求结果
  const { data, isLoading, error } = useMentionableUsers(contractId, debouncedQuery);

  const users: MentionableUser[] = (data ?? []).slice(0, 10);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'absolute',
        bottom: '100%',
        left: 0,
        marginBottom: 4,
        zIndex: 1000,
        background: '#fff',
        borderRadius: 8,
        boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
        maxHeight: 200,
        overflowY: 'auto',
        minWidth: 220,
        padding: '4px 0',
      }}
    >
      {error ? (
        <div style={{ padding: '8px 16px', color: '#ff4d4f', fontSize: 13 }}>
          加载候选人失败，请重试
        </div>
      ) : isLoading ? (
        <div style={{ padding: '8px 16px', color: '#999', fontSize: 13 }}>加载中...</div>
      ) : users.length === 0 ? (
        <div style={{ padding: '8px 16px', color: '#999', fontSize: 13 }}>无匹配用户</div>
      ) : (
        users.map((user) => (
          <MentionItem key={user.id} user={user} onSelect={onSelect} />
        ))
      )}
    </div>
  );
};

interface MentionItemProps {
  user: MentionableUser;
  onSelect: (user: { id: string; name: string }) => void;
}

const MentionItem: React.FC<MentionItemProps> = ({ user, onSelect }) => {
  const [hovered, setHovered] = useState(false);

  // 取姓名首字作为头像
  const avatarChar = user.name ? user.name.charAt(0) : '?';

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onMouseDown={(e) => {
        // 使用 mousedown 而非 click，避免触发外部 mousedown 关闭逻辑
        e.preventDefault();
        e.stopPropagation();
        onSelect({ id: user.id, name: user.name });
      }}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '6px 14px',
        cursor: 'pointer',
        backgroundColor: hovered ? '#f0f7ff' : 'transparent',
        transition: 'background-color 0.15s',
      }}
    >
      {/* 头像 */}
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: '50%',
          backgroundColor: '#1677ff',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 12,
          fontWeight: 600,
          flexShrink: 0,
        }}
      >
        {avatarChar}
      </div>

      {/* 姓名 + 部门 */}
      <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <span
          style={{
            fontSize: 13,
            color: '#1a1a1a',
            fontWeight: 500,
            lineHeight: '18px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {user.name}
        </span>
        {user.department && (
          <span
            style={{
              fontSize: 11,
              color: '#999',
              lineHeight: '16px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {user.department}
          </span>
        )}
      </div>
    </div>
  );
};

export default MentionPicker;
