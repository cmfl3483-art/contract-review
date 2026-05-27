import { Layout } from 'antd';
import { useUserStore } from '../stores/useUserStore';
import NotificationCenter from '../components/NotificationCenter/NotificationCenter';
import '../components/NotificationCenter/NotificationCenter.css';
import './MainLayout.css';

const { Header, Footer, Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const currentUser = useUserStore((state) => state.currentUser);

  return (
    <Layout className="main-layout">
      <Header className="main-header">
        <h1>合同预审看板系统</h1>
        <div className="main-header-actions">
          <NotificationCenter />
        </div>
      </Header>
      <Content className="main-content">{children}</Content>
      <Footer className="main-footer">
        <span>
          当前用户: {currentUser ? currentUser.name : '未登录'}
        </span>
      </Footer>
    </Layout>
  );
};

export default MainLayout;
