import { useSelectedContractStore } from '../stores';
import ThreeColumnLayout from '../layouts/ThreeColumnLayout';
import ContractList from '../components/ContractList/ContractList';
import ContractDetail from '../components/ContractDetail/ContractDetail';
import Timeline from '../components/Timeline/Timeline';
import AIAdvisor from '../components/AIAdvisor/AIAdvisor';
import './ContractBoard.css';

const ContractBoard: React.FC = () => {
  const { selectedContractId } = useSelectedContractStore();

  return (
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
  );
};

export default ContractBoard;
