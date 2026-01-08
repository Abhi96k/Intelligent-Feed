import { useCallback, useMemo } from "react";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";

/**
 * Custom Table Node Component
 * Displays a database table with its columns
 */
function TableNode({ data }) {
  return (
    <div className="bg-white rounded-lg shadow-lg border-2 border-gray-200 min-w-[200px] overflow-hidden">
      {/* Table Header */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 px-4 py-2">
        <div className="flex items-center">
          <svg
            className="h-4 w-4 text-white mr-2"
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
          <span className="font-bold text-white text-sm">{data.label}</span>
        </div>
        {data.rowCount && (
          <span className="text-xs text-primary-100">
            {data.rowCount.toLocaleString()} rows
          </span>
        )}
      </div>

      {/* Columns */}
      <div className="divide-y divide-gray-100">
        {data.columns?.map((col, idx) => (
          <div
            key={idx}
            className="px-3 py-1.5 flex items-center justify-between text-xs hover:bg-gray-50"
          >
            <div className="flex items-center">
              {col.isPrimaryKey && (
                <svg
                  className="h-3 w-3 text-warning-500 mr-1"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 8a6 6 0 01-7.743 5.743L10 14l-1 1-1 1H6v2H2v-4l4.257-4.257A6 6 0 1118 8zm-6-4a1 1 0 100 2 2 2 0 012 2 1 1 0 102 0 4 4 0 00-4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
              {col.isForeignKey && (
                <svg
                  className="h-3 w-3 text-primary-500 mr-1"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                  />
                </svg>
              )}
              <span
                className={`font-medium ${
                  col.isPrimaryKey
                    ? "text-warning-700"
                    : col.isForeignKey
                    ? "text-primary-700"
                    : "text-gray-700"
                }`}
              >
                {col.name}
              </span>
            </div>
            <span className="text-gray-400 ml-2">{col.type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Custom node types
const nodeTypes = {
  tableNode: TableNode,
};

/**
 * SchemaVisualization Component
 * Visualizes database schema with tables and relationships using React Flow
 */
function SchemaVisualization({ bvData }) {
  // Generate nodes from BV data
  const initialNodes = useMemo(() => {
    if (!bvData?.tables) return [];

    const tableNames = Object.keys(bvData.tables);
    const nodes = [];

    // Position tables in a grid layout
    const cols = 3;
    const spacing = { x: 300, y: 350 };

    tableNames.forEach((tableName, idx) => {
      const tableData = bvData.tables[tableName];
      const col = idx % cols;
      const row = Math.floor(idx / cols);

      // Determine columns with their types
      const columns = tableData.columns?.map((colName) => {
        const isPrimaryKey = colName.toLowerCase().includes("_id") && colName.toLowerCase() === tableName.replace("_dim", "_id").replace("_fact", "_id");
        const isForeignKey = colName.toLowerCase().endsWith("_id") && !isPrimaryKey;

        return {
          name: colName,
          type: getColumnType(colName, tableData.data?.[0]?.[colName]),
          isPrimaryKey: colName.toLowerCase() === tableName.split("_")[0] + "_id" || 
                        (tableName === "sales_fact" && colName === "sale_id"),
          isForeignKey: isForeignKey,
        };
      }) || [];

      nodes.push({
        id: tableName,
        type: "tableNode",
        position: { x: col * spacing.x + 50, y: row * spacing.y + 50 },
        data: {
          label: tableName,
          rowCount: tableData.total_rows,
          columns: columns,
        },
      });
    });

    return nodes;
  }, [bvData]);

  // Generate edges (relationships) from foreign keys
  const initialEdges = useMemo(() => {
    if (!bvData?.tables) return [];

    const edges = [];
    const tableNames = Object.keys(bvData.tables);

    // Find relationships based on _id columns
    tableNames.forEach((tableName) => {
      const tableData = bvData.tables[tableName];
      
      tableData.columns?.forEach((colName) => {
        // Check if this is a foreign key (ends with _id and matches another table)
        if (colName.toLowerCase().endsWith("_id")) {
          const potentialTable = colName.replace("_id", "_dim");
          
          if (tableNames.includes(potentialTable) && tableName !== potentialTable) {
            edges.push({
              id: `${tableName}-${potentialTable}`,
              source: potentialTable,
              target: tableName,
              sourceHandle: null,
              targetHandle: null,
              type: "smoothstep",
              animated: true,
              style: { stroke: "#6366f1", strokeWidth: 2 },
              markerEnd: {
                type: MarkerType.ArrowClosed,
                color: "#6366f1",
              },
              label: colName,
              labelStyle: { fontSize: 10, fill: "#6b7280" },
              labelBgStyle: { fill: "#f3f4f6", fillOpacity: 0.9 },
            });
          }
        }
      });
    });

    return edges;
  }, [bvData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when data changes
  useMemo(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onConnect = useCallback(() => {}, []);

  if (!bvData?.tables || Object.keys(bvData.tables).length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-xl border border-gray-200">
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
          <p className="text-gray-500">No schema data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[500px] bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={1.5}
        attributionPosition="bottom-left"
      >
        <Controls className="bg-white rounded-lg shadow-md" />
        <MiniMap
          className="bg-white rounded-lg shadow-md"
          nodeColor={(node) => {
            if (node.data.label?.includes("fact")) return "#6366f1";
            return "#8b5cf6";
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
        <Background color="#e5e7eb" gap={20} />
      </ReactFlow>
    </div>
  );
}

// Helper function to infer column type from value
function getColumnType(colName, value) {
  if (colName.toLowerCase().includes("id")) return "INT";
  if (colName.toLowerCase().includes("date")) return "DATE";
  if (colName.toLowerCase().includes("name")) return "VARCHAR";
  if (colName.toLowerCase().includes("price") || colName.toLowerCase().includes("revenue") || colName.toLowerCase().includes("cost")) return "DECIMAL";
  if (typeof value === "number") return Number.isInteger(value) ? "INT" : "FLOAT";
  if (typeof value === "string") return "VARCHAR";
  return "VARCHAR";
}

export default SchemaVisualization;

