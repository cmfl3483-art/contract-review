/**
 * 规范化后端返回的 ISO 时间字符串
 * 后端使用 datetime.utcnow().isoformat() 输出无时区后缀的 UTC 时间,
 * 浏览器 new Date() 会按本地时区解析导致偏差 8 小时。
 * 这里判断字符串末尾没有 Z/±HH:mm 后缀时补上 'Z' 强制识别为 UTC。
 */
function normalizeIsoString(s: string): string {
  if (!s) return s;
  // 已带时区后缀 (Z 或 +08:00 / -05:00) 则不动
  if (/[zZ]$|[+-]\d{2}:?\d{2}$/.test(s)) return s;
  return s + 'Z';
}

/**
 * 格式化相对时间
 * @param dateString - ISO 8601 格式的日期字符串
 * @returns 相对时间字符串（刚刚、N分钟前、N小时前、N天前等）
 */
export function formatRelativeTime(dateString: string): string {
  if (!dateString) {
    return '';
  }

  try {
    const now = new Date();
    const date = new Date(normalizeIsoString(dateString));
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      return dateString;
    }

    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSeconds < 60) {
      return '刚刚';
    } else if (diffMinutes < 60) {
      return `${diffMinutes}分钟前`;
    } else if (diffHours < 24) {
      return `${diffHours}小时前`;
    } else if (diffDays < 30) {
      return `${diffDays}天前`;
    } else if (diffDays < 365) {
      const diffMonths = Math.floor(diffDays / 30);
      return `${diffMonths}个月前`;
    } else {
      const diffYears = Math.floor(diffDays / 365);
      return `${diffYears}年前`;
    }
  } catch (error) {
    console.error('Error formatting relative time:', error);
    return dateString;
  }
}

/**
 * 格式化日期时间
 * @param dateString - ISO 8601 格式的日期字符串
 * @param format - 格式化模板（默认：YYYY-MM-DD HH:mm）
 * @returns 格式化后的日期时间字符串
 */
export function formatDateTime(dateString: string, format: string = 'YYYY-MM-DD HH:mm'): string {
  const date = new Date(normalizeIsoString(dateString));
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}
