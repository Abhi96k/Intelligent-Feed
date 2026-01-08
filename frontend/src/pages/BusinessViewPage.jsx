import { useState, useEffect } from "react";
import SchemaVisualization from "../components/SchemaVisualization";

/**
 * BusinessViewPage Component
 * Page for viewing business views with sidebar and tabular data display
 */
function BusinessViewPage({
  businessViews,
  onRefreshBV,
  isRefreshing,
  onFetchBVData,
  bvData,
}) {
  const [selectedBV, setSelectedBV] = useState(null);
  const [selectedTable, setSelectedTable] = useState(null);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [viewMode, setViewMode] = useState("table"); // "table" or "schema"
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  // Select first BV by default
  useEffect(() => {
    if (businessViews.length > 0 && !selectedBV) {
      setSelectedBV(businessViews[0].name);
    }
  }, [businessViews, selectedBV]);

  // Load BV data when selected
  useEffect(() => {
    if (selectedBV && onFetchBVData) {
      setIsLoadingData(true);
      onFetchBVData(selectedBV).finally(() => setIsLoadingData(false));
    }
  }, [selectedBV, onFetchBVData]);

  // Select first table when data loads or when BV changes
  useEffect(() => {
    if (bvData?.tables) {
      const tableNames = Object.keys(bvData.tables);
      // If no table selected OR selected table is not in current BV, select first
      if (tableNames.length > 0 && (!selectedTable || !tableNames.includes(selectedTable))) {
        setSelectedTable(tableNames[0]);
      }
    }
  }, [bvData, selectedTable]);

  // Reset page when table changes
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedTable]);

  const handleRefresh = async () => {
    if (selectedBV) {
      await onRefreshBV(selectedBV);
    }
  };

  const currentTableData = bvData?.tables?.[selectedTable];
  
  // Pagination calculations
  const totalRows = currentTableData?.data?.length || 0;
  const totalPages = Math.ceil(totalRows / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const paginatedData = currentTableData?.data?.slice(startIndex, endIndex) || [];

  return (
    <div className="flex min-h-[600px]">
      {/* Sidebar - BV List */}
      <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">
            Business Views
          </h2>
        </div>
        <nav className="p-2">
          {businessViews.map((bv) => (
            <button
              key={bv.name}
              onClick={() => {
                setSelectedBV(bv.name);
                setSelectedTable(null);
              }}
              className={`w-full text-left px-3 py-2.5 rounded-lg mb-1 flex items-center transition-colors ${
                selectedBV === bv.name
                  ? "bg-primary-50 text-primary-700 border border-primary-200"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              <svg
                className={`h-5 w-5 mr-3 ${
                  selectedBV === bv.name ? "text-primary-500" : "text-gray-400"
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                />
              </svg>
              <div>
                <div className="font-medium text-sm">
                  {bv.display_name || bv.name}
                </div>
                <div className="text-xs text-gray-500">
                  {bv.table_count || 0} tables
                </div>
              </div>
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {selectedBV ? (
          <>
            {/* Header with View Toggle and Refresh Button */}
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  {businessViews.find((bv) => bv.name === selectedBV)
                    ?.display_name || selectedBV}
                </h1>
                <p className="text-sm text-gray-500">
                  {businessViews.find((bv) => bv.name === selectedBV)
                    ?.description || "View and analyze data"}
                </p>
              </div>
              <div className="flex items-center space-x-4">
                {/* View Mode Toggle */}
                <div className="flex bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setViewMode("table")}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md flex items-center transition-colors ${
                      viewMode === "table"
                        ? "bg-white text-gray-900 shadow-sm"
                        : "text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Table
                  </button>
                  <button
                    onClick={() => setViewMode("schema")}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md flex items-center transition-colors ${
                      viewMode === "schema"
                        ? "bg-white text-gray-900 shadow-sm"
                        : "text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
                    </svg>
                    Schema
                  </button>
                </div>
                
                {/* Refresh Button */}
                <button
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg ${
                    isRefreshing
                      ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                      : "text-white bg-primary-600 hover:bg-primary-700"
                  }`}
                >
                {isRefreshing ? (
                  <>
                    <svg
                      className="animate-spin -ml-0.5 mr-2 h-4 w-4"
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
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Analyzing Feeds...
                  </>
                ) : (
                  <>
                    <svg
                      className="h-4 w-4 mr-2"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                    Refresh & Analyze
                  </>
                )}
                </button>
              </div>
            </div>

            {/* Schema Visualization Mode */}
            {viewMode === "schema" && (
              <div className="p-6">
                <SchemaVisualization bvData={bvData} />
              </div>
            )}

            {/* Table Tabs - Only show in table mode */}
            {viewMode === "table" && bvData?.tables && (
              <div className="bg-gray-50 border-b border-gray-200 px-6">
                <nav className="flex space-x-4 overflow-x-auto py-2">
                  {Object.keys(bvData.tables).map((tableName) => (
                    <button
                      key={tableName}
                      onClick={() => setSelectedTable(tableName)}
                      className={`px-3 py-2 text-sm font-medium rounded-lg whitespace-nowrap ${
                        selectedTable === tableName
                          ? "bg-white text-primary-700 shadow-sm border border-gray-200"
                          : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                      }`}
                    >
                      {tableName}
                      <span className="ml-2 text-xs text-gray-400">
                        ({bvData.tables[tableName]?.total_rows || 0} rows)
                      </span>
                    </button>
                  ))}
                </nav>
              </div>
            )}

            {/* Data Table - Only show in table mode */}
            {viewMode === "table" && (
            <div className="p-6">
              {isLoadingData ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <svg
                      className="animate-spin h-8 w-8 mx-auto text-primary-500 mb-4"
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
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    <p className="text-gray-500">Loading data...</p>
                  </div>
                </div>
              ) : currentTableData?.data ? (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          {currentTableData.columns.map((col) => (
                            <th
                              key={col}
                              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {paginatedData.map((row, rowIdx) => (
                          <tr
                            key={rowIdx}
                            className="hover:bg-gray-50 transition-colors"
                          >
                            {currentTableData.columns.map((col) => (
                              <td
                                key={col}
                                className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap"
                              >
                                {formatCellValue(row[col])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination Controls */}
                  <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 flex items-center justify-between">
                    <div className="text-sm text-gray-500">
                      Showing {startIndex + 1} - {Math.min(endIndex, totalRows)} of {totalRows} rows
                      <span className="text-gray-400 ml-2">
                        (Total in DB: {currentTableData.total_rows})
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setCurrentPage(1)}
                        disabled={currentPage === 1}
                        className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        First
                      </button>
                      <button
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        ←
                      </button>
                      <span className="text-sm text-gray-700">
                        Page {currentPage} of {totalPages}
                      </span>
                      <button
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                        className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        →
                      </button>
                      <button
                        onClick={() => setCurrentPage(totalPages)}
                        disabled={currentPage === totalPages}
                        className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Last
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 bg-white rounded-xl border border-gray-200">
                  <div className="text-center">
                    <svg
                      className="h-12 w-12 text-gray-400 mx-auto mb-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <p className="text-gray-500">Select a table to view data</p>
                  </div>
                </div>
              )}

              {/* Measures & Dimensions Info */}
              {bvData && (
                <div className="mt-6 grid grid-cols-2 gap-6">
                  {/* Measures */}
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                    <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                      <svg
                        className="h-4 w-4 mr-2 text-primary-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                        />
                      </svg>
                      Measures ({bvData.measures?.length || 0})
                    </h3>
                    <div className="space-y-2">
                      {bvData.measures?.map((m) => (
                        <div
                          key={m.name}
                          className="flex items-center justify-between text-sm"
                        >
                          <span className="font-medium text-gray-700">
                            {m.name}
                          </span>
                          <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600">
                            {m.expression}
                          </code>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Dimensions */}
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                    <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                      <svg
                        className="h-4 w-4 mr-2 text-warning-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                        />
                      </svg>
                      Dimensions ({bvData.dimensions?.length || 0})
                    </h3>
                    <div className="space-y-2">
                      {bvData.dimensions?.map((d) => (
                        <div
                          key={d.name}
                          className="flex items-center justify-between text-sm"
                        >
                          <span className="font-medium text-gray-700">
                            {d.name}
                          </span>
                          <span className="text-xs text-gray-500">
                            {d.table}.{d.column}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <svg
                className="h-12 w-12 text-gray-400 mx-auto mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                />
              </svg>
              <h3 className="text-lg font-medium text-gray-900">
                No Business View Selected
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Select a business view from the sidebar to view its data.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper function to format cell values
function formatCellValue(value) {
  if (value === null || value === undefined) {
    return <span className="text-gray-400 italic">null</span>;
  }
  if (typeof value === "number") {
    // Format large numbers
    if (Math.abs(value) >= 1000000) {
      return (value / 1000000).toFixed(2) + "M";
    }
    if (Math.abs(value) >= 1000) {
      return (value / 1000).toFixed(2) + "K";
    }
    if (Number.isInteger(value)) {
      return value.toLocaleString();
    }
    return value.toFixed(2);
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return String(value);
}

export default BusinessViewPage;
