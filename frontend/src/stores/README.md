# Zustand State Management

This directory contains all Zustand stores for the contract pre-review system.

## Stores

### 1. useUserStore

Manages user authentication and current user information.

**State:**

- `currentUser`: Current logged-in user object or null
- `token`: JWT authentication token or null

**Actions:**

- `setCurrentUser(user)`: Set the current user
- `setToken(token)`: Set the authentication token
- `logout()`: Clear user and token (logout)

**Persistence:** This store is persisted to localStorage with key `user-storage`.

**Usage Example:**

```typescript
import { useUserStore } from '@/stores';

function UserProfile() {
  const { currentUser, token, setCurrentUser, logout } = useUserStore();

  if (!currentUser) {
    return <div>Please login</div>;
  }

  return (
    <div>
      <h1>Welcome, {currentUser.name}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### 2. useContractListStore

Manages the contract list, filters, search keyword, and pending count.

**State:**

- `contracts`: Array of contract objects
- `filter`: Current filter type ('all' | '进行中' | '已完成' | '待我处理' | '抄送我')
- `searchKeyword`: Current search keyword
- `pendingCount`: Number of pending tasks for current user

**Actions:**

- `setContracts(contracts)`: Set the entire contract list
- `setFilter(filter)`: Set the current filter
- `setSearchKeyword(keyword)`: Set the search keyword
- `setPendingCount(count)`: Set the pending count
- `updateContract(contractId, updates)`: Update a specific contract
- `addContract(contract)`: Add a new contract to the list
- `reset()`: Reset to initial state

**Usage Example:**

```typescript
import { useContractListStore } from '@/stores';

function ContractList() {
  const {
    contracts,
    filter,
    searchKeyword,
    pendingCount,
    setFilter,
    setSearchKeyword
  } = useContractListStore();

  return (
    <div>
      <input
        value={searchKeyword}
        onChange={(e) => setSearchKeyword(e.target.value)}
        placeholder="Search contracts..."
      />
      <button onClick={() => setFilter('待我处理')}>
        Pending ({pendingCount})
      </button>
      {contracts.map(contract => (
        <div key={contract.id}>{contract.name}</div>
      ))}
    </div>
  );
}
```

### 3. useSelectedContractStore

Manages the currently selected contract ID.

**State:**

- `selectedContractId`: ID of the currently selected contract or null

**Actions:**

- `setSelectedContractId(contractId)`: Set the selected contract ID
- `clearSelection()`: Clear the selection

**Usage Example:**

```typescript
import { useSelectedContractStore } from '@/stores';

function ContractCard({ contract }) {
  const { selectedContractId, setSelectedContractId } = useSelectedContractStore();
  const isSelected = selectedContractId === contract.id;

  return (
    <div
      className={isSelected ? 'selected' : ''}
      onClick={() => setSelectedContractId(contract.id)}
    >
      {contract.name}
    </div>
  );
}
```

## Integration with React Query

The stores work seamlessly with React Query for server state management:

```typescript
import { useQuery } from '@tanstack/react-query';
import { useContractListStore } from '@/stores';
import { fetchContracts } from '@/services/api';

function ContractListContainer() {
  const { filter, searchKeyword, setContracts, setPendingCount } = useContractListStore();

  const { data, isLoading } = useQuery({
    queryKey: ['contracts', filter, searchKeyword],
    queryFn: () => fetchContracts({ filter, search: searchKeyword }),
    onSuccess: (data) => {
      setContracts(data.contracts);
      setPendingCount(data.pendingCount);
    }
  });

  if (isLoading) return <div>Loading...</div>;

  return <ContractList />;
}
```

## WebSocket Integration

Update stores when receiving WebSocket events:

```typescript
import { useEffect } from 'react';
import { socket } from '@/services/socket';
import { useContractListStore } from '@/stores';

function useContractSync() {
  const { updateContract, setPendingCount } = useContractListStore();

  useEffect(() => {
    socket.on('contract:updated', (data) => {
      updateContract(data.contractId, data.updates);
    });

    socket.on('pending:changed', (data) => {
      setPendingCount(data.count);
    });

    return () => {
      socket.off('contract:updated');
      socket.off('pending:changed');
    };
  }, [updateContract, setPendingCount]);
}
```

## Best Practices

1. **Separation of Concerns**: Use Zustand for client state (UI state, selections) and React Query for server state (API data, caching).

2. **Selective Subscriptions**: Only subscribe to the state you need to avoid unnecessary re-renders:

   ```typescript
   // Good - only subscribes to filter
   const filter = useContractListStore((state) => state.filter);

   // Avoid - subscribes to entire store
   const store = useContractListStore();
   ```

3. **Persistence**: Only the user store is persisted. Contract list and selection are ephemeral and should be refreshed on page load.

4. **Type Safety**: All stores are fully typed with TypeScript for better developer experience and error prevention.

5. **Actions over Direct Mutations**: Always use provided actions to update state rather than mutating directly.
