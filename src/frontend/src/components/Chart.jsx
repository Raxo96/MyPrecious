import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

function Chart({ data, type = 'line' }) {
  const chartContainerRef = useRef()
  const chartRef = useRef()
  const seriesRef = useRef()

  useEffect(() => {
    if (!chartContainerRef.current) return

    // Create chart
    chartRef.current = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 300,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      timeScale: {
        borderColor: '#cccccc',
      },
      rightPriceScale: {
        borderColor: '#cccccc',
      },
    })

    // Add series
    if (type === 'line') {
      seriesRef.current = chartRef.current.addLineSeries({
        color: '#3B82F6',
        lineWidth: 2,
      })
    } else if (type === 'candlestick') {
      seriesRef.current = chartRef.current.addCandlestickSeries({
        upColor: '#10B981',
        downColor: '#EF4444',
        borderDownColor: '#EF4444',
        borderUpColor: '#10B981',
        wickDownColor: '#EF4444',
        wickUpColor: '#10B981',
      })
    }

    // Handle resize
    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (chartRef.current) {
        chartRef.current.remove()
      }
    }
  }, [type])

  useEffect(() => {
    if (seriesRef.current && data && data.length > 0) {
      seriesRef.current.setData(data)
    }
  }, [data])

  return (
    <div className="w-full">
      <div ref={chartContainerRef} className="w-full h-[300px]" />
    </div>
  )
}

export default Chart