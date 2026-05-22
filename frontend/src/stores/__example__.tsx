/**
 * Example usage of Zustand stores
 * This file demonstrates how to use the stores in React components
 *
 * NOTE: This is an example file for reference only, not used in production
 */

import { useUserStore, useContractListStore, useSelectedContractStore } from './index';
import type { Contract } from '../types';

// Example 1: User Authentication
export function UserProfile() {
  const { currentUser, logout } = useUserStore();

  if (!currentUser) {
    return <div>Please login</div>;
  }

  return (
    <div>
      <h1>Welcome, {currentUser.name}</h1>
      <p>Role: {currentUser.role}</p>
      <p>Department: {currentUser.department}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

// Example 2: Contract List with Filters
export function ContractListExample() {
  const { contracts, filter, searchKeyword, pendingCount, setFilter, setSearchKeyword } =
    useContractListStore();

  const { selectedContractId, setSelectedContractId } = useSelectedContractStore();

  return (
    <div>
      {/* Search */}
      <input
        type="text"
        value={searchKeyword}
        onChange={(e) => setSearchKeyword(e.target.value)}
        placeholder="Search contracts..."
      />

      {/* Filters */}
      <div>
        <button onClick={() => setFilter('all')} disabled={filter === 'all'}>
          All
        </button>
        <button onClick={() => setFilter('进行中')} disabled={filter === '进行中'}>
          In Progress
        </button>
        <button onClick={() => setFilter('已完成')} disabled={filter === '已完成'}>
          Completed
        </button>
        <button onClick={() => setFilter('待我处理')} disabled={filter === '待我处理'}>
          Pending ({pendingCount})
        </button>
        <button onClick={() => setFilter('抄送我')} disabled={filter === '抄送我'}>
          CC'd to Me
        </button>
      </div>

      {/* Contract List */}
      <div>
        {contracts.map((contract) => (
          <div
            key={contract.id}
            onClick={() => setSelectedContractId(contract.id)}
            style={{
              padding: '10px',
              border: selectedContractId === contract.id ? '2px solid blue' : '1px solid gray',
              cursor: 'pointer',
            }}
          >
            <h3>{contract.name}</h3>
            <p>Status: {contract.status}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// Example 3: Selective Subscription (Performance Optimization)
export function PendingBadge() {
  // Only subscribe to pendingCount, not the entire store
  const pendingCount = useContractListStore((state) => state.pendingCount);

  if (pendingCount === 0) return null;

  return (
    <span
      style={{
        backgroundColor: 'red',
        color: 'white',
        borderRadius: '50%',
        padding: '2px 6px',
        fontSize: '12px',
      }}
    >
      {pendingCount}
    </span>
  );
}

// Example 4: Using Multiple Stores Together
export function ContractHeader() {
  const currentUser = useUserStore((state) => state.currentUser);
  const selectedContractId = useSelectedContractStore((state) => state.selectedContractId);
  const contracts = useContractListStore((state) => state.contracts);

  const selectedContract = contracts.find((c) => c.id === selectedContractId);

  if (!selectedContract) {
    return <div>No contract selected</div>;
  }

  return (
    <div>
      <h2>{selectedContract.name}</h2>
      <p>Viewing as: {currentUser?.name}</p>
      <p>Status: {selectedContract.status}</p>
    </div>
  );
}

// Example 5: Store Actions
export function ContractActions() {
  const { addContract, updateContract } = useContractListStore();
  const currentUser = useUserStore((state) => state.currentUser);

  const handleCreateContract = () => {
    const newContract: Contract = {
      id: Date.now().toString(),
      name: 'New Contract',
      status: 'progress',
      initiatorId: currentUser?.id || '',
      ccUsers: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    addContract(newContract);
  };

  const handleCompleteContract = (contractId: string) => {
    updateContract(contractId, { status: 'completed' });
  };

  return (
    <div>
      <button onClick={handleCreateContract}>Create New Contract</button>
      <button onClick={() => handleCompleteContract('some-id')}>Complete Contract</button>
    </div>
  );
}

// Example 6: Reset Store
export function ResetButton() {
  const reset = useContractListStore((state) => state.reset);

  return <button onClick={reset}>Reset Contract List</button>;
}
