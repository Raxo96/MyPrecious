import { useState, useEffect } from 'react'
import { fetcherApi } from '../services/api'
import Loading from './Loading'

function LogsCard() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [levelFilter, setLevelFilter] = useState('all')
  const [expandedRows, setExpandedRows] = useState(new Set())

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true)
        const level = levelFilter === 'all' ? null : levelFilter
        const response = await fetcherApi.getLogs(100, 0, level)
        setLogs(response.data.logs || [])
        setError(null)
      } catch (err) {
        setError('Failed to fetch logs')
        console.error('Error fetching logs:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchLogs()
  }, [levelFilter])

  const toggleRow = (logId) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev)
      if (newSet.has(logId)) {
        newSet.delete(logId)
      } else {
        newSet.add(logId)
      }
      return newSet
    })
  }

  const getLevelColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
        return 'bg-red-100 text-red-800'
      case 'WARNING':
        return 'bg-yellow-100 text-yellow-800'
      case 'INFO':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  if (loading) return <Loading />

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Logs</h2>
        <div className="text-red-600">{error}</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Logs</h2>
        
        <div className="flex items-center space-x-2">
          <label htmlFor="level-filter" className="text-sm text-gray-600">
            Filter:
          </label>
          <select
            id="level-filter"
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Levels</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
          </select>
        </div>
      </div>
      
      {logs.length === 0 ? (
        <div className="text-gray-500 text-center py-8">No logs found</div>
      ) : (
        <div className="overflow-auto max-h-96">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Level
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Message
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.map((log) => (
                <>
                  <tr 
                    key={log.id} 
                    className={`hover:bg-gray-50 ${log.level === 'ERROR' ? 'bg-red-50' : ''}`}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-sm text-gray-600">
                        {formatTimestamp(log.timestamp)}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelColor(log.level)}`}>
                        {log.level}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-sm ${log.level === 'ERROR' ? 'font-medium text-red-900' : 'text-gray-900'}`}>
                        {log.message}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      {log.context && Object.keys(log.context).length > 0 && (
                        <button
                          onClick={() => toggleRow(log.id)}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          {expandedRows.has(log.id) ? 'Hide' : 'Show'}
                        </button>
                      )}
                    </td>
                  </tr>
                  {expandedRows.has(log.id) && log.context && (
                    <tr key={`${log.id}-details`}>
                      <td colSpan="4" className="px-4 py-3 bg-gray-50">
                        <div className="text-sm">
                          <div className="font-medium text-gray-700 mb-2">Context Details:</div>
                          <pre className="bg-white p-3 rounded border border-gray-200 overflow-auto text-xs">
                            {JSON.stringify(log.context, null, 2)}
                          </pre>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default LogsCard
