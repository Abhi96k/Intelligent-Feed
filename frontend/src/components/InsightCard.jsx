/**
 * InsightCard Component
 * Displays individual insight with triggered status and details
 *
 * @param {Object} props
 * @param {Object} props.insight - Insight data object
 * @param {string} props.insight.insight_type - Type of insight
 * @param {boolean} props.insight.triggered - Whether insight was triggered
 * @param {string} props.insight.title - Insight title
 * @param {string} props.insight.description - Insight description
 * @param {number} props.insight.confidence - Confidence score (0-1)
 * @param {Object} props.insight.metadata - Additional metadata
 */
function InsightCard({ insight }) {
  const {
    insight_type = 'general',
    triggered = false,
    title = 'Untitled Insight',
    description = '',
    confidence = 0,
    metadata = {},
  } = insight

  // Determine card styling based on triggered status
  const cardClasses = triggered
    ? 'card border-l-4 border-l-success-500 bg-success-50'
    : 'card border-l-4 border-l-gray-300 bg-gray-50'

  const badgeClasses = triggered ? 'badge badge-success' : 'badge bg-gray-200 text-gray-600'

  // Get icon based on insight type
  const getInsightIcon = () => {
    const iconClasses = triggered ? 'text-success-600' : 'text-gray-400'

    switch (insight_type.toLowerCase()) {
      case 'anomaly':
      case 'spike':
      case 'drop':
        return (
          <svg className={`h-5 w-5 ${iconClasses}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        )
      case 'trend':
      case 'pattern':
        return (
          <svg className={`h-5 w-5 ${iconClasses}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        )
      case 'correlation':
      case 'driver':
        return (
          <svg className={`h-5 w-5 ${iconClasses}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        )
      default:
        return (
          <svg className={`h-5 w-5 ${iconClasses}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  return (
    <div className={cardClasses}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getInsightIcon()}
          <span className={badgeClasses}>
            {triggered ? 'Triggered' : 'Not Triggered'}
          </span>
        </div>
        {confidence > 0 && (
          <div className="flex items-center space-x-1">
            <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-xs text-gray-500">
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      <h3 className="text-base font-semibold text-gray-900 mb-2">
        {title}
      </h3>

      {description && (
        <p className="text-sm text-gray-700 mb-3 leading-relaxed">
          {description}
        </p>
      )}

      {/* Metadata */}
      {metadata && Object.keys(metadata).length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-3 text-xs">
            {Object.entries(metadata).map(([key, value]) => (
              <div key={key}>
                <span className="text-gray-500 capitalize">
                  {key.replace(/_/g, ' ')}
                </span>
                <p className="font-medium text-gray-900 mt-0.5">
                  {typeof value === 'number' && value < 1 && value > 0
                    ? `${(value * 100).toFixed(1)}%`
                    : typeof value === 'object'
                    ? JSON.stringify(value)
                    : String(value)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insight Type Badge */}
      <div className="mt-3">
        <span className="inline-flex items-center text-xs text-gray-500">
          <span className="capitalize">{insight_type}</span>
        </span>
      </div>
    </div>
  )
}

export default InsightCard
