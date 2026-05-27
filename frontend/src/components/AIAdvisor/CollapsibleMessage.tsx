import React, { useState, useLayoutEffect, useRef } from 'react';

const LINE_HEIGHT_PX = 22;
const MAX_LINES = 10;
const MAX_HEIGHT_PX = LINE_HEIGHT_PX * MAX_LINES; // 220px

interface CollapsibleMessageProps {
  children: React.ReactNode;
  /** 流式输出中：不测量、不显示折叠按钮、不应用遮罩 */
  isStreaming?: boolean;
  /** 文本签名，变化时触发重新测量 */
  contentKey?: string;
}

const CollapsibleMessage: React.FC<CollapsibleMessageProps> = ({
  children,
  isStreaming = false,
  contentKey,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const [needCollapse, setNeedCollapse] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useLayoutEffect(() => {
    if (isStreaming) {
      // 流式输出中不测量
      setNeedCollapse(false);
      setExpanded(false);
      return;
    }
    if (!ref.current) return;
    const el = ref.current;
    // 临时移除 max-height 测量真实高度
    const previousMaxHeight = el.style.maxHeight;
    el.style.maxHeight = 'none';
    const fullHeight = el.scrollHeight;
    el.style.maxHeight = previousMaxHeight;
    setNeedCollapse(fullHeight > MAX_HEIGHT_PX);
  }, [contentKey, isStreaming]);

  const showCollapsed = needCollapse && !expanded && !isStreaming;

  return (
    <div className={`collapsible-message ${showCollapsed ? 'collapsed' : ''}`}>
      <div ref={ref} className="collapsible-content">
        {children}
      </div>
      {needCollapse && !isStreaming && (
        <>
          {!expanded && <div className="fade-mask" />}
          <button
            type="button"
            className="toggle-btn"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? '收起' : '展开全部'}
          </button>
        </>
      )}
    </div>
  );
};

export default CollapsibleMessage;
