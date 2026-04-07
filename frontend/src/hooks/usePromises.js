import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

/**
 * Fetches /api/promises with optional filters.
 * Params: { party, year, category, status }
 * Backend returns: { count: N, promises: [...] }
 */
export function usePromises(params) {
  return useQuery({
    queryKey: ['promises', params],
    queryFn:  () => api.getPromises(params),
    staleTime: 1000 * 60 * 5,
    retry: 2,
  })
}
