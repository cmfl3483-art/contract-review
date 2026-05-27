import React from 'react';
import { useFocusedAnchorStore } from '../../stores/useFocusedAnchorStore';
import { useSelectedContractStore } from '../../stores/useSelectedContractStore';

interface MessageContentProps {
  text: string;
  contractId?: string;
  reviewMap?: Map<string, { authorName: string }>;
  commentMap?: Map<string, { authorName: string }>;
}

const REF_REGEX = /\[ref:(review|comment)-([a-f0-9-]+)\]/g;

const MessageContent: React.FC<MessageContentProps> = ({
  text,
  contractId,
  reviewMap,
  commentMap,
}) => {
  const setAnchorId = useFocusedAnchorStore((s) => s.setAnchorId);
  const setSelectedContractId = useSelectedContractStore((s) => s.setSelectedContractId);

  const handleRefClick = (id: string) => {
    if (contractId) setSelectedContractId(contractId);
    setAnchorId(id);
    setTimeout(() => {
      const el = document.getElementById(`anchor-${id}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('highlight-flash');
        setTimeout(() => el.classList.remove('highlight-flash'), 3000);
      }
    }, 200);
  };

  // 解析 text，把 [ref:xxx-yyy] 替换为 React 节点
  const parts: Array<string | React.ReactNode> = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  REF_REGEX.lastIndex = 0;
  while ((match = REF_REGEX.exec(text)) !== null) {
    const [full, type, id] = match;
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const map = type === 'review' ? reviewMap : commentMap;
    const target = map?.get(id);
    if (!target) {
      // 引用无法解析时静默忽略，不显示错误文案
      lastIndex = match.index + full.length;
      continue;
    } else {
      const label =
        type === 'review'
          ? `@${target.authorName}的评审`
          : `@${target.authorName}的评论`;
      parts.push(
        <a
          key={`${type}-${id}-${match.index}`}
          className="ai-ref-link"
          onClick={(e) => {
            e.preventDefault();
            handleRefClick(id);
          }}
        >
          {label}
        </a>
      );
    }
    lastIndex = match.index + full.length;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return <>{parts}</>;
};

export default MessageContent;
