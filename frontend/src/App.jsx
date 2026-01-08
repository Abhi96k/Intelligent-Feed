import { useState } from 'react'
import QuestionInput from './components/QuestionInput'
import InsightCard from './components/InsightCard'
import TrendChart from './components/TrendChart'
import DriverImpactChart from './components/DriverImpactChart'
import { useMutation } from '@tanstack/react-query'
import { analyzeQuestion } from './services/api'

/**
 * Main App Component
 * Intelligent Feed Analytics Dashboard
 */
function App() {
  const [results, setResults] = useState(null)

  // Mutation for analyzing questions
  const analyzeMutation = useMutation({
    mutationFn: analyzeQuestion,
    onSuccess: (data) => {
      setResults(data)
    },
    onError: (error) => {
      console.error('Analysis failed:', error)
    }
  })

  const handleAnalyze = (question) => {
    analyzeMutation.mutate({ question })
  }

  const handleClear = () => {
    setResults(null)
    analyzeMutation.reset()
  }

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
                AI-powered analytics insights and trend analysis
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
                  <svg className="h-5 w-5 text-error-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
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
                       'Failed to analyze question. Please try again.'}
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
            {/* Question Echo */}
            <div className="card bg-primary-50 border-primary-200">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3 flex-1">
                  <h3 className="text-sm font-medium text-primary-900">Question</h3>
                  <p className="mt-1 text-sm text-primary-700">{results.question}</p>
                </div>
              </div>
            </div>

            {/* Insights Grid */}
            {results.insights && results.insights.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Insights
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {results.insights.map((insight, index) => (
                    <InsightCard key={index} insight={insight} />
                  ))}
                </div>
              </div>
            )}

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Primary Trend Chart */}
              {results.primary_trend && (
                <div className="lg:col-span-2">
                  <TrendChart data={results.primary_trend} />
                </div>
              )}

              {/* Driver Impact Chart */}
              {results.driver_impact && (
                <div className="lg:col-span-2">
                  <DriverImpactChart data={results.driver_impact} />
                </div>
              )}
            </div>

            {/* Summary Section */}
            {results.summary && (
              <div className="card">
                <h3 className="card-header">Summary</h3>
                <p className="text-gray-700 leading-relaxed">{results.summary}</p>
              </div>
            )}

            {/* Metadata */}
            {results.metadata && (
              <div className="card bg-gray-50">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Analysis Metadata</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  {results.metadata.analysis_timestamp && (
                    <div>
                      <span className="text-gray-500">Timestamp</span>
                      <p className="font-medium text-gray-900 mt-1">
                        {new Date(results.metadata.analysis_timestamp).toLocaleString()}
                      </p>
                    </div>
                  )}
                  {results.metadata.total_insights !== undefined && (
                    <div>
                      <span className="text-gray-500">Total Insights</span>
                      <p className="font-medium text-gray-900 mt-1">
                        {results.metadata.total_insights}
                      </p>
                    </div>
                  )}
                  {results.metadata.triggered_insights !== undefined && (
                    <div>
                      <span className="text-gray-500">Triggered</span>
                      <p className="font-medium text-gray-900 mt-1">
                        {results.metadata.triggered_insights}
                      </p>
                    </div>
                  )}
                  {results.metadata.confidence_score !== undefined && (
                    <div>
                      <span className="text-gray-500">Confidence</span>
                      <p className="font-medium text-gray-900 mt-1">
                        {(results.metadata.confidence_score * 100).toFixed(0)}%
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
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
            <h3 className="mt-2 text-sm font-medium text-gray-900">No analysis yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Enter a question above to get started with intelligent insights.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Powered by Intelligent Feed Analytics Engine
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
