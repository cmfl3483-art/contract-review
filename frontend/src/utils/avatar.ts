/**
 * Avatar Utilities
 *
 * Utilities for generating avatar colors and initials
 */

/**
 * Predefined color palette for avatars
 * Using a set of visually distinct, accessible colors
 */
const AVATAR_COLORS = [
  '#1890ff', // Blue
  '#52c41a', // Green
  '#faad14', // Orange
  '#f5222d', // Red
  '#722ed1', // Purple
  '#13c2c2', // Cyan
  '#eb2f96', // Magenta
  '#fa8c16', // Volcano
  '#a0d911', // Lime
  '#2f54eb', // Geek Blue
  '#fa541c', // Orange Red
  '#9254de', // Purple Light
];

/**
 * Generate a consistent color for a user based on their name
 *
 * Uses a simple hash function to map the name to a color from the palette.
 * The same name will always produce the same color.
 *
 * @param name - User name
 * @returns Hex color code
 *
 * @example
 * getAvatarColor('张三') // "#1890ff"
 * getAvatarColor('李四') // "#52c41a"
 * getAvatarColor('张三') // "#1890ff" (same as first call)
 */
export function getAvatarColor(name: string): string {
  if (!name) return AVATAR_COLORS[0];

  // Simple hash function
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash; // Convert to 32-bit integer
  }

  // Map hash to color index
  const index = Math.abs(hash) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
}

/**
 * Get initials from a name
 *
 * Rules:
 * - Chinese names: Use the last character (usually the given name)
 * - English names: Use the first letter of first and last name
 * - Single word: Use the first character
 *
 * @param name - User name
 * @returns Initials (1-2 characters)
 *
 * @example
 * getInitials('张三') // "三"
 * getInitials('李明华') // "华"
 * getInitials('John Doe') // "JD"
 * getInitials('Alice') // "A"
 */
export function getInitials(name: string): string {
  if (!name) return '?';

  const trimmed = name.trim();

  // Check if it's likely a Chinese name (contains Chinese characters)
  const hasChinese = /[\u4e00-\u9fa5]/.test(trimmed);

  if (hasChinese) {
    // For Chinese names, use the last character
    return trimmed.charAt(trimmed.length - 1);
  }

  // For English names, split by space
  const parts = trimmed.split(/\s+/);

  if (parts.length === 1) {
    // Single word: use first character
    return parts[0].charAt(0).toUpperCase();
  }

  // Multiple words: use first letter of first and last word
  const first = parts[0].charAt(0).toUpperCase();
  const last = parts[parts.length - 1].charAt(0).toUpperCase();
  return first + last;
}

/**
 * Generate avatar style object for use in React components
 *
 * @param name - User name
 * @param size - Avatar size in pixels (default: 32)
 * @returns Style object with backgroundColor, color, and size
 *
 * @example
 * const style = getAvatarStyle('张三', 40);
 * // { backgroundColor: '#1890ff', color: '#fff', width: 40, height: 40 }
 */
export function getAvatarStyle(
  name: string,
  size: number = 32
): {
  backgroundColor: string;
  color: string;
  width: number;
  height: number;
  fontSize: number;
} {
  return {
    backgroundColor: getAvatarColor(name),
    color: '#fff',
    width: size,
    height: size,
    fontSize: Math.floor(size * 0.4), // Font size is 40% of avatar size
  };
}

/**
 * Generate a data URL for an avatar image with initials
 *
 * This creates a simple SVG avatar with the user's initials and color.
 * Can be used as an img src or background image.
 *
 * @param name - User name
 * @param size - Avatar size in pixels (default: 32)
 * @returns Data URL string
 *
 * @example
 * const avatarUrl = generateAvatarDataUrl('张三', 40);
 * <img src={avatarUrl} alt="Avatar" />
 */
export function generateAvatarDataUrl(name: string, size: number = 32): string {
  const initials = getInitials(name);
  const color = getAvatarColor(name);
  const fontSize = Math.floor(size * 0.4);

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">
      <rect width="${size}" height="${size}" fill="${color}" />
      <text
        x="50%"
        y="50%"
        dominant-baseline="middle"
        text-anchor="middle"
        fill="#fff"
        font-family="Arial, sans-serif"
        font-size="${fontSize}"
        font-weight="500"
      >${initials}</text>
    </svg>
  `;

  // Encode SVG to data URL
  const encoded = encodeURIComponent(svg).replace(/'/g, '%27').replace(/"/g, '%22');

  return `data:image/svg+xml,${encoded}`;
}

/**
 * Get a contrasting text color (black or white) for a given background color
 *
 * Uses the relative luminance formula to determine if white or black text
 * would be more readable on the given background color.
 *
 * @param hexColor - Background color in hex format
 * @returns '#000' or '#fff'
 *
 * @example
 * getContrastColor('#1890ff') // "#fff"
 * getContrastColor('#faad14') // "#000"
 */
export function getContrastColor(hexColor: string): string {
  // Remove # if present
  const hex = hexColor.replace('#', '');

  // Convert to RGB
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);

  // Calculate relative luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  // Return black for light backgrounds, white for dark backgrounds
  return luminance > 0.5 ? '#000' : '#fff';
}
