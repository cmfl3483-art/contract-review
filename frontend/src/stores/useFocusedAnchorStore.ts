import { create } from 'zustand';

/**
 * 焦点锚点 Store
 * 用于通知点击跳转时，告诉所有相关组件（如 ReplyList）
 * 哪条记录正在被聚焦，需要自动展开折叠区域以便滚动定位。
 */
interface FocusedAnchorState {
  anchorId: string | null;
  setAnchorId: (id: string | null) => void;
}

export const useFocusedAnchorStore = create<FocusedAnchorState>((set) => ({
  anchorId: null,
  setAnchorId: (id) => set({ anchorId: id }),
}));
