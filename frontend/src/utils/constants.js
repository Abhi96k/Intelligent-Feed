/**
 * Application constants and configuration
 */

// API Configuration
export const API_CONFIG = {
  TIMEOUT: 30000, // 30 seconds
  RETRY_COUNT: 1,
  BASE_URL: '/api',
}

// Query Configuration
export const QUERY_CONFIG = {
  STALE_TIME: 5 * 60 * 1000, // 5 minutes
  CACHE_TIME: 10 * 60 * 1000, // 10 minutes
  RETRY: 1,
  REFETCH_ON_WINDOW_FOCUS: false,
}

// Insight Types
export const INSIGHT_TYPES = {
  ANOMALY: 'anomaly',
  TREND: 'trend',
  PATTERN: 'pattern',
  CORRELATION: 'correlation',
  DRIVER: 'driver',
  SPIKE: 'spike',
  DROP: 'drop',
  GENERAL: 'general',
}

// Trend Directions
export const TREND_DIRECTIONS = {
  UP: 'up',
  DOWN: 'down',
  STABLE: 'stable',
  INCREASING: 'increasing',
  DECREASING: 'decreasing',
}

// Impact Directions
export const IMPACT_DIRECTIONS = {
  POSITIVE: 'positive',
  NEGATIVE: 'negative',
  NEUTRAL: 'neutral',
}

// Chart Colors
export const CHART_COLORS = {
  PRIMARY: '#3b82f6',
  SUCCESS: '#22c55e',
  ERROR: '#ef4444',
  WARNING: '#f97316',
  INFO: '#06b6d4',
  GRAY: '#6b7280',
}

// Status Colors
export const STATUS_COLORS = {
  HEALTHY: '#22c55e',
  DEGRADED: '#f97316',
  UNHEALTHY: '#ef4444',
}

// Example Questions
export const EXAMPLE_QUESTIONS = [
  'Why did revenue drop in Q3?',
  'What are the main drivers of customer churn?',
  'Show me sales trends by region',
  'What caused the spike in expenses last month?',
  'Analyze product performance trends',
]

// Local Storage Keys
export const STORAGE_KEYS = {
  RECENT_QUESTIONS: 'intelligent_feed_recent_questions',
  USER_PREFERENCES: 'intelligent_feed_preferences',
}

// UI Constants
export const UI_CONSTANTS = {
  MAX_QUESTION_LENGTH: 500,
  MAX_RECENT_QUESTIONS: 10,
  DEBOUNCE_DELAY: 300,
  TOAST_DURATION: 5000,
}

export default {
  API_CONFIG,
  QUERY_CONFIG,
  INSIGHT_TYPES,
  TREND_DIRECTIONS,
  IMPACT_DIRECTIONS,
  CHART_COLORS,
  STATUS_COLORS,
  EXAMPLE_QUESTIONS,
  STORAGE_KEYS,
  UI_CONSTANTS,
}
