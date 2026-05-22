import { create } from 'zustand';
import type { Contract, FilterType } from '../types';

interface ContractListState {
  contracts: Contract[];
  filter: FilterType;
  searchKeyword: string;
  pendingCount: number;
  setContracts: (contracts: Contract[]) => void;
  setFilter: (filter: FilterType) => void;
  setSearchKeyword: (keyword: string) => void;
  setPendingCount: (count: number) => void;
  updateContract: (contractId: string, updates: Partial<Contract>) => void;
  addContract: (contract: Contract) => void;
  reset: () => void;
}

const initialState = {
  contracts: [],
  filter: 'all' as FilterType,
  searchKeyword: '',
  pendingCount: 0,
};

/**
 * Contract list state store
 * Manages the list of contracts, filter settings, search keyword, and pending count
 */
export const useContractListStore = create<ContractListState>((set) => ({
  ...initialState,

  setContracts: (contracts) => set({ contracts }),

  setFilter: (filter) => set({ filter }),

  setSearchKeyword: (searchKeyword) => set({ searchKeyword }),

  setPendingCount: (pendingCount) => set({ pendingCount }),

  updateContract: (contractId, updates) =>
    set((state) => ({
      contracts: state.contracts.map((contract) =>
        contract.id === contractId ? { ...contract, ...updates } : contract
      ),
    })),

  addContract: (contract) =>
    set((state) => ({
      contracts: [contract, ...state.contracts],
    })),

  reset: () => set(initialState),
}));
