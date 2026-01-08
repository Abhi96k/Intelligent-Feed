/**
 * Utility functions for formatting data
 */

/**
 * Format a date string to a readable format
 * @param {string|Date} dateString - Date to format
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export function formatDate(dateString, options = {}) {
  if (!dateString) return ''

  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return String(dateString)

    const defaultOptions = {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      ...options,
    }

    return date.toLocaleDateString('en-US', defaultOptions)
  } catch (e) {
    return String(dateString)
  }
}

/**
 * Format a timestamp to include time
 * @param {string|Date} timestamp - Timestamp to format
 * @returns {string} Formatted timestamp
 */
export function formatTimestamp(timestamp) {
  if (!timestamp) return ''

  try {
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) return String(timestamp)

    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch (e) {
    return String(timestamp)
  }
}

/**
 * Format a number with commas and optional decimal places
 * @param {number} value - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number
 */
export function formatNumber(value, decimals = 0) {
  if (typeof value !== 'number' || isNaN(value)) {
    return String(value)
  }

  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

/**
 * Format a number as currency
 * @param {number} value - Number to format as currency
 * @param {string} currency - Currency code (default: USD)
 * @returns {string} Formatted currency string
 */
export function formatCurrency(value, currency = 'USD') {
  if (typeof value !== 'number' || isNaN(value)) {
    return String(value)
  }

  return value.toLocaleString('en-US', {
    style: 'currency',
    currency: currency,
  })
}

/**
 * Format a number as a percentage
 * @param {number} value - Number to format (0-1 or 0-100)
 * @param {number} decimals - Decimal places
 * @param {boolean} isDecimal - Whether value is already 0-1 (default: true)
 * @returns {string} Formatted percentage
 */
export function formatPercentage(value, decimals = 1, isDecimal = true) {
  if (typeof value !== 'number' || isNaN(value)) {
    return String(value)
  }

  const percentage = isDecimal ? value * 100 : value
  return `${percentage.toFixed(decimals)}%`
}

/**
 * Format a large number with K/M/B suffixes
 * @param {number} value - Number to format
 * @param {number} decimals - Decimal places
 * @returns {string} Formatted compact number
 */
export function formatCompactNumber(value, decimals = 1) {
  if (typeof value !== 'number' || isNaN(value)) {
    return String(value)
  }

  const absValue = Math.abs(value)
  const sign = value < 0 ? '-' : ''

  if (absValue >= 1e9) {
    return `${sign}${(absValue / 1e9).toFixed(decimals)}B`
  } else if (absValue >= 1e6) {
    return `${sign}${(absValue / 1e6).toFixed(decimals)}M`
  } else if (absValue >= 1e3) {
    return `${sign}${(absValue / 1e3).toFixed(decimals)}K`
  }

  return formatNumber(value, decimals)
}

/**
 * Truncate text to a maximum length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @param {string} suffix - Suffix to add (default: '...')
 * @returns {string} Truncated text
 */
export function truncateText(text, maxLength = 100, suffix = '...') {
  if (!text || typeof text !== 'string') return ''
  if (text.length <= maxLength) return text

  return text.substring(0, maxLength - suffix.length) + suffix
}

/**
 * Convert a string to title case
 * @param {string} str - String to convert
 * @returns {string} Title case string
 */
export function toTitleCase(str) {
  if (!str || typeof str !== 'string') return ''

  return str
    .toLowerCase()
    .split(/[\s_-]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Calculate relative time (e.g., "2 hours ago")
 * @param {string|Date} dateString - Date to calculate from
 * @returns {string} Relative time string
 */
export function getRelativeTime(dateString) {
  if (!dateString) return ''

  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return String(dateString)

    const now = new Date()
    const diffMs = now - date
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHour = Math.floor(diffMin / 60)
    const diffDay = Math.floor(diffHour / 24)

    if (diffSec < 60) return 'just now'
    if (diffMin < 60) return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`
    if (diffHour < 24) return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`
    if (diffDay < 7) return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`

    return formatDate(date)
  } catch (e) {
    return String(dateString)
  }
}

export default {
  formatDate,
  formatTimestamp,
  formatNumber,
  formatCurrency,
  formatPercentage,
  formatCompactNumber,
  truncateText,
  toTitleCase,
  getRelativeTime,
}
