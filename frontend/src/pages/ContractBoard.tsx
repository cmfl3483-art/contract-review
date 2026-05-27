import { useSelectedContractStore } from '../stores';
import ThreeColumnLayout from '../layouts/ThreeColumnLayout';
import ContractList from '../components/ContractList/ContractList';
import ContractDetail from '../components/ContractDetail/ContractDetail';
import Timeline from '../components/Timeline/Timeline';
import AIAdvisor from '../components/AIAdvisor/AIAdvisor';
import { useSocketIntegration } from '../hooks/useSocket';
import './ContractBoard.css';

const ContractBoard: React.FC = () => {
  const { selectedContractId } = useSelectedContractStore();

  // 初始化 Socket.IO 连接和事件监听（含 notification:new）
  useSocketIntegration(selectedContractId ?? undefined);

  return (
    <div className="contract-board-root">
      <ThreeColumnLayout
        leftPanel={<ContractList />}
        centerPanel={
          <div className="center-panel-container">
            <ContractDetail />
            {selectedContractId && <Timeline contractId={selectedContractId} />}
          </div>
        }
        rightPanel={<AIAdvisor />}
      />
    </div>
  );
};

export default ContractBoard;
