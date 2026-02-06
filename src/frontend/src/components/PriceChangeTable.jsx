import PropTypes from 'prop-types'

/**
 * PriceChangeTable Component
 * 
 * Displays a table of price changes across multiple time periods (1D, 1M, 3M, 6M, 1Y).
 * 
 * Requirements:
 * - 4.1: Display table with columns for each time period
 * - 4.2: Format percentage values to 2 decimal places with % sign
 * - 4.3: Display "N/A" for null values
 * - 4.4: Green color for positive changes
 * - 4.5: Red color for negative changes
 * - 4.6: Gray color for zero or null values
 */
function PriceChangeTable({ priceChanges }) {
  const periods = [
    { key: '1D', label: '1 Day' },
    { key: '1M', label: '1 Month' },
    { key: '3M', label: '3 Months' },
    { key: '6M', label: '6 Months' },
    { key: '1Y', label: '1 Year' }
  ]

  /**
   * Format a price change value for display
   * @param {number|null} value - The price change percentage
   * @returns {string} Formatted string with % sign or "N/A"
   */
  const formatPriceChange = (value) => {
    if (value === null || value === undefined) {
      return 'N/A'
    }
    
    const formatted = value.toFixed(2)
    return value > 0 ? `+${formatted}%` : `${formatted}%`
  }

  /**
   * Get the color class for a price change value
   * @param {number|null} value - The price change percentage
   * @returns {string} Tailwind CSS color class
   */
  const getColorClass = (value) => {
    if (value === null || value === undefined || value === 0) {
      return 'text-gray-500'
    }
    return value > 0 ? 'text-green-600' : 'text-red-600'
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Price Changes</h2>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              {periods.map(period => (
                <th 
                  key={period.key}
                  className="px-4 py-3 text-center text-sm font-semibold text-gray-700"
                >
                  {period.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              {periods.map(period => {
                const value = priceChanges?.[period.key]
                return (
                  <td 
                    key={period.key}
                    className={`px-4 py-4 text-center text-lg font-semibold ${getColorClass(value)}`}
                  >
                    {formatPriceChange(value)}
                  </td>
                )
              })}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

PriceChangeTable.propTypes = {
  priceChanges: PropTypes.shape({
    '1D': PropTypes.number,
    '1M': PropTypes.number,
    '3M': PropTypes.number,
    '6M': PropTypes.number,
    '1Y': PropTypes.number
  })
}

PriceChangeTable.defaultProps = {
  priceChanges: {}
}

export default PriceChangeTable
