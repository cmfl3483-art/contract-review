import { create } from 'zustand';

interface SelectedContractState {
  selectedContractId: string | null;
  setSelectedContractId: (contractId: string | null) => void;
  clearSelection: () => void;
}

/**
 * Selected contract state store
 * Manages the currently selected contract ID
 */
export const useSelectedContractStore = create<SelectedContractState>((set) => ({
  selectedContractId: null,

  setSelectedContractId: (selectedContractId) => set({ selectedContractId }),

  clearSelection: () => set({ selectedContractId: null }),
}));
