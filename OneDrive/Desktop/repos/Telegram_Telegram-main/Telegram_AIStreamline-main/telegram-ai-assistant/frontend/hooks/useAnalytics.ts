import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { apiHelpers } from '../utils/api'
import { AnalyticsData, APIResponse } from '../types'
import { TIME_RANGES, TimeRange } from '../utils/constants'

interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string
    borderColor?: string
    fill?: boolean
  }[]
}

interface UseAnalyticsProps {
  timeRange?: TimeRange
  startDate?: string
  endDate?: string
}

type MetricKey = keyof Omit<AnalyticsData, 'timeRange'>

export function useAnalytics({
  timeRange = TIME_RANGES.LAST_7_DAYS,
  startDate,
  endDate,
}: UseAnalyticsProps = {}) {
  const [chartData, setChartData] = useState<ChartData | null>(null)

  // Fetch analytics data
  const {
    data: response,
    isLoading,
    error,
    refetch,
  } = useQuery<APIResponse<AnalyticsData>>(
    ['analytics', timeRange, startDate, endDate],
    () => apiHelpers.getAnalytics(timeRange)
  )

  const analyticsData = response?.data

  // Transform analytics data into chart format
  useEffect(() => {
    if (analyticsData) {
      const transformedData: ChartData = {
        labels: [], // Will be populated based on time range
        datasets: [
          {
            label: 'Messages',
            data: [],
            backgroundColor: 'rgba(14, 165, 233, 0.2)',
            borderColor: 'rgb(14, 165, 233)',
            fill: true,
          },
          {
            label: 'Users',
            data: [],
            backgroundColor: 'rgba(34, 197, 94, 0.2)',
            borderColor: 'rgb(34, 197, 94)',
            fill: true,
          },
          {
            label: 'Engagement',
            data: [],
            backgroundColor: 'rgba(245, 158, 11, 0.2)',
            borderColor: 'rgb(245, 158, 11)',
            fill: true,
          },
        ],
      }

      // TODO: Populate labels and data based on analytics data
      setChartData(transformedData)
    }
  }, [analyticsData])

  const getMetricTrend = (metric: MetricKey) => {
    if (!analyticsData?.[metric]) {
      return { trend: 'stable' as const, percentage: 0 }
    }

    const data = analyticsData[metric]
    const change = data.change

    return {
      trend: change > 0 ? 'up' as const : change < 0 ? 'down' as const : 'stable' as const,
      percentage: Math.abs(change),
    }
  }

  const getMetricValue = (metric: MetricKey): number => {
    if (!analyticsData?.[metric]) {
      return 0
    }

    return analyticsData[metric].value
  }

  const formatMetricValue = (value: number): string => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`
    }
    return value.toString()
  }

  const getTimeRangeLabel = (): string => {
    switch (timeRange) {
      case TIME_RANGES.TODAY:
        return 'Today'
      case TIME_RANGES.YESTERDAY:
        return 'Yesterday'
      case TIME_RANGES.LAST_7_DAYS:
        return 'Last 7 Days'
      case TIME_RANGES.LAST_30_DAYS:
        return 'Last 30 Days'
      case TIME_RANGES.THIS_MONTH:
        return 'This Month'
      case TIME_RANGES.LAST_MONTH:
        return 'Last Month'
      case TIME_RANGES.CUSTOM:
        return `${startDate} - ${endDate}`
      default:
        return ''
    }
  }

  return {
    analyticsData,
    chartData,
    isLoading,
    error,
    refetch,
    getMetricTrend,
    getMetricValue,
    formatMetricValue,
    getTimeRangeLabel,
  }
}
