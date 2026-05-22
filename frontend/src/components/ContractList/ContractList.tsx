import { Button, Space, Spin, Empty } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useEffect, useState } from 'react';
import SearchBox from './SearchBox';
import FilterBar, { type FilterType } from './FilterBar';
import ContractCard from './ContractCard';
import ContractForm from '../ContractForm';
import QuickApprovalDialog from '../QuickApprovalDialog/QuickApprovalDialog';
import { useContractList, usePendingCount } from '../../hooks/useContracts';
import { useContractListStore } from '../../stores/useContractListStore';
import { useSelectedContractStore } from '../../stores/useSelectedContractStore';
import './ContractList.css';

interface ContractListProps {
  onContractSelect?: (contractId: string) => void;
}

const ContractList: React.FC<ContractListProps> = ({ onContractSelect }) => {
  // State for contract form dialog
  const [isFormVisible, setIsFormVisible] = useState(false);

  // 快速审批弹窗状态
  const [approvalTarget, setApprovalTarget] = useState<{ id: string; name: string } | null>(null);

  // Get state from stores
  const { filter, searchKeyword, setFilter, setSearchKeyword, setContracts, setPendingCount } =
    useContractListStore();
  const { selectedContractId, setSelectedContractId } = useSelectedContractStore();

  // Fetch contract list data
  const {
    data: contractData,
    isLoading: isLoadingContracts,
    isError: isErrorContracts,
    error: contractError,
  } = useContractList(filter, searchKeyword);

  // Fetch pending count
  const { data: pendingCount = 0 } = usePendingCount();

  // Update store when data changes
  useEffect(() => {
    if (contractData) {
      setContracts(contractData.contracts);
      setPendingCount(contractData.pendingCount);
    }
  }, [contractData, setContracts, setPendingCount]);

  // Handle filter change
  const handleFilterChange = (newFilter: FilterType) => {
    setFilter(newFilter);
  };

  // Handle search
  const handleSearch = (keyword: string) => {
    setSearchKeyword(keyword);
  };

  // Handle contract selection
  const handleContractSelect = (contractId: string) => {
    setSelectedContractId(contractId);
    if (onContractSelect) {
      onContractSelect(contractId);
    }
  };

  // Handle approve action - 打开快速审批弹窗
  const handleApprove = (contractId: string) => {
    const target = (contractData?.contracts || []).find((c) => c.id === contractId);
    if (!target) {
      return;
    }
    setApprovalTarget({ id: target.id, name: target.name });
  };

  // Handle open contract form
  const handleOpenForm = () => {
    setIsFormVisible(true);
  };

  // Handle close contract form
  const handleCloseForm = () => {
    setIsFormVisible(false);
  };

  // Render loading state
  if (isLoadingContracts) {
    return (
      <div className="contract-list">
        <div className="contract-list-filters">
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <SearchBox onSearch={handleSearch} />
            <FilterBar
              activeFilter={filter}
              onFilterChange={handleFilterChange}
              pendingCount={pendingCount}
            />
          </Space>
        </div>

        <div className="contract-list-items">
          <div className="contract-list-loading">
            <Spin tip="加载中..." />
          </div>
        </div>

        <div className="contract-list-footer">
          <Button type="primary" icon={<PlusOutlined />} block onClick={handleOpenForm}>
            发起合同预审
          </Button>
        </div>

        {/* Contract Form Dialog */}
        <ContractForm visible={isFormVisible} onClose={handleCloseForm} />
      </div>
    );
  }

  // Render error state
  if (isErrorContracts) {
    return (
      <div className="contract-list">
        <div className="contract-list-filters">
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <SearchBox onSearch={handleSearch} />
            <FilterBar
              activeFilter={filter}
              onFilterChange={handleFilterChange}
              pendingCount={pendingCount}
            />
          </Space>
        </div>

        <div className="contract-list-items">
          <div className="contract-list-error">
            <Empty
              description={
                contractError instanceof Error ? contractError.message : '加载合同列表失败'
              }
            />
          </div>
        </div>

        <div className="contract-list-footer">
          <Button type="primary" icon={<PlusOutlined />} block onClick={handleOpenForm}>
            发起合同预审
          </Button>
        </div>

        {/* Contract Form Dialog */}
        <ContractForm visible={isFormVisible} onClose={handleCloseForm} />
      </div>
    );
  }

  const contracts = contractData?.contracts || [];

  return (
    <div className="contract-list">
      <div className="contract-list-filters">
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <SearchBox onSearch={handleSearch} />
          <FilterBar
            activeFilter={filter}
            onFilterChange={handleFilterChange}
            pendingCount={pendingCount}
          />
        </Space>
      </div>

      <div className="contract-list-items">
        {contracts.length === 0 ? (
          <div className="contract-list-empty">
            <Empty description="暂无合同" />
          </div>
        ) : (
          contracts.map((contract) => (
            <ContractCard
              key={contract.id}
              contract={contract}
              selected={selectedContractId === contract.id}
              onSelect={handleContractSelect}
              onApprove={contract.hasPendingReview ? handleApprove : undefined}
            />
          ))
        )}
      </div>

      <div className="contract-list-footer">
        <Button type="primary" icon={<PlusOutlined />} block onClick={handleOpenForm}>
          发起合同预审
        </Button>
      </div>

      {/* Contract Form Dialog */}
      <ContractForm visible={isFormVisible} onClose={handleCloseForm} />

      {/* 快速审批弹窗 */}
      <QuickApprovalDialog
        visible={!!approvalTarget}
        contractId={approvalTarget?.id ?? null}
        contractName={approvalTarget?.name}
        onClose={() => setApprovalTarget(null)}
      />
    </div>
  );
};

export default ContractList;
