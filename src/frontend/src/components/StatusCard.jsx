import { useState, useEffect } from 'react'
import { fetcherApi } from '../services/api'
import Loading from './Loading'

function StatusCard() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [countdown, setCountdown] = useState(0)
  const [triggering, setTriggering] = useState(false)
  const [triggerMessage, setTriggerMessage] = useState(null)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true)
        const response = await fetcherApi.getStatus()
        setStatus(response.data)
        setCountdown(response.data.next_update_in_seconds || 0)
        setError(null)
      } catch (err) {
        setError('Failed to fetch status')
        console.error('Error fetching status:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
  }, [])

  useEffect(() => {
    if (countdown <= 0) return

    const timer = setInterval(() => {
      setCountdown(prev => Math.max(0, prev - 1))
    }, 1000)

    return () => clearInterval(timer)
  }, [countdown])

  const getStatusColor = (status) => {
    if (status === 'running') return 'bg-green-500'
    if (status === 'error') return 'bg-red-500'
    return 'bg-gray-500'
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
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

  const handleTriggerUpdate = async () => {
    setTriggering(true)
    setTriggerMessage(null)
    
    try {
      const response = await fetcherApi.triggerUpdate()
      if (response.data.success) {
        setTriggerMessage({ type: 'success', text: 'Price update triggered! Check logs for progress.' })
        // Refresh status after a short delay
        setTimeout(async () => {
          const statusResponse = await fetcherApi.getStatus()
          setStatus(statusResponse.data)
          setCountdown(statusResponse.data.next_update_in_seconds || 0)
        }, 2000)
      } else {
        setTriggerMessage({ type: 'error', text: response.data.message || 'Failed to trigger update' })
      }
    } catch (err) {
      setTriggerMessage({ type: 'error', text: 'Failed to trigger update' })
      console.error('Error triggering update:', err)
    } finally {
      setTriggering(false)
      // Clear message after 5 seconds
      setTimeout(() => setTriggerMessage(null), 5000)
    }
  }

  if (loading) return <Loading />

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Daemon Status</h2>
        <div className="text-red-600">{error}</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Daemon Status</h2>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Status</span>
          <div className="flex items-center space-x-2">
            <span className={`w-3 h-3 rounded-full ${getStatusColor(status?.status)}`}></span>
            <span className="font-medium capitalize">{status?.status || 'Unknown'}</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-600">Last Update</span>
          <span className="font-medium">{formatTimestamp(status?.last_update)}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-600">Next Update In</span>
          <span className="font-medium text-blue-600">{formatTime(countdown)}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-600">Tracked Assets</span>
          <span className="font-medium text-lg">{status?.tracked_assets_count || 0}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-600">Update Interval</span>
          <span className="font-medium">{status?.update_interval_minutes || 10} minutes</span>
        </div>

        {triggerMessage && (
          <div className={`p-3 rounded-md ${
            triggerMessage.type === 'success' 
              ? 'bg-green-50 text-green-800 border border-green-200' 
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {triggerMessage.text}
          </div>
        )}

        <button
          onClick={handleTriggerUpdate}
          disabled={triggering}
          className={`w-full mt-4 px-4 py-2 rounded-md font-medium transition-colors ${
            triggering
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {triggering ? 'Triggering...' : '🔄 Trigger Update Now'}
        </button>
      </div>
    </div>
  )
}

export default StatusCard
