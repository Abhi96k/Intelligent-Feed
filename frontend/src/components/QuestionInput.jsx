import { useState } from "react";

/**
 * QuestionInput Component
 * Input field for user questions with Run and Clear buttons
 *
 * @param {Object} props
 * @param {Function} props.onAnalyze - Callback when Run is clicked
 * @param {Function} props.onClear - Callback when Clear is clicked
 * @param {boolean} props.isLoading - Loading state
 * @param {boolean} props.hasResults - Whether results are displayed
 */
function QuestionInput({ onAnalyze, onClear, isLoading, hasResults }) {
  const [question, setQuestion] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onAnalyze(question.trim());
    }
  };

  const handleClear = () => {
    setQuestion("");
    onClear();
  };

  return (
    <div className="card">
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <div>
            <label
              htmlFor="question"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Ask a Question
            </label>
            <textarea
              id="question"
              rows={3}
              className="input-field resize-none"
              placeholder="e.g., Why did revenue drop in Q3? What are the top drivers of customer churn?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {question.length > 0 && <span>{question.length} characters</span>}
            </div>
            <div className="flex gap-3">
              {hasResults && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="btn-secondary"
                  disabled={isLoading}
                >
                  Clear
                </button>
              )}
              <button
                type="submit"
                className="btn-primary"
                disabled={!question.trim() || isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center">
                    <svg
                      className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Analyzing...
                  </span>
                ) : (
                  <span className="flex items-center">
                    <svg
                      className="w-4 h-4 mr-2"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    Run Analysis
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Example Questions */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-xs font-medium text-gray-700 mb-2">
          Example Questions:
        </p>
        <div className="flex flex-wrap gap-2">
          {[
            "Why did revenue drop in Q3 2024 vs previous period?",
            "Show me anomalies in revenue for Q4 2024",
            "What caused the profit spike in Enterprise segment in November 2024?",
            "Why did Order_Count decrease in APAC region last month?",
          ].map((example, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setQuestion(example)}
              className="text-xs px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors disabled:opacity-50"
              disabled={isLoading}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default QuestionInput;
