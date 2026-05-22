import { useCallback, useRef, useState } from 'react';
import './ThreeColumnLayout.css';

interface ThreeColumnLayoutProps {
  leftPanel: React.ReactNode;
  centerPanel: React.ReactNode;
  rightPanel: React.ReactNode;
}

const ThreeColumnLayout: React.FC<ThreeColumnLayoutProps> = ({
  leftPanel,
  centerPanel,
  rightPanel,
}) => {
  const [leftWidth, setLeftWidth] = useState(280);
  const [rightWidth, setRightWidth] = useState(340);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragging = useRef<'left' | 'right' | null>(null);
  const startX = useRef(0);
  const startWidth = useRef(0);

  const handleMouseDown = useCallback((side: 'left' | 'right') => (e: React.MouseEvent) => {
    e.preventDefault();
    dragging.current = side;
    startX.current = e.clientX;
    startWidth.current = side === 'left' ? leftWidth : rightWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [leftWidth, rightWidth]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging.current || !containerRef.current) return;

    const containerWidth = containerRef.current.offsetWidth;
    const MIN_LEFT = 200;
    const MIN_RIGHT = 260;
    const MIN_CENTER = 300;

    if (dragging.current === 'left') {
      const delta = e.clientX - startX.current;
      const newLeft = Math.max(MIN_LEFT, Math.min(startWidth.current + delta, containerWidth - MIN_CENTER - rightWidth));
      setLeftWidth(newLeft);
    } else {
      const delta = startX.current - e.clientX;
      const newRight = Math.max(MIN_RIGHT, Math.min(startWidth.current + delta, containerWidth - MIN_CENTER - leftWidth));
      setRightWidth(newRight);
    }
  }, [rightWidth, leftWidth]);

  const handleMouseUp = useCallback(() => {
    if (dragging.current) {
      dragging.current = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
  }, []);

  return (
    <div
      className="three-column-layout"
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div className="left-panel" style={{ width: leftWidth }}>
        {leftPanel}
      </div>
      <div className="resize-handle" onMouseDown={handleMouseDown('left')} />
      <div className="center-panel">
        {centerPanel}
      </div>
      <div className="resize-handle" onMouseDown={handleMouseDown('right')} />
      <div className="right-panel" style={{ width: rightWidth }}>
        {rightPanel}
      </div>
    </div>
  );
};

export default ThreeColumnLayout;
