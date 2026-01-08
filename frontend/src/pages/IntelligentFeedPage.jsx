import { useState } from 'react';
import AlertBanner from '../components/AlertBanner';
import InsightCard from '../components/InsightCard';
import TrendChart from '../components/TrendChart';
import DriverImpactChart from '../components/DriverImpactChart';

/**
 * IntelligentFeedPage Component
 * Main page showing triggered alerts from feeds
 */
function IntelligentFeedPage({ triggeredAlerts, feeds, onViewDetails, onFetchFeedRuns }) {
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [expandedRuns, setExpandedRuns] = useState({});
  const [feedRuns, setFeedRuns] = useState({});
  const [loadingRuns, setLoadingRuns] = useState({});
  const [sqlExpanded, setSqlExpanded] = useState(false);

  const handleAlertClick = (alert) => {
    setSelectedAlert(alert);
  };

  const handleBack = () => {
    setSelectedAlert(null);
  };

  // Helper functions for selected alert details
  const getInsights = (results) => {
    if (!results) return [];
    const insights = [];

    if (results.triggered) {
      insights.push({
        insight_type: results.evidence?.alert?.alert_type || 'trend',
        triggered: true,
        title: results.trigger_reason || 'Insight Triggered',
        description: results.what_happened || '',
        confidence: results.confidence / 100,
        metadata: {
          metric: results.metric,
          time_range: `${results.time_range?.start} to ${results.time_range?.end}`,
          ...results.evidence?.detection,
        },
      });

      if (results.evidence?.drivers?.length > 0) {
        results.evidence.drivers.slice(0, 3).forEach((driver) => {
          const driverName = driver.member || driver.dimension_value || driver.name || 'Unknown';
          const contributionPct = driver.contribution_current || driver.contribution_pct || 0;
          const direction = driver.shift > 0 ? 'increase' : driver.shift < 0 ? 'decrease' : 'neutral';

          insights.push({
            insight_type: 'driver',
            triggered: true,
            title: `Driver: ${driverName}`,
            description: `Contribution: ${contributionPct.toFixed(1)}%`,
            confidence: contributionPct / 100,
            metadata: {
              dimension: driver.dimension,
              impact: driver.impact || driver.shift || 0,
              direction,
              value_current: driver.value_current,
              value_baseline: driver.value_baseline,
            },
          });
        });
      }
    }
    return insights;
  };

  const getTrendData = (results) => {
    if (!results?.charts) return null;
    const lineChart = results.charts.find((c) => c.data);
    if (lineChart) {
      return {
        metric_name: results.metric || 'Metric',
        time_series: lineChart.data,
        trend_direction: results.evidence?.detection?.change_direction || 'stable',
        percent_change: results.evidence?.detection?.percent_change || 0,
      };
    }
    return null;
  };

  const getDriverData = (results) => {
    if (!results?.evidence?.drivers?.length) return null;
    return {
      drivers: results.evidence.drivers.map((d, index) => ({
        driver_name: d.member || d.dimension_value || d.name || `Driver ${index + 1}`,
        impact_score: d.contribution_current || d.contribution_pct || d.impact_score || 0,
        direction: d.shift > 0 ? 'positive' : d.shift < 0 ? 'negative' : 'neutral',
        isPrimary: index === 0,
      })),
      primary_driver: results.evidence.drivers[0]?.member || results.evidence.drivers[0]?.name,
    };
  };

  // Detail View
  if (selectedAlert) {
    const results = selectedAlert.results;
    const insights = getInsights(results);
    const trendData = getTrendData(results);
    const driverData = getDriverData(results);

    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <button
          onClick={handleBack}
          className="mb-6 inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
        >
          <svg className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Alerts
        </button>

        {/* Feed Info */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">{selectedAlert.feed_name}</h1>
          <p className="mt-1 text-sm text-gray-500">{selectedAlert.user_query}</p>
        </div>

        <div className="space-y-6">
          {/* Alert Banner */}
          <AlertBanner
            triggered={results.triggered}
            triggerReason={results.trigger_reason}
            alertConfig={results.evidence?.alert}
            metric={results.metric}
            confidence={results.confidence}
          />

          {/* What & Why Cards */}
          {results.triggered && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="card border-l-4 border-l-primary-500">
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  What Happened
                </h3>
                <p className="text-gray-700 leading-relaxed">{results.what_happened}</p>
              </div>

              <div className="card border-l-4 border-l-warning-500">
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-warning-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  Why It Happened
                </h3>
                <p className="text-gray-700 leading-relaxed">{results.why_happened}</p>
              </div>
            </div>
          )}

          {/* Insights Grid */}
          {insights.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Insights</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {insights.map((insight, index) => (
                  <InsightCard key={index} insight={insight} />
                ))}
              </div>
            </div>
          )}

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {trendData && (
              <div className="lg:col-span-2">
                <TrendChart data={trendData} />
              </div>
            )}
            {driverData && (
              <div className="lg:col-span-2">
                <DriverImpactChart data={driverData} />
              </div>
            )}
          </div>

          {/* SQL Queries - Collapsible */}
          {results.evidence?.llm_generated_sql && (
            <div className="card overflow-hidden">
              <button
                onClick={() => setSqlExpanded(!sqlExpanded)}
                className="w-full flex items-center justify-between text-left px-0 py-0"
              >
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <svg className="h-5 w-5 mr-2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                  LLM-Generated SQL
                </h3>
                <svg className={`h-5 w-5 text-gray-500 transition-transform ${sqlExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {sqlExpanded && (
                <div className="mt-4 space-y-4">
                  {Object.entries(results.evidence.llm_generated_sql).map(([key, sql]) =>
                    sql && (
                      <div key={key} className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2 capitalize">
                          {key.replace(/_/g, ' ')}
                        </h4>
                        <pre className="text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap font-mono bg-gray-100 p-3 rounded">
                          {sql}
                        </pre>
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Load run history for a feed
  const handleLoadRuns = async (feedId, e) => {
    e.stopPropagation();
    
    if (expandedRuns[feedId]) {
      setExpandedRuns(prev => ({ ...prev, [feedId]: false }));
      return;
    }
    
    setLoadingRuns(prev => ({ ...prev, [feedId]: true }));
    try {
      if (onFetchFeedRuns) {
        const runs = await onFetchFeedRuns(feedId);
        setFeedRuns(prev => ({ ...prev, [feedId]: runs }));
      }
      setExpandedRuns(prev => ({ ...prev, [feedId]: true }));
    } catch (error) {
      console.error('Error loading runs:', error);
    } finally {
      setLoadingRuns(prev => ({ ...prev, [feedId]: false }));
    }
  };

  // List View
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Intelligent Feed</h1>
        <p className="mt-1 text-sm text-gray-500">
          Triggered alerts from your configured feeds
        </p>
      </div>

      {/* Alerts List */}
      {triggeredAlerts.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">All Clear!</h3>
          <p className="mt-2 text-sm text-gray-500">
            No alerts have been triggered. Your metrics are within normal range.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {triggeredAlerts.map((alert) => (
            <div
              key={alert.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            >
              {/* Main Alert Card */}
              <div
                onClick={() => handleAlertClick(alert)}
                className="p-6 cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    {/* Alert Icon */}
                    <div className={`flex-shrink-0 p-3 rounded-lg ${
                      alert.severity === 'critical' ? 'bg-error-100' :
                      alert.severity === 'high' ? 'bg-warning-100' :
                      'bg-primary-100'
                    }`}>
                      <svg className={`h-6 w-6 ${
                        alert.severity === 'critical' ? 'text-error-600' :
                        alert.severity === 'high' ? 'text-warning-600' :
                        'text-primary-600'
                      }`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>

                    {/* Alert Content */}
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-semibold text-gray-900">{alert.feed_name}</h3>
                        <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                          alert.severity === 'critical' ? 'bg-error-100 text-error-800' :
                          alert.severity === 'high' ? 'bg-warning-100 text-warning-800' :
                          'bg-primary-100 text-primary-800'
                        }`}>
                          {alert.severity?.toUpperCase() || 'MEDIUM'}
                        </span>
                        <span className="text-xs text-gray-400">Latest Run</span>
                      </div>
                      <p className="mt-1 text-sm text-gray-600">{alert.trigger_reason}</p>
                      <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                        <span>Metric: {alert.metric}</span>
                        <span>•</span>
                        <span>Confidence: {alert.confidence?.toFixed(1)}%</span>
                        <span>•</span>
                        <span>{new Date(alert.triggered_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  {/* Arrow */}
                  <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>

              {/* Load More Button & Run History */}
              <div className="border-t border-gray-100 px-6 py-3 bg-gray-50">
                <button
                  onClick={(e) => handleLoadRuns(alert.feed_id, e)}
                  className="text-sm text-primary-600 hover:text-primary-800 font-medium flex items-center"
                >
                  {loadingRuns[alert.feed_id] ? (
                    <>
                      <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Loading...
                    </>
                  ) : (
                    <>
                      <svg className={`h-4 w-4 mr-2 transition-transform ${expandedRuns[alert.feed_id] ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                      {expandedRuns[alert.feed_id] ? 'Hide Run History' : 'Show Run History'}
                    </>
                  )}
                </button>

                {/* Run History List */}
                {expandedRuns[alert.feed_id] && feedRuns[alert.feed_id] && (
                  <div className="mt-3 space-y-2">
                    {feedRuns[alert.feed_id].length === 0 ? (
                      <p className="text-sm text-gray-500">No previous runs</p>
                    ) : (
                      feedRuns[alert.feed_id].map((run) => (
                        <div key={run.id} className="flex items-center justify-between text-sm py-2 border-b border-gray-100 last:border-0">
                          <div className="flex items-center space-x-3">
                            <span className={`inline-flex h-2 w-2 rounded-full ${run.triggered ? 'bg-warning-500' : run.error ? 'bg-error-500' : 'bg-success-500'}`} />
                            <span className="text-gray-600">
                              {new Date(run.run_at).toLocaleString()}
                            </span>
                          </div>
                          <span className={`text-xs ${run.triggered ? 'text-warning-600' : run.error ? 'text-error-600' : 'text-success-600'}`}>
                            {run.triggered ? 'Triggered' : run.error ? 'Error' : 'No Alert'}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default IntelligentFeedPage;

