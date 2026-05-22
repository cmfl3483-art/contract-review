/**
 * Formatting Utilities
 *
 * Utilities for formatting various data types (file size, numbers, etc.)
 */

/**
 * Format file size in bytes to human-readable format
 *
 * @param bytes - File size in bytes
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted file size string
 *
 * @example
 * formatFileSize(1024) // "1.00 KB"
 * formatFileSize(1048576) // "1.00 MB"
 * formatFileSize(1073741824) // "1.00 GB"
 * formatFileSize(1234567, 1) // "1.2 MB"
 */
export function formatFileSize(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';
  if (bytes < 0) return 'Invalid size';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const size = parseFloat((bytes / Math.pow(k, i)).toFixed(dm));

  return `${size} ${sizes[i]}`;
}

/**
 * Format a number with thousand separators
 *
 * @param num - Number to format
 * @param separator - Separator character (default: ',')
 * @returns Formatted number string
 *
 * @example
 * formatNumber(1234567) // "1,234,567"
 * formatNumber(1234567.89) // "1,234,567.89"
 * formatNumber(1234567, ' ') // "1 234 567"
 */
export function formatNumber(num: number, separator: string = ','): string {
  const parts = num.toString().split('.');
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, separator);
  return parts.join('.');
}

/**
 * Format a percentage value
 *
 * @param value - Value to format (0-1 or 0-100)
 * @param decimals - Number of decimal places (default: 0)
 * @param isDecimal - Whether the value is in decimal format (0-1) or percentage format (0-100)
 * @returns Formatted percentage string
 *
 * @example
 * formatPercentage(0.5) // "50%"
 * formatPercentage(0.666, 2) // "66.60%"
 * formatPercentage(75, 0, false) // "75%"
 */
export function formatPercentage(
  value: number,
  decimals: number = 0,
  isDecimal: boolean = true
): string {
  const percentage = isDecimal ? value * 100 : value;
  return `${percentage.toFixed(decimals)}%`;
}

/**
 * Truncate a string to a maximum length with ellipsis
 *
 * @param str - String to truncate
 * @param maxLength - Maximum length
 * @param ellipsis - Ellipsis string (default: '...')
 * @returns Truncated string
 *
 * @example
 * truncateString('Hello World', 5) // "Hello..."
 * truncateString('Short', 10) // "Short"
 */
export function truncateString(str: string, maxLength: number, ellipsis: string = '...'): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + ellipsis;
}

/**
 * Format a phone number
 *
 * @param phone - Phone number string
 * @returns Formatted phone number
 *
 * @example
 * formatPhoneNumber('13812345678') // "138 1234 5678"
 * formatPhoneNumber('1381234567') // "138 1234 567"
 */
export function formatPhoneNumber(phone: string): string {
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 11) {
    return `${cleaned.slice(0, 3)} ${cleaned.slice(3, 7)} ${cleaned.slice(7)}`;
  }
  return phone;
}

/**
 * Capitalize the first letter of a string
 *
 * @param str - String to capitalize
 * @returns Capitalized string
 *
 * @example
 * capitalize('hello') // "Hello"
 * capitalize('HELLO') // "HELLO"
 */
export function capitalize(str: string): string {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Convert a string to title case
 *
 * @param str - String to convert
 * @returns Title case string
 *
 * @example
 * toTitleCase('hello world') // "Hello World"
 * toTitleCase('HELLO WORLD') // "Hello World"
 */
export function toTitleCase(str: string): string {
  return str
    .toLowerCase()
    .split(' ')
    .map((word) => capitalize(word))
    .join(' ');
}

/**
 * Parse a file extension from a filename
 *
 * @param filename - Filename to parse
 * @returns File extension (without dot) or empty string
 *
 * @example
 * getFileExtension('document.pdf') // "pdf"
 * getFileExtension('archive.tar.gz') // "gz"
 * getFileExtension('noextension') // ""
 */
export function getFileExtension(filename: string): string {
  const parts = filename.split('.');
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
}

/**
 * Get a filename without extension
 *
 * @param filename - Filename to parse
 * @returns Filename without extension
 *
 * @example
 * getFileNameWithoutExtension('document.pdf') // "document"
 * getFileNameWithoutExtension('archive.tar.gz') // "archive.tar"
 */
export function getFileNameWithoutExtension(filename: string): string {
  const lastDotIndex = filename.lastIndexOf('.');
  return lastDotIndex === -1 ? filename : filename.slice(0, lastDotIndex);
}
