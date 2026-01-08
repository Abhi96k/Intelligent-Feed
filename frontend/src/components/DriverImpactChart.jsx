import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'

/**
 * DriverImpactChart Component
 * Displays driver impact analysis using a horizontal bar chart
 *
 * @param {Object} props
 * @param {Object} props.data - Driver impact data object
 * @param {Array} props.data.drivers - Array of {driver_name, impact_score, direction} objects
 * @param {string} props.data.primary_driver - Name of the primary driver
 */
function DriverImpactChart({ data }) {
  if (!data || !data.drivers || data.drivers.length === 0) {
    return (
      <div className="card">
        <h3 className="card-header">Driver Impact Analysis</h3>
        <div className="text-center py-8 text-gray-500">
          No driver impact data available
        </div>
      </div>
    )
  }

  const { drivers = [], primary_driver = '' } = data

  // Format the data for Recharts and sort by impact score
  const chartData = drivers
    .map(driver => ({
      name: driver.driver_name || driver.name || 'Unknown',
      impact: Math.abs(driver.impact_score || driver.impact || 0),
      rawImpact: driver.impact_score || driver.impact || 0,
      direction: driver.direction || (driver.impact_score > 0 ? 'positive' : 'negative'),
      isPrimary: driver.driver_name === primary_driver || driver.name === primary_driver,
    }))
    .sort((a, b) => b.impact - a.impact)
    .slice(0, 10) // Show top 10 drivers

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-semibold text-gray-900 mb-1">{data.name}</p>
          <p className="text-xs text-gray-600">
            Impact: <span className="font-semibold">{data.rawImpact.toFixed(2)}</span>
          </p>
          <p className="text-xs text-gray-600">
            Direction: <span className={`font-semibold capitalize ${
              data.direction === 'positive' ? 'text-success-600' : 'text-error-600'
            }`}>
              {data.direction}
            </span>
          </p>
          {data.isPrimary && (
            <p className="text-xs text-primary-600 font-semibold mt-1">Primary Driver</p>
          )}
        </div>
      )
    }
    return null
  }

  // Get bar color based on direction
  const getBarColor = (direction, isPrimary) => {
    if (isPrimary) return '#1d4ed8' // primary-700
    return direction === 'positive' ? '#22c55e' : '#ef4444'
  }

  // Custom label for bars
  const CustomLabel = (props) => {
    const { x, y, width, height, value, payload } = props
    const radius = 10

    return (
      <g>
        {payload.isPrimary && (
          <text
            x={x + width + 5}
            y={y + height / 2}
            fill="#1d4ed8"
            fontSize={12}
            fontWeight="bold"
            textAnchor="start"
            dominantBaseline="middle"
          >
            Primary
          </text>
        )}
      </g>
    )
  }

  return (
    <div className="card">
      <div className="mb-6">
        <h3 className="card-header mb-2">Driver Impact Analysis</h3>
        <p className="text-sm text-gray-600">
          Top factors influencing the metric
          {primary_driver && (
            <span className="ml-2 text-primary-600 font-medium">
              Primary: {primary_driver}
            </span>
          )}
        </p>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 80, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ value: 'Impact Score', position: 'insideBottom', offset: -5, fontSize: 12 }}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            width={150}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }}
            payload={[
              { value: 'Positive Impact', type: 'square', color: '#22c55e' },
              { value: 'Negative Impact', type: 'square', color: '#ef4444' },
              { value: 'Primary Driver', type: 'square', color: '#1d4ed8' },
            ]}
          />
          <Bar
            dataKey="impact"
            name="Impact Score"
            label={<CustomLabel />}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getBarColor(entry.direction, entry.isPrimary)}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Driver Summary */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Total Drivers</span>
            <p className="font-semibold text-gray-900 mt-1">{drivers.length}</p>
          </div>
          <div>
            <span className="text-gray-500">Positive Impact</span>
            <p className="font-semibold text-success-600 mt-1">
              {drivers.filter(d => (d.impact_score || d.impact || 0) > 0).length}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Negative Impact</span>
            <p className="font-semibold text-error-600 mt-1">
              {drivers.filter(d => (d.impact_score || d.impact || 0) < 0).length}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DriverImpactChart
