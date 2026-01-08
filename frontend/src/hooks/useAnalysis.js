import { useMutation, useQuery } from '@tanstack/react-query'
import { analyzeQuestion, getHealthStatus } from '../services/api'

/**
 * Custom hook for question analysis
 * @returns {Object} Analysis mutation and related functions
 */
export function useAnalysis() {
  const mutation = useMutation({
    mutationFn: analyzeQuestion,
    retry: 1,
  })

  return {
    analyze: mutation.mutate,
    analyzeAsync: mutation.mutateAsync,
    data: mutation.data,
    error: mutation.error,
    isLoading: mutation.isPending,
    isError: mutation.isError,
    isSuccess: mutation.isSuccess,
    reset: mutation.reset,
  }
}

/**
 * Custom hook for backend health status
 * @param {Object} options - useQuery options
 * @returns {Object} Health query result
 */
export function useHealthStatus(options = {}) {
  return useQuery({
    queryKey: ['health'],
    queryFn: getHealthStatus,
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
    ...options,
  })
}

/**
 * Custom hook to check if backend is available
 * @returns {boolean} Whether backend is healthy
 */
export function useBackendStatus() {
  const { data, isError } = useHealthStatus({
    retry: 1,
    refetchInterval: false,
  })

  return {
    isHealthy: !isError && data?.status === 'healthy',
    status: data?.status,
    timestamp: data?.timestamp,
  }
}

export default {
  useAnalysis,
  useHealthStatus,
  useBackendStatus,
}
