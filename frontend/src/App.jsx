import { useState } from "react";
import QuestionInput from "./components/QuestionInput";
import InsightCard from "./components/InsightCard";
import TrendChart from "./components/TrendChart";
import DriverImpactChart from "./components/DriverImpactChart";
import AlertBanner from "./components/AlertBanner";
import { useMutation } from "@tanstack/react-query";
import { analyzeQuestion } from "./services/api";

/**
 * Main App Component
 * Intelligent Feed Analytics Dashboard
 */
function App() {
  const [results, setResults] = useState(null);

  // Mutation for analyzing questions
  const analyzeMutation = useMutation({
    mutationFn: analyzeQuestion,
    onSuccess: (data) => {
      setResults(data);
    },
    onError: (error) => {
      console.error("Analysis failed:", error);
    },
  });

  const handleAnalyze = (question) => {
    analyzeMutation.mutate({ question });
  };

  const handleClear = () => {
    setResults(null);
    analyzeMutation.reset();
  };

  // Check if insight was triggered (alert condition met)
  const isTriggered = results?.triggered === true;

  // Extract chart data from results
  const getChartData = () => {
    if (!results?.charts || results.charts.length === 0) return null;

    // Find trend chart
    const trendChart = results.charts.find(
      (c) =>
        c.chart_type === "line" ||
        c.chart_type === "timeseries" ||
        c.chart_type === "trend"
    );

    // Find driver chart
    const driverChart = results.charts.find(
      (c) =>
        c.chart_type === "bar" ||
        c.chart_type === "driver" ||
        c.chart_type === "waterfall"
    );

    return { trendChart, driverChart };
  };

  // Convert backend response to frontend insight format
  const getInsights = () => {
    if (!results) return [];

    const insights = [];

    if (results.triggered) {
      // Main triggered insight
      insights.push({
        insight_type: results.evidence?.alert?.alert_type || "trend",
        triggered: true,
        title: results.trigger_reason || "Insight Triggered",
        description: results.what_happened || "",
        confidence: results.confidence / 100,
        metadata: {
          metric: results.metric,
          time_range: `${results.time_range?.start} to ${results.time_range?.end}`,
          ...results.evidence?.detection,
        },
      });

      // Add driver insights if available
      if (results.evidence?.drivers && results.evidence.drivers.length > 0) {
        const topDrivers = results.evidence.drivers.slice(0, 3);
        topDrivers.forEach((driver) => {
          // Backend returns: dimension, member, impact, contribution_current, contribution_baseline, shift, value_current, value_baseline
          const driverName =
            driver.member || driver.dimension_value || driver.name || "Unknown";
          const contributionPct =
            driver.contribution_current || driver.contribution_pct || 0;
          const impactValue =
            driver.impact || driver.impact_score || driver.shift || 0;
          const direction =
            driver.shift > 0
              ? "increase"
              : driver.shift < 0
              ? "decrease"
              : "neutral";

          insights.push({
            insight_type: "driver",
            triggered: true,
            title: `Driver: ${driverName}`,
            description: `Contribution: ${contributionPct.toFixed(1)}%`,
            confidence: contributionPct / 100,
            metadata: {
              dimension: driver.dimension,
              impact: impactValue,
              direction: direction,
              value_current: driver.value_current,
              value_baseline: driver.value_baseline,
            },
          });
        });
      }
    } else {
      // Not triggered insight
      insights.push({
        insight_type: "info",
        triggered: false,
        title: "No Alert Triggered",
        description:
          results.explanation || "The metric is within normal range.",
        confidence: 0,
        metadata: {
          metric: results.metric,
          suggestion: results.suggestion,
          ...results.metrics,
        },
      });
    }

    return insights;
  };

  // Get trend data for chart
  const getTrendData = () => {
    const chartData = getChartData();
    if (!chartData?.trendChart) {
      // Try to construct from evidence
      if (results?.charts) {
        const lineChart = results.charts.find((c) => c.data);
        if (lineChart) {
          return {
            metric_name: results.metric || "Metric",
            time_series: lineChart.data,
            trend_direction:
              results.evidence?.detection?.change_direction || "stable",
            percent_change: results.evidence?.detection?.percent_change || 0,
          };
        }
      }
      return null;
    }

    return {
      metric_name: results.metric || chartData.trendChart.title || "Metric",
      time_series: chartData.trendChart.data || [],
      trend_direction:
        results.evidence?.detection?.change_direction || "stable",
      percent_change: results.evidence?.detection?.percent_change || 0,
    };
  };

  // Get driver data for chart
  const getDriverData = () => {
    if (!results?.evidence?.drivers || results.evidence.drivers.length === 0)
      return null;

    return {
      drivers: results.evidence.drivers.map((d, index) => ({
        // Backend returns: dimension, member, impact, contribution_current, shift, value_current, value_baseline
        driver_name:
          d.member || d.dimension_value || d.name || `Driver ${index + 1}`,
        impact_score:
          d.contribution_current || d.contribution_pct || d.impact_score || 0,
        direction:
          d.shift > 0 ? "positive" : d.shift < 0 ? "negative" : "neutral",
        isPrimary: index === 0,
      })),
      primary_driver:
        results.evidence.drivers[0]?.member ||
        results.evidence.drivers[0]?.dimension_value ||
        results.evidence.drivers[0]?.name,
    };
  };

  const insights = getInsights();
  const trendData = getTrendData();
  const driverData = getDriverData();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Intelligent Feed
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                AI-powered analytics insights with LLM-generated SQL queries
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-700">
                <span className="w-2 h-2 bg-primary-500 rounded-full mr-2 animate-pulse"></span>
                Ready
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Question Input Section */}
        <div className="mb-8">
          <QuestionInput
            onAnalyze={handleAnalyze}
            onClear={handleClear}
            isLoading={analyzeMutation.isPending}
            hasResults={!!results}
          />

          {analyzeMutation.isError && (
            <div className="mt-4 p-4 bg-error-50 border border-error-200 rounded-lg">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-error-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-error-800">
                    Analysis Error
                  </h3>
                  <div className="mt-2 text-sm text-error-700">
                    <p>
                      {analyzeMutation.error?.response?.data?.error ||
                        analyzeMutation.error?.message ||
                        "Failed to analyze question. Please try again."}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Results Section */}
        {results && (
          <div className="space-y-6">
            {/* Alert Banner - Shows when insight is triggered */}
            <AlertBanner
              triggered={isTriggered}
              triggerReason={results.trigger_reason}
              alertConfig={results.evidence?.alert}
              metric={results.metric}
              confidence={results.confidence}
            />

            {/* What Happened & Why Happened Cards */}
            {isTriggered && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* What Happened */}
                <div className="card border-l-4 border-l-primary-500">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                    <svg
                      className="w-5 h-5 mr-2 text-primary-600"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    What Happened
                  </h3>
                  <p className="text-gray-700 leading-relaxed">
                    {results.what_happened}
                  </p>
                </div>

                {/* Why Happened */}
                <div className="card border-l-4 border-l-warning-500">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                    <svg
                      className="w-5 h-5 mr-2 text-warning-600"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                      />
                    </svg>
                    Why It Happened
                  </h3>
                  <p className="text-gray-700 leading-relaxed">
                    {results.why_happened}
                  </p>
                </div>
              </div>
            )}

            {/* Not Triggered - Suggestion Card */}
            {!isTriggered && results.suggestion && (
              <div className="card border-l-4 border-l-gray-400 bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <svg
                    className="w-5 h-5 mr-2 text-gray-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                    />
                  </svg>
                  Suggestion
                </h3>
                <p className="text-gray-700 leading-relaxed">
                  {results.suggestion}
                </p>
              </div>
            )}

            {/* Insights Grid */}
            {insights.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Insights
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {insights.map((insight, index) => (
                    <InsightCard key={index} insight={insight} />
                  ))}
                </div>
              </div>
            )}

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Primary Trend Chart */}
              {trendData && (
                <div className="lg:col-span-2">
                  <TrendChart data={trendData} />
                </div>
              )}

              {/* Driver Impact Chart */}
              {driverData && (
                <div className="lg:col-span-2">
                  <DriverImpactChart data={driverData} />
                </div>
              )}
            </div>

            {/* Evidence Section - LLM Generated SQL */}
            {isTriggered && results.evidence?.llm_generated_sql && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <svg
                    className="w-5 h-5 mr-2 text-gray-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                    />
                  </svg>
                  LLM-Generated SQL Queries
                </h3>
                <div className="space-y-4">
                  {Object.entries(results.evidence.llm_generated_sql).map(
                    ([key, sql]) =>
                      sql && (
                        <div key={key} className="bg-gray-50 rounded-lg p-4">
                          <h4 className="text-sm font-medium text-gray-700 mb-2 capitalize">
                            {key.replace(/_/g, " ")}
                          </h4>
                          <pre className="text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap font-mono bg-gray-100 p-3 rounded">
                            {sql}
                          </pre>
                        </div>
                      )
                  )}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="card bg-gray-50">
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Analysis Metadata
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Metric</span>
                  <p className="font-medium text-gray-900 mt-1">
                    {results.metric}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Time Range</span>
                  <p className="font-medium text-gray-900 mt-1">
                    {results.time_range?.start} → {results.time_range?.end}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Status</span>
                  <p
                    className={`font-medium mt-1 ${
                      isTriggered ? "text-error-600" : "text-success-600"
                    }`}
                  >
                    {isTriggered ? "Alert Triggered" : "Normal"}
                  </p>
                </div>
                {results.confidence !== undefined && (
                  <div>
                    <span className="text-gray-500">Confidence</span>
                    <p className="font-medium text-gray-900 mt-1">
                      {results.confidence.toFixed(1)}%
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!results && !analyzeMutation.isPending && (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              No analysis yet
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Enter a question above to get started with intelligent insights.
            </p>
            <p className="mt-2 text-xs text-gray-400">
              Try: "Why did revenue drop in Q3 2024?" or "Show me anomalies in
              sales for last quarter"
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Powered by Intelligent Feed Analytics Engine with LLM-Generated SQL
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
