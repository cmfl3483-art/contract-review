import { useState, useRef } from 'react';

export interface UseMentionReturn {
  inputValue: string;
  mentionQuery: string;
  isMentionOpen: boolean;
  mentionedUserIds: string[];
  mentionedUserNames: string[];
  showMaxMentionWarning: boolean;
  handleInputChange: (value: string) => void;
  handleUserSelect: (user: { id: string; name: string }) => void;
  handleMentionClose: () => void;
  setInputValue: (value: string) => void;
  reset: () => void;
}

const MAX_MENTION_COUNT = 10;

export function useMention(): UseMentionReturn {
  const [inputValue, setInputValue] = useState('');
  const [mentionQuery, setMentionQuery] = useState('');
  const [isMentionOpen, setIsMentionOpen] = useState(false);
  const [mentionedUserIds, setMentionedUserIds] = useState<string[]>([]);
  const [mentionedUserNames, setMentionedUserNames] = useState<string[]>([]);
  const [showMaxMentionWarning, setShowMaxMentionWarning] = useState(false);

  // 记录当前 @ 触发的起始位置
  const mentionStartRef = useRef<number>(-1);

  const handleInputChange = (value: string) => {
    setInputValue(value);
    setShowMaxMentionWarning(false);

    // 找到最后一个 @ 的位置
    const lastAtIndex = value.lastIndexOf('@');

    if (lastAtIndex === -1) {
      // 没有 @，关闭 Picker
      setIsMentionOpen(false);
      setMentionQuery('');
      mentionStartRef.current = -1;
      return;
    }

    // @ 后面的文本（到字符串末尾）
    const textAfterAt = value.slice(lastAtIndex + 1);

    // 如果 @ 后面有空格，说明这个 @ 已经完成了（选过人或者用户手动加了空格）
    if (textAfterAt.includes(' ')) {
      setIsMentionOpen(false);
      setMentionQuery('');
      mentionStartRef.current = -1;
      return;
    }

    // 正在输入 @ 搜索词
    if (mentionedUserIds.length >= MAX_MENTION_COUNT) {
      setShowMaxMentionWarning(true);
      setIsMentionOpen(false);
      return;
    }

    mentionStartRef.current = lastAtIndex;
    setMentionQuery(textAfterAt);
    setIsMentionOpen(true);
  };

  const handleUserSelect = (user: { id: string; name: string }) => {
    const atIndex = mentionStartRef.current;
    if (atIndex !== -1) {
      // 替换从 @ 开始到末尾的内容为 @{姓名} + 空格
      const before = inputValue.slice(0, atIndex);
      const newValue = `${before}@${user.name} `;
      setInputValue(newValue);
    }

    // 去重添加
    setMentionedUserIds((prev) =>
      prev.includes(user.id) ? prev : [...prev, user.id]
    );
    setMentionedUserNames((prev) =>
      prev.includes(user.name) ? prev : [...prev, user.name]
    );

    setIsMentionOpen(false);
    setMentionQuery('');
    mentionStartRef.current = -1;
  };

  const handleMentionClose = () => {
    setIsMentionOpen(false);
    setMentionQuery('');
    mentionStartRef.current = -1;
  };

  const reset = () => {
    setInputValue('');
    setMentionQuery('');
    setIsMentionOpen(false);
    setMentionedUserIds([]);
    setMentionedUserNames([]);
    setShowMaxMentionWarning(false);
    mentionStartRef.current = -1;
  };

  return {
    inputValue,
    mentionQuery,
    isMentionOpen,
    mentionedUserIds,
    mentionedUserNames,
    showMaxMentionWarning,
    handleInputChange,
    handleUserSelect,
    handleMentionClose,
    setInputValue,
    reset,
  };
}
