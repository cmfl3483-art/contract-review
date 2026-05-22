/**
 * Frontend Infrastructure Manual Verification Script
 * Task 21: Checkpoint - 验证前端基础设施
 *
 * This script provides manual verification steps for:
 * 1. Axios interceptors and error handling
 * 2. Zustand state management
 * 3. React Query caching
 * 4. Socket.IO connection and events
 *
 * Run this in the browser console to verify infrastructure components.
 */

// ============================================================================
// 1. AXIOS INTERCEPTORS AND ERROR HANDLING
// ============================================================================

console.log('='.repeat(80));
console.log('1. AXIOS INTERCEPTORS AND ERROR HANDLING');
console.log('='.repeat(80));

// Check if axios is available
if (typeof window !== 'undefined') {
  console.log('✓ Running in browser environment');

  // Test 1.1: Check Authorization header
  console.log('\n[Test 1.1] Checking Authorization header configuration...');
  console.log('→ Open DevTools Network tab and make an API request');
  console.log('→ Verify "Authorization: Bearer <token>" header is present');

  // Test 1.2: Check error interceptor
  console.log('\n[Test 1.2] Checking error interceptor...');
  console.log('→ Trigger a 401 error (e.g., with expired token)');
  console.log('→ Verify redirect to login or error message appears');

  // Test 1.3: Check network error handling
  console.log('\n[Test 1.3] Checking network error handling...');
  console.log('→ Disconnect network and make an API request');
  console.log('→ Verify user-friendly error message appears');
}

// ============================================================================
// 2. ZUSTAND STATE MANAGEMENT
// ============================================================================

console.log('\n' + '='.repeat(80));
console.log('2. ZUSTAND STATE MANAGEMENT');
console.log('='.repeat(80));

// Test 2.1: Check user store persistence
console.log('\n[Test 2.1] Checking user store persistence...');
const userStorage = localStorage.getItem('user-storage');
if (userStorage) {
  console.log('✓ User storage found in localStorage');
  try {
    const parsed = JSON.parse(userStorage);
    console.log('✓ User storage structure:', {
      hasState: !!parsed.state,
      hasCurrentUser: !!parsed.state?.currentUser,
      hasToken: !!parsed.state?.token,
    });
  } catch (e) {
    console.error('✗ Failed to parse user storage:', e);
  }
} else {
  console.log('⚠ User storage not found (user may not be logged in)');
}

// Test 2.2: Check contract list store
console.log('\n[Test 2.2] Checking contract list store...');
console.log('→ Contract list store is in-memory (not persisted)');
console.log('→ Verify state updates when filtering/searching contracts');

// Test 2.3: Check selected contract store
console.log('\n[Test 2.3] Checking selected contract store...');
console.log('→ Selected contract store is in-memory (not persisted)');
console.log('→ Verify state updates when selecting a contract');

// ============================================================================
// 3. REACT QUERY CACHING
// ============================================================================

console.log('\n' + '='.repeat(80));
console.log('3. REACT QUERY CACHING');
console.log('='.repeat(80));

// Test 3.1: Check React Query configuration
console.log('\n[Test 3.1] Checking React Query configuration...');
console.log('→ React Query is configured with:');
console.log('  - staleTime: 5 minutes');
console.log('  - gcTime: 10 minutes');
console.log('  - refetchOnWindowFocus: true');
console.log('  - refetchOnReconnect: true');
console.log('  - retry: 1');

// Test 3.2: Check query keys
console.log('\n[Test 3.2] Checking query keys structure...');
console.log('→ Query keys are organized by resource:');
console.log('  - contracts.list(filter, search)');
console.log('  - contracts.detail(id)');
console.log('  - reviews.list(contractId)');
console.log('  - pending.count()');
console.log('  - user.current()');
console.log('  - ai.summary(contractId)');

// Test 3.3: Verify caching behavior
console.log('\n[Test 3.3] Verifying caching behavior...');
console.log('→ Open React Query DevTools (if available)');
console.log('→ Make an API request and verify it\'s cached');
console.log('→ Make the same request again within 5 minutes');
console.log('→ Verify no new network request is made (cached)');

// ============================================================================
// 4. SOCKET.IO CONNECTION AND EVENTS
// ============================================================================

console.log('\n' + '='.repeat(80));
console.log('4. SOCKET.IO CONNECTION AND EVENTS');
console.log('='.repeat(80));

// Test 4.1: Check Socket.IO connection
console.log('\n[Test 4.1] Checking Socket.IO connection...');
console.log('→ Look for "[Socket.IO] 连接成功" in console');
console.log('→ Verify connection is established');

// Test 4.2: Check event listeners
console.log('\n[Test 4.2] Checking Socket.IO event listeners...');
console.log('→ Supported events:');
console.log('  - contract:updated');
console.log('  - review:added');
console.log('  - comment:added');
console.log('  - reply:added');
console.log('  - like:updated');
console.log('  - pending:changed');

// Test 4.3: Check error handling
console.log('\n[Test 4.3] Checking Socket.IO error handling...');
console.log('→ Disconnect network and verify error notification');
console.log('→ Reconnect and verify success notification');

// Test 4.4: Check reconnection
console.log('\n[Test 4.4] Checking Socket.IO reconnection...');
console.log('→ Configured with:');
console.log('  - reconnectionAttempts: 5');
console.log('  - reconnectionDelay: 1000ms');
console.log('  - reconnectionDelayMax: 5000ms');

// ============================================================================
// SUMMARY
// ============================================================================

console.log('\n' + '='.repeat(80));
console.log('VERIFICATION SUMMARY');
console.log('='.repeat(80));

console.log('\n✓ Infrastructure Components:');
console.log('  1. Axios - HTTP client with interceptors');
console.log('  2. Zustand - State management with persistence');
console.log('  3. React Query - Server state caching');
console.log('  4. Socket.IO - Real-time communication');

console.log('\n✓ Configuration Files:');
console.log('  - /src/config/api.ts - API endpoints and base URL');
console.log('  - /src/config/queryClient.ts - React Query configuration');
console.log('  - /src/config/socket.ts - Socket.IO client');
console.log('  - /src/stores/useUserStore.ts - User state');
console.log('  - /src/stores/useContractListStore.ts - Contract list state');
console.log('  - /src/stores/useSelectedContractStore.ts - Selected contract state');

console.log('\n✓ Next Steps:');
console.log('  1. Start the development server: npm run dev');
console.log('  2. Open browser DevTools console');
console.log('  3. Follow the manual verification steps above');
console.log('  4. Verify all infrastructure components are working');

console.log('\n' + '='.repeat(80));
console.log('END OF VERIFICATION SCRIPT');
console.log('='.repeat(80));
