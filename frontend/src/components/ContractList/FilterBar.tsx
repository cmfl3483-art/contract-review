import { Button, Badge, Space } from 'antd';
import './FilterBar.css';

export type FilterType = 'all' | '进行中' | '已完成' | '待我处理' | '抄送我' | '我发起的' | '我已审批';

interface FilterBarProps {
  activeFilter: FilterType;
  onFilterChange: (filter: FilterType) => void;
  pendingCount?: number;
}

const FilterBar: React.FC<FilterBarProps> = ({
  activeFilter,
  onFilterChange,
  pendingCount = 0,
}) => {
  const filters: { key: FilterType; label: string }[] = [
    { key: 'all', label: '全部' },
    { key: '进行中', label: '进行中' },
    { key: '已完成', label: '已完成' },
    { key: '待我处理', label: '待我处理' },
    { key: '抄送我', label: '抄送我' },
    { key: '我发起的', label: '我发起的' },
    { key: '我已审批', label: '我已审批' },
  ];

  return (
    <Space wrap className="filter-bar">
      {filters.map((filter) => {
        const isActive = activeFilter === filter.key;

        // 为"待我处理"按钮添加徽章
        if (filter.key === '待我处理' && pendingCount > 0) {
          return (
            <Badge key={filter.key} count={pendingCount} offset={[-2, 6]}>
              <Button
                type={isActive ? 'primary' : 'default'}
                onClick={() => onFilterChange(filter.key)}
                className={isActive ? 'filter-button-active' : 'filter-button'}
              >
                {filter.label}
              </Button>
            </Badge>
          );
        }

        return (
          <Button
            key={filter.key}
            type={isActive ? 'primary' : 'default'}
            onClick={() => onFilterChange(filter.key)}
            className={isActive ? 'filter-button-active' : 'filter-button'}
          >
            {filter.label}
          </Button>
        );
      })}
    </Space>
  );
};

export default FilterBar;
