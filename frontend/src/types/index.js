/**
 * Type Definitions for Intelligent Feed
 * Using JSDoc for type safety in JavaScript
 */

/**
 * @typedef {Object} Insight
 * @property {string} insight_type - Type of insight (anomaly, trend, correlation, etc.)
 * @property {boolean} triggered - Whether the insight was triggered
 * @property {string} title - Insight title
 * @property {string} description - Detailed description
 * @property {number} confidence - Confidence score (0-1)
 * @property {Object} metadata - Additional metadata
 */

/**
 * @typedef {Object} TimeSeriesPoint
 * @property {string} date - Date/time stamp
 * @property {number} value - Metric value
 */

/**
 * @typedef {Object} PrimaryTrend
 * @property {string} metric_name - Name of the metric
 * @property {TimeSeriesPoint[]} time_series - Array of time series data points
 * @property {string} trend_direction - Direction of trend (up/down/stable)
 * @property {number} percent_change - Percentage change
 * @property {Object[]} [anomalies] - Optional anomalies detected
 */

/**
 * @typedef {Object} Driver
 * @property {string} driver_name - Name of the driver
 * @property {number} impact_score - Impact score (can be positive or negative)
 * @property {string} direction - Direction of impact (positive/negative)
 * @property {Object} [metadata] - Additional driver metadata
 */

/**
 * @typedef {Object} DriverImpact
 * @property {Driver[]} drivers - Array of drivers
 * @property {string} primary_driver - Name of the primary driver
 * @property {Object} [metadata] - Additional metadata
 */

/**
 * @typedef {Object} AnalysisMetadata
 * @property {string} analysis_timestamp - Timestamp of analysis
 * @property {number} total_insights - Total number of insights
 * @property {number} triggered_insights - Number of triggered insights
 * @property {number} confidence_score - Overall confidence score
 * @property {string} [model_version] - Model version used
 */

/**
 * @typedef {Object} AnalysisResponse
 * @property {string} question - Original question
 * @property {Insight[]} insights - Array of insights
 * @property {PrimaryTrend} [primary_trend] - Primary trend data
 * @property {DriverImpact} [driver_impact] - Driver impact analysis
 * @property {string} [summary] - Summary text
 * @property {AnalysisMetadata} [metadata] - Analysis metadata
 */

/**
 * @typedef {Object} AnalysisRequest
 * @property {string} question - User question to analyze
 */

/**
 * @typedef {Object} HealthStatus
 * @property {string} status - Health status (healthy/unhealthy)
 * @property {string} timestamp - Timestamp of health check
 * @property {Object} [details] - Additional health details
 */

/**
 * @typedef {Object} ApiError
 * @property {string} error - Error message
 * @property {string} [detail] - Detailed error information
 * @property {number} [status_code] - HTTP status code
 */

/**
 * @typedef {Object} FeedbackData
 * @property {string} insight_id - Insight identifier
 * @property {boolean} helpful - Whether the insight was helpful
 * @property {string} [comment] - Optional comment
 */

// Export empty object to make this a module
export default {}
