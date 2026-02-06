import { useState, useEffect } from 'react'
import { fetcherApi } from '../services/api'
import Loading from './Loading'

function StatisticsCard() {
  const [statistics, setStatistics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchStatistics = async () => {
      try {
        setLoading(true)
        const response = await fetcherApi.getStatistics()
        setStatistics(response.data)
        setError(null)
      } catch (err) {
        setError('Failed to fetch statistics')
        console.error('Error fetching statistics:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchStatistics()
  }, [])

  const formatUptime = (seconds) => {
    if (!seconds) return 'N/A'
    
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    const parts = []
    if (days > 0) parts.push(`${days}d`)
    if (hours > 0) parts.push(`${hours}h`)
    if (minutes > 0) parts.push(`${minutes}m`)
    
    return parts.length > 0 ? parts.join(' ') : '< 1m'
  }

  const getSuccessRateColor = (rate) => {
    if (rate >= 95) return 'text-green-600'
    if (rate >= 80) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getSuccessRateBarColor = (rate) => {
    if (rate >= 95) return 'bg-green-500'
    if (rate >= 80) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  if (loading) return <Loading />

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Statistics</h2>
        <div className="text-red-600">{error}</div>
      </div>
    )
  }

  const successRate = statistics?.success_rate || 0

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Statistics</h2>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Uptime</span>
          <span className="font-medium text-lg">
            {formatUptime(statistics?.uptime_seconds)}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-600">Total Cycles</span>
          <span className="font-medium text-lg">{statistics?.total_cycles || 0}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-600">Successful</span>
          <span className="font-medium text-green-600">
            {statistics?.successful_cycles || 0}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-600">Failed</span>
          <span className="font-medium text-red-600">
            {statistics?.failed_cycles || 0}
          </span>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-600">Success Rate</span>
            <span className={`font-medium text-lg ${getSuccessRateColor(successRate)}`}>
              {successRate.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${getSuccessRateBarColor(successRate)}`}
              style={{ width: `${successRate}%` }}
            ></div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-600">Avg Cycle Duration</span>
          <span className="font-medium">
            {statistics?.average_cycle_duration_seconds 
              ? `${statistics.average_cycle_duration_seconds.toFixed(1)}s`
              : 'N/A'}
          </span>
        </div>

        {statistics?.last_cycle_duration_seconds !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Last Cycle Duration</span>
            <span className="font-medium">
              {statistics.last_cycle_duration_seconds.toFixed(1)}s
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default StatisticsCard
