/**
 * AlertBanner Component
 * Displays alert status banner when insights are triggered
 *
 * @param {Object} props
 * @param {boolean} props.triggered - Whether the alert was triggered
 * @param {string} props.triggerReason - Reason for the trigger
 * @param {Object} props.alertConfig - Alert configuration from backend
 * @param {string} props.metric - Metric name
 * @param {number} props.confidence - Confidence score (0-100)
 */
function AlertBanner({
  triggered,
  triggerReason,
  alertConfig,
  metric,
  confidence,
}) {
  if (!triggered && !triggerReason) {
    return null;
  }

  // Get severity color classes
  const getSeverityClasses = () => {
    const severity = alertConfig?.severity || "medium";

    switch (severity.toLowerCase()) {
      case "critical":
        return {
          bg: "bg-error-100",
          border: "border-error-500",
          text: "text-error-800",
          icon: "text-error-600",
          badge: "bg-error-500 text-white",
        };
      case "high":
        return {
          bg: "bg-warning-100",
          border: "border-warning-500",
          text: "text-warning-800",
          icon: "text-warning-600",
          badge: "bg-warning-500 text-white",
        };
      case "medium":
        return {
          bg: "bg-primary-100",
          border: "border-primary-500",
          text: "text-primary-800",
          icon: "text-primary-600",
          badge: "bg-primary-500 text-white",
        };
      case "low":
      default:
        return {
          bg: "bg-gray-100",
          border: "border-gray-500",
          text: "text-gray-800",
          icon: "text-gray-600",
          badge: "bg-gray-500 text-white",
        };
    }
  };

  // Get alert type icon
  const getAlertIcon = () => {
    const alertType = alertConfig?.alert_type || "unknown";
    const colors = getSeverityClasses();

    switch (alertType.toLowerCase()) {
      case "drop":
      case "decrease":
        return (
          <svg
            className={`h-6 w-6 ${colors.icon}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"
            />
          </svg>
        );
      case "increase":
      case "spike":
        return (
          <svg
            className={`h-6 w-6 ${colors.icon}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
            />
          </svg>
        );
      case "anomaly":
        return (
          <svg
            className={`h-6 w-6 ${colors.icon}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        );
      default:
        return (
          <svg
            className={`h-6 w-6 ${colors.icon}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
        );
    }
  };

  const colors = getSeverityClasses();
  const severity = alertConfig?.severity || "medium";
  const alertType = alertConfig?.alert_type || "alert";
  const threshold = alertConfig?.threshold_percent || 5;

  if (triggered) {
    return (
      <div
        className={`${colors.bg} border-l-4 ${colors.border} p-4 rounded-r-lg shadow-sm`}
      >
        <div className="flex items-start">
          <div className="flex-shrink-0">{getAlertIcon()}</div>
          <div className="ml-4 flex-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <h3 className={`text-lg font-semibold ${colors.text}`}>
                  Alert Triggered
                </h3>
                <span
                  className={`px-2 py-0.5 text-xs font-medium rounded-full uppercase ${colors.badge}`}
                >
                  {severity}
                </span>
                <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-200 text-gray-700 capitalize">
                  {alertType}
                </span>
              </div>
              {confidence !== undefined && (
                <div className="flex items-center space-x-1 text-sm text-gray-600">
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span>{confidence.toFixed(1)}% confidence</span>
                </div>
              )}
            </div>
            <p className={`mt-2 ${colors.text}`}>{triggerReason}</p>
            <div className="mt-3 flex items-center space-x-4 text-sm">
              <span className="text-gray-600">
                <strong>Metric:</strong> {metric}
              </span>
              <span className="text-gray-600">
                <strong>Threshold:</strong> {threshold}%
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Not triggered state
  return (
    <div className="bg-success-50 border-l-4 border-success-500 p-4 rounded-r-lg shadow-sm">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg
            className="h-6 w-6 text-success-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div className="ml-4 flex-1">
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-semibold text-success-800">
              No Alert Triggered
            </h3>
            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-success-200 text-success-800">
              Normal
            </span>
          </div>
          <p className="mt-2 text-success-700">
            {triggerReason ||
              `${metric} is within the expected range. No significant changes detected.`}
          </p>
        </div>
      </div>
    </div>
  );
}

export default AlertBanner;
