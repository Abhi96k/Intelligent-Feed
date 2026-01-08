import axios from "axios";

/**
 * API Client for Intelligent Feed Backend
 * Base URL is configured through Vite proxy: /api -> http://localhost:8000
 */

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(
      `[API Request] ${config.method?.toUpperCase()} ${config.url}`,
      config.data
    );
    return config;
  },
  (error) => {
    console.error("[API Request Error]", error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    console.error(
      "[API Response Error]",
      error.response?.data || error.message
    );

    // Enhanced error handling
    if (error.response) {
      // Server responded with error status
      const errorMessage =
        error.response.data?.error ||
        error.response.data?.message ||
        "Server error occurred";
      error.message = errorMessage;
    } else if (error.request) {
      // Request made but no response
      error.message =
        "No response from server. Please check if the backend is running.";
    } else {
      // Something else happened
      error.message = error.message || "An unexpected error occurred";
    }

    return Promise.reject(error);
  }
);

/**
 * Analyze a question and get insights
 * @param {Object} data - Request data
 * @param {string} data.question - User question
 * @returns {Promise} Response with insights, trends, and driver analysis
 */
export const analyzeQuestion = async (data) => {
  // Backend expects { user_question: "..." }
  const payload = {
    user_question: data.question || data.user_question,
  };
  const response = await apiClient.post("/insight", payload);
  return response.data;
};

/**
 * Get health status of the backend
 * @returns {Promise} Health check response
 */
export const getHealthStatus = async () => {
  const response = await apiClient.get("/health");
  return response.data;
};

/**
 * Get system configuration
 * @returns {Promise} Configuration data
 */
export const getConfig = async () => {
  const response = await apiClient.get("/config");
  return response.data;
};

/**
 * Get historical analysis results (if available)
 * @param {Object} params - Query parameters
 * @param {number} params.limit - Number of results to fetch
 * @param {number} params.offset - Offset for pagination
 * @returns {Promise} Historical analysis data
 */
export const getHistory = async (params = {}) => {
  const response = await apiClient.get("/history", { params });
  return response.data;
};

/**
 * Submit feedback on an insight (if available)
 * @param {Object} data - Feedback data
 * @param {string} data.insight_id - Insight identifier
 * @param {boolean} data.helpful - Whether the insight was helpful
 * @param {string} data.comment - Optional comment
 * @returns {Promise} Feedback submission response
 */
export const submitFeedback = async (data) => {
  const response = await apiClient.post("/feedback", data);
  return response.data;
};

export default apiClient;
