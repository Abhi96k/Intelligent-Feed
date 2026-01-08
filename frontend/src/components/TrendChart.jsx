import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Scatter, ComposedChart, Cell } from 'recharts'

/**
 * TrendChart Component
 * Displays time series trend data using a line chart with anomaly markers
 *
 * @param {Object} props
 * @param {Object} props.data - Trend data object
 * @param {string} props.data.metric_name - Name of the metric
 * @param {Array} props.data.time_series - Array of {date, value} objects
 * @param {string} props.data.trend_direction - Direction of trend (up/down/stable)
 * @param {number} props.data.percent_change - Percentage change
 * @param {Array} props.data.anomalies - Array of anomaly points
 */
function TrendChart({ data }) {
  if (!data || !data.time_series || data.time_series.length === 0) {
    return (
      <div className="card">
        <h3 className="card-header">Primary Trend</h3>
        <div className="text-center py-8 text-gray-500">
          No trend data available
        </div>
      </div>
    )
  }

  const {
    metric_name = 'Metric',
    time_series = [],
    trend_direction = 'stable',
    percent_change = 0,
    anomalies = [],
  } = data

  // Helper to extract just the date part (handles "2024-01-01", "2024-01-01T00:00:00", "2024-01-01 00:00:00")
  const extractDatePart = (dateStr) => {
    if (!dateStr) return ''
    // Handle both ISO format (T separator) and space separator
    return dateStr.split('T')[0].split(' ')[0]
  }

  // Create a Set of anomaly dates for fast lookup
  const anomalyDates = new Set(
    anomalies.map(a => extractDatePart(a.date))
  )
  
  // Get anomaly severity for a date
  const getAnomalySeverity = (dateStr) => {
    const targetDate = extractDatePart(dateStr)
    const anomaly = anomalies.find(a => extractDatePart(a.date) === targetDate)
    return anomaly?.severity || null
  }

  // Format the data for Recharts, marking anomalies
  const chartData = time_series.map(point => {
    const dateStr = point.date || point.time || point.timestamp
    const datePart = extractDatePart(dateStr)
    const isAnomaly = anomalyDates.has(datePart)
    return {
      date: dateStr,
      value: point.value,
      label: formatDate(dateStr),
      isAnomaly,
      anomalyValue: isAnomaly ? point.value : null,
      severity: isAnomaly ? getAnomalySeverity(dateStr) : null,
    }
  })

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload
      return (
        <div className={`p-3 border rounded-lg shadow-lg ${dataPoint.isAnomaly ? 'bg-red-50 border-red-300' : 'bg-white border-gray-200'}`}>
          <p className="text-xs text-gray-500 mb-1">{dataPoint.label}</p>
          <p className="text-sm font-semibold text-gray-900">
            {metric_name}: {formatValue(payload[0].value)}
          </p>
          {dataPoint.isAnomaly && (
            <div className="mt-2 pt-2 border-t border-red-200">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                ⚠️ Anomaly Detected
              </span>
              {dataPoint.severity && (
                <p className="text-xs text-red-600 mt-1">
                  Severity: {typeof dataPoint.severity === 'number' ? (dataPoint.severity > 0.7 ? 'High' : dataPoint.severity > 0.4 ? 'Medium' : 'Low') : dataPoint.severity}
                </p>
              )}
            </div>
          )}
        </div>
      )
    }
    return null
  }

  // Determine trend color
  const getTrendColor = () => {
    switch (trend_direction?.toLowerCase()) {
      case 'up':
      case 'increasing':
        return percent_change > 0 ? '#22c55e' : '#ef4444'
      case 'down':
      case 'decreasing':
        return percent_change < 0 ? '#ef4444' : '#22c55e'
      default:
        return '#3b82f6'
    }
  }

  const getTrendIcon = () => {
    switch (trend_direction?.toLowerCase()) {
      case 'up':
      case 'increasing':
        return (
          <svg className="h-5 w-5 text-success-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        )
      case 'down':
      case 'decreasing':
        return (
          <svg className="h-5 w-5 text-error-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6" />
          </svg>
        )
      default:
        return (
          <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
          </svg>
        )
    }
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="card-header mb-2">Primary Trend</h3>
          <p className="text-sm text-gray-600">{metric_name}</p>
        </div>
        <div className="text-right">
          <div className="flex items-center space-x-2">
            {getTrendIcon()}
            <span className="text-lg font-semibold text-gray-900">
              {percent_change > 0 ? '+' : ''}{percent_change.toFixed(1)}%
            </span>
          </div>
          <span className="text-xs text-gray-500 capitalize">{trend_direction}</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickFormatter={(value) => formatDate(value)}
          />
          <YAxis
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickFormatter={(value) => formatValue(value, true)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={getTrendColor()}
            strokeWidth={2}
            dot={(props) => {
              const { cx, cy, payload } = props
              if (payload.isAnomaly) {
                return (
                  <circle
                    key={`anomaly-${cx}-${cy}`}
                    cx={cx}
                    cy={cy}
                    r={8}
                    fill="#ef4444"
                    stroke="#fff"
                    strokeWidth={2}
                  />
                )
              }
              return (
                <circle
                  key={`normal-${cx}-${cy}`}
                  cx={cx}
                  cy={cy}
                  r={3}
                  fill={getTrendColor()}
                />
              )
            }}
            activeDot={{ r: 6 }}
            name={metric_name}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Anomaly Legend & Info */}
      {anomalies && anomalies.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <span className="w-4 h-4 rounded-full bg-red-500 mr-2"></span>
                <span className="text-xs text-gray-600">Anomaly Points ({anomalies.length})</span>
              </div>
              <div className="flex items-center">
                <span className="w-4 h-4 rounded-full mr-2" style={{ backgroundColor: getTrendColor() }}></span>
                <span className="text-xs text-gray-600">Normal Data</span>
              </div>
            </div>
            <span className="text-xs font-medium text-red-600">
              {anomalies.filter(a => a.severity > 0.7 || a.severity === 'high').length} High Severity
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper function to format dates
function formatDate(dateString) {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch (e) {
    return String(dateString)
  }
}

// Helper function to format values
function formatValue(value, compact = false) {
  if (typeof value !== 'number') return value

  if (compact && Math.abs(value) >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`
  } else if (compact && Math.abs(value) >= 1000) {
    return `${(value / 1000).toFixed(1)}K`
  }

  return value.toLocaleString('en-US', {
    maximumFractionDigits: 2,
  })
}

export default TrendChart
