import { Layout } from 'antd';
import { Link } from 'react-router-dom';
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
        {currentUser && (
          <nav className="main-header-nav">
            <Link to="/" className="main-header-nav-link">合同看板</Link>
            <Link to="/compliance" className="main-header-nav-link">合规审查</Link>
          </nav>
        )}
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
