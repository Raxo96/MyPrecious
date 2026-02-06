import { useState, useEffect } from 'react'
import StatusCard from '../components/StatusCard'
import StatisticsCard from '../components/StatisticsCard'
import RecentUpdatesCard from '../components/RecentUpdatesCard'
import LogsCard from '../components/LogsCard'

function FetcherMonitoring() {
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    // Auto-refresh every 15 seconds
    const interval = setInterval(() => {
      setRefreshKey(prev => prev + 1)
    }, 15000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Fetcher Monitoring</h1>
        <div className="text-sm text-gray-500">
          Auto-refreshing every 15 seconds
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <StatusCard key={`status-${refreshKey}`} />
        <StatisticsCard key={`stats-${refreshKey}`} />
      </div>

      <div className="grid grid-cols-1 gap-6">
        <RecentUpdatesCard key={`updates-${refreshKey}`} />
        <LogsCard key={`logs-${refreshKey}`} />
      </div>
    </div>
  )
}

export default FetcherMonitoring
