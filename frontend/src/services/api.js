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

// ==================== Feed Management APIs ====================

/**
 * Get all feeds
 * @returns {Promise} List of feeds
 */
export const getFeeds = async () => {
  const response = await apiClient.get("/feeds");
  return response.data;
};

/**
 * Create a new feed
 * @param {Object} data - Feed data
 * @returns {Promise} Created feed
 */
export const createFeed = async (data) => {
  const response = await apiClient.post("/feeds", data);
  return response.data;
};

/**
 * Update a feed
 * @param {string} feedId - Feed ID
 * @param {Object} data - Updated feed data
 * @returns {Promise} Updated feed
 */
export const updateFeed = async (feedId, data) => {
  const response = await apiClient.put(`/feeds/${feedId}`, data);
  return response.data;
};

/**
 * Delete a feed
 * @param {string} feedId - Feed ID
 * @returns {Promise} Deletion confirmation
 */
export const deleteFeed = async (feedId) => {
  const response = await apiClient.delete(`/feeds/${feedId}`);
  return response.data;
};

/**
 * Get feed run history
 * @param {string} feedId - Feed ID
 * @param {number} limit - Number of runs to fetch
 * @returns {Promise} List of run history entries
 */
export const getFeedRuns = async (feedId, limit = 10) => {
  const response = await apiClient.get(`/feeds/${feedId}/runs`, {
    params: { limit },
  });
  return response.data;
};

/**
 * Validate a query
 * @param {string} query - User query to validate
 * @param {string} bvName - Business view name
 * @returns {Promise} Validation result
 */
export const validateQuery = async (query, bvName) => {
  const response = await apiClient.post("/feeds/validate", {
    query,
    bv_name: bvName,
  });
  return response.data;
};

/**
 * Get triggered alerts
 * @returns {Promise} List of triggered alerts
 */
export const getTriggeredAlerts = async () => {
  const response = await apiClient.get("/alerts/triggered");
  return response.data;
};

// ==================== Business View APIs ====================

/**
 * Get all business views
 * @returns {Promise} List of business views
 */
export const getBusinessViews = async () => {
  const response = await apiClient.get("/business-views");
  return response.data;
};

/**
 * Refresh a business view (analyze all feeds)
 * @param {string} bvName - Business view name
 * @returns {Promise} Refresh results with any triggered alerts
 */
export const refreshBusinessView = async (bvName) => {
  const response = await apiClient.post(`/business-views/${bvName}/refresh`);
  return response.data;
};

/**
 * Get data from a business view's tables
 * @param {string} bvName - Business view name
 * @param {number} limit - Number of rows to fetch per table
 * @returns {Promise} Business view data with tables, measures, dimensions
 */
export const getBusinessViewData = async (bvName, limit = 100) => {
  const response = await apiClient.get(`/business-views/${bvName}/data`, {
    params: { limit },
  });
  return response.data;
};

export default apiClient;
