import { useEffect, useMemo, useState } from 'react';
import { Modal, Tree, Input, Checkbox, Empty, Spin, Tag, Avatar, message } from 'antd';
import { SearchOutlined, UserOutlined, CloseOutlined } from '@ant-design/icons';
import type { DataNode } from 'antd/es/tree';
import axios from '../../utils/axios';
import { API_BASE_URL } from '../../config/api';
import './UserPicker.css';

// 模块级通讯录缓存: 10 分钟内重复打开弹窗不再发请求
let _contactsCache: ContactsPayload | null = null;
let _contactsCacheAt = 0;
const CONTACTS_CACHE_TTL = 10 * 60 * 1000; // 10 分钟

export interface PickerUser {
  id: string;
  name: string;
  role: string;
  email?: string | null;
  mobile?: string | null;
  avatar?: string | null;
  department?: string | null;
  dept_ids: number[];
}

interface DeptNode {
  id: number;
  name: string;
  parent_id: number;
  children: DeptNode[];
}

interface ContactsPayload {
  departments: DeptNode[];
  users: PickerUser[];
}

interface UserPickerProps {
  visible: boolean;
  title: string;
  multiple?: boolean;
  selectedIds: string[];
  onChange: (ids: string[], users: PickerUser[]) => void;
  onClose: () => void;
}

const ROOT_KEY = '__all__';

function flattenDeptIds(node: DeptNode): number[] {
  const ids: number[] = [node.id];
  for (const c of node.children || []) ids.push(...flattenDeptIds(c));
  return ids;
}

function toTreeData(nodes: DeptNode[]): DataNode[] {
  return nodes.map((n) => ({
    key: String(n.id),
    title: n.name,
    children: n.children && n.children.length ? toTreeData(n.children) : undefined,
  }));
}

const UserPicker: React.FC<UserPickerProps> = ({
  visible,
  title,
  multiple = true,
  selectedIds,
  onChange,
  onClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ContactsPayload | null>(null);
  const [keyword, setKeyword] = useState('');
  const [activeKey, setActiveKey] = useState<string>(ROOT_KEY);
  const [tempSelected, setTempSelected] = useState<string[]>(selectedIds);

  // 弹窗打开时拉取通讯录 + 同步外部已选
  useEffect(() => {
    if (!visible) return;
    setTempSelected(selectedIds);
    setKeyword('');
    setActiveKey(ROOT_KEY);

    // 优先使用模块级缓存
    const now = Date.now();
    if (_contactsCache && now - _contactsCacheAt < CONTACTS_CACHE_TTL) {
      setData(_contactsCache);
      setLoading(false);
      return;
    }

    let cancelled = false;
    const fetchContacts = async () => {
      setLoading(true);
      try {
        const resp = await axios.get(`${API_BASE_URL}/api/dingtalk/contacts`);
        if (cancelled) return;
        if (resp.data.success) {
          _contactsCache = resp.data.data;
          _contactsCacheAt = Date.now();
          setData(resp.data.data);
        } else {
          message.error('获取钉钉通讯录失败');
        }
      } catch (err: unknown) {
        if (cancelled) return;
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        message.error(detail || '获取钉钉通讯录失败, 请检查后台与钉钉应用权限');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchContacts();
    return () => {
      cancelled = true;
    };
  }, [visible, selectedIds]);

  // 部门树数据 (前面加一个"全公司"虚拟节点)
  const treeData = useMemo<DataNode[]>(() => {
    if (!data) return [];
    const root: DataNode = {
      key: ROOT_KEY,
      title: '全公司',
      children: toTreeData(data.departments),
    };
    return [root];
  }, [data]);

  // 当前部门下应展示的用户 (含子部门)
  const filteredUsers = useMemo<PickerUser[]>(() => {
    if (!data) return [];
    const kw = keyword.trim().toLowerCase();

    // 先按部门过滤
    let scoped: PickerUser[] = data.users;
    if (activeKey && activeKey !== ROOT_KEY) {
      const target = Number(activeKey);
      // 找到目标节点, 收集其所有后代 dept id
      const findNode = (nodes: DeptNode[], id: number): DeptNode | null => {
        for (const n of nodes) {
          if (n.id === id) return n;
          const r = findNode(n.children || [], id);
          if (r) return r;
        }
        return null;
      };
      const node = findNode(data.departments, target);
      if (node) {
        const ids = new Set(flattenDeptIds(node));
        scoped = data.users.filter((u) =>
          (u.dept_ids || []).some((d) => ids.has(d))
        );
      }
    }

    // 再按关键词过滤 (姓名/部门/手机/邮箱)
    if (kw) {
      scoped = scoped.filter((u) => {
        const haystack = [u.name, u.department, u.mobile, u.email, u.role]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        return haystack.includes(kw);
      });
    }
    return scoped;
  }, [data, activeKey, keyword]);

  // 已选的完整 user 列表 (按 tempSelected 顺序)
  const selectedUsers = useMemo<PickerUser[]>(() => {
    if (!data) return [];
    const map = new Map(data.users.map((u) => [u.id, u]));
    return tempSelected.map((id) => map.get(id)).filter(Boolean) as PickerUser[];
  }, [data, tempSelected]);

  const toggleUser = (uid: string) => {
    if (multiple) {
      setTempSelected((prev) =>
        prev.includes(uid) ? prev.filter((x) => x !== uid) : [...prev, uid]
      );
    } else {
      setTempSelected([uid]);
    }
  };

  const removeSelected = (uid: string) => {
    setTempSelected((prev) => prev.filter((x) => x !== uid));
  };

  const handleOk = () => {
    if (!data) {
      onChange(tempSelected, []);
    } else {
      const map = new Map(data.users.map((u) => [u.id, u]));
      const users = tempSelected.map((id) => map.get(id)).filter(Boolean) as PickerUser[];
      onChange(tempSelected, users);
    }
    onClose();
  };

  return (
    <Modal
      open={visible}
      title={title}
      width={820}
      onCancel={onClose}
      onOk={handleOk}
      okText={`确定 (已选 ${tempSelected.length} 人)`}
      cancelText="取消"
      destroyOnClose
      styles={{ body: { padding: 0 } }}
    >
      <Spin spinning={loading}>
        <div className="user-picker-body">
          {/* 顶部搜索 */}
          <div className="user-picker-search">
            <Input
              allowClear
              prefix={<SearchOutlined />}
              placeholder="搜索姓名 / 部门 / 手机号"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
          </div>

          <div className="user-picker-main">
            {/* 左侧部门树 */}
            <div className="user-picker-tree">
              {data ? (
                <Tree
                  treeData={treeData}
                  defaultExpandAll
                  selectedKeys={[activeKey]}
                  onSelect={(keys) => {
                    if (keys.length > 0) setActiveKey(String(keys[0]));
                  }}
                  blockNode
                />
              ) : (
                <div className="user-picker-empty">
                  <Empty description="暂无部门" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                </div>
              )}
            </div>

            {/* 右侧成员 */}
            <div className="user-picker-list">
              {filteredUsers.length === 0 ? (
                <div className="user-picker-empty">
                  <Empty
                    description={keyword ? '没有匹配的成员' : '该部门暂无成员'}
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                </div>
              ) : (
                filteredUsers.map((u) => {
                  const checked = tempSelected.includes(u.id);
                  return (
                    <div
                      key={u.id}
                      className={`user-picker-item ${checked ? 'selected' : ''}`}
                      onClick={() => toggleUser(u.id)}
                    >
                      <Checkbox checked={checked} onChange={() => toggleUser(u.id)} />
                      <Avatar
                        size={32}
                        src={u.avatar || undefined}
                        icon={<UserOutlined />}
                      />
                      <div className="user-picker-info">
                        <div className="user-picker-name">
                          {u.name}
                          {u.role && u.role !== '业务' && (
                            <Tag color="blue" style={{ marginLeft: 6 }}>
                              {u.role}
                            </Tag>
                          )}
                        </div>
                        <div className="user-picker-meta">
                          {u.department || '未分部门'}
                          {u.mobile ? ` · ${u.mobile}` : ''}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* 底部已选 */}
          {tempSelected.length > 0 && (
            <div className="user-picker-selected">
              <span className="user-picker-selected-label">已选:</span>
              <div className="user-picker-selected-list">
                {selectedUsers.map((u) => (
                  <Tag
                    key={u.id}
                    closable
                    closeIcon={<CloseOutlined />}
                    onClose={(e) => {
                      e.preventDefault();
                      removeSelected(u.id);
                    }}
                    color="processing"
                  >
                    {u.name}
                    {u.department ? ` (${u.department})` : ''}
                  </Tag>
                ))}
              </div>
            </div>
          )}
        </div>
      </Spin>
    </Modal>
  );
};

export default UserPicker;
