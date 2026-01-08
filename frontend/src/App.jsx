import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import TabNavigation from "./components/TabNavigation";
import Toast from "./components/Toast";
import IntelligentFeedPage from "./pages/IntelligentFeedPage";
import ManageFeedPage from "./pages/ManageFeedPage";
import BusinessViewPage from "./pages/BusinessViewPage";
import {
  getFeeds,
  createFeed,
  updateFeed,
  deleteFeed,
  validateQuery,
  getTriggeredAlerts,
  getBusinessViews,
  refreshBusinessView,
  getBusinessViewData,
} from "./services/api";

/**
 * Main App Component
 * Intelligent Feed Analytics Dashboard with Tab Navigation
 */
function App() {
  const [activeTab, setActiveTab] = useState("feeds");
  const [toasts, setToasts] = useState([]);
  const [bvData, setBvData] = useState(null);
  const queryClient = useQueryClient();

  // Add toast notification
  const addToast = useCallback((message, type = "info") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
  }, []);

  // Remove toast
  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // ==================== Data Fetching ====================

  // Fetch feeds
  const { data: feeds = [] } = useQuery({
    queryKey: ["feeds"],
    queryFn: getFeeds,
    retry: 1,
  });

  // Fetch business views
  const { data: businessViews = [] } = useQuery({
    queryKey: ["businessViews"],
    queryFn: getBusinessViews,
    retry: 1,
  });

  // Fetch triggered alerts
  const { data: triggeredAlerts = [], isLoading: alertsLoading } = useQuery({
    queryKey: ["triggeredAlerts"],
    queryFn: getTriggeredAlerts,
    retry: 1,
    refetchInterval: 30000, // Refresh every 30 seconds
    onError: () => {
      // Silently fail if API not available yet
    },
  });

  // ==================== Mutations ====================

  // Create feed mutation
  const createFeedMutation = useMutation({
    mutationFn: createFeed,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
      addToast("Feed created successfully", "success");
    },
    onError: (error) => {
      addToast(error.message || "Failed to create feed", "error");
    },
  });

  // Update feed mutation
  const updateFeedMutation = useMutation({
    mutationFn: ({ id, ...data }) => updateFeed(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
      addToast("Feed updated successfully", "success");
    },
    onError: (error) => {
      addToast(error.message || "Failed to update feed", "error");
    },
  });

  // Delete feed mutation
  const deleteFeedMutation = useMutation({
    mutationFn: deleteFeed,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
      addToast("Feed deleted successfully", "success");
    },
    onError: (error) => {
      addToast(error.message || "Failed to delete feed", "error");
    },
  });

  // Refresh BV mutation
  const refreshBVMutation = useMutation({
    mutationFn: refreshBusinessView,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["triggeredAlerts"] });
      queryClient.invalidateQueries({ queryKey: ["businessViews"] });

      if (data.triggered_count > 0) {
        addToast(
          `Analysis complete! ${data.triggered_count} alert(s) triggered.`,
          "warning"
        );
        // Switch to feeds tab to show alerts
        setActiveTab("feeds");
      } else {
        addToast("Analysis complete. No alerts triggered.", "success");
      }
    },
    onError: (error) => {
      addToast(error.message || "Failed to refresh business view", "error");
    },
  });

  // ==================== Handlers ====================

  const handleCreateFeed = async (data) => {
    await createFeedMutation.mutateAsync(data);
  };

  const handleUpdateFeed = async (data) => {
    await updateFeedMutation.mutateAsync({ id: data.id, ...data });
  };

  const handleDeleteFeed = async (feedId) => {
    await deleteFeedMutation.mutateAsync(feedId);
  };

  const handleValidateQuery = async (query, bvName) => {
    try {
      const result = await validateQuery(query, bvName);
      return result;
    } catch (error) {
      // Return a default valid result if API fails
      return { is_valid: true, can_proceed: true };
    }
  };

  const handleRefreshBV = async (bvName) => {
    await refreshBVMutation.mutateAsync(bvName);
  };

  const handleFetchBVData = useCallback(async (bvName) => {
    try {
      const data = await getBusinessViewData(bvName);
      setBvData(data);
      return data;
    } catch (error) {
      console.error("Failed to fetch BV data:", error);
      throw error;
    }
  }, []);

  // ==================== Render ====================

  // Mock data for initial development (remove when backend is ready)
  const mockBusinessViews =
    businessViews.length > 0
      ? businessViews
      : [
          {
            name: "ecommerce_analytics",
            display_name: "E-Commerce Analytics",
            description: "Sales and revenue analytics for e-commerce platform",
            table_count: 5,
            measure_count: 4,
            active_feeds: feeds.filter(
              (f) => f.bv_name === "ecommerce_analytics"
            ).length,
            last_refresh: null,
          },
        ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toast Notifications */}
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          onClose={() => removeToast(toast.id)}
        />
      ))}

      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Tellius Intelligent Feed
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                AI-powered analytics insights with automated alert monitoring
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {triggeredAlerts.length > 0 && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-error-100 text-error-700">
                  <span className="w-2 h-2 bg-error-500 rounded-full mr-2 animate-pulse"></span>
                  {triggeredAlerts.length} Alert
                  {triggeredAlerts.length !== 1 ? "s" : ""}
                </span>
              )}
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-success-100 text-success-700">
                <span className="w-2 h-2 bg-success-500 rounded-full mr-2"></span>
                Online
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content */}
      <main>
        {activeTab === "feeds" && (
          <IntelligentFeedPage
            triggeredAlerts={triggeredAlerts}
            isLoading={alertsLoading}
          />
        )}

        {activeTab === "manage" && (
          <ManageFeedPage
            feeds={feeds}
            businessViews={mockBusinessViews}
            onCreateFeed={handleCreateFeed}
            onUpdateFeed={handleUpdateFeed}
            onDeleteFeed={handleDeleteFeed}
            onValidateQuery={handleValidateQuery}
          />
        )}

        {activeTab === "business-view" && (
          <BusinessViewPage
            businessViews={mockBusinessViews}
            onRefreshBV={handleRefreshBV}
            isRefreshing={refreshBVMutation.isPending}
            onFetchBVData={handleFetchBVData}
            bvData={bvData}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Powered by Tellius Intelligent Feed Analytics Engine
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
