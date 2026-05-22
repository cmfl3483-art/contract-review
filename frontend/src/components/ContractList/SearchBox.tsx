import { Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useState, useCallback, useRef, useEffect, memo } from 'react';

interface SearchBoxProps {
  onSearch: (keyword: string) => void;
  placeholder?: string;
}

const SearchBox: React.FC<SearchBoxProps> = memo(({
  onSearch,
  placeholder = '搜索合同名称或发起人',
}) => {
  const [value, setValue] = useState('');
  const timeoutRef = useRef<number | null>(null);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // 防抖搜索 (300ms)
  const debouncedSearch = useCallback(
    (keyword: string) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = window.setTimeout(() => {
        onSearch(keyword);
      }, 300);
    },
    [onSearch]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setValue(newValue);
    debouncedSearch(newValue);
  };

  const handleClear = () => {
    setValue('');
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    onSearch('');
  };

  return (
    <Input
      value={value}
      onChange={handleChange}
      onClear={handleClear}
      placeholder={placeholder}
      prefix={<SearchOutlined />}
      allowClear
    />
  );
});

SearchBox.displayName = 'SearchBox';

export default SearchBox;
