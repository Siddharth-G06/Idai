import { useInfiniteQuery } from '@tanstack/react-query'
import { api } from '../api/client'

/**
 * Fetches /api/promises with pagination and optional filters.
 * Params: { party, year, category, status }
 * Backend returns: { data: [...], pagination: { ... } }
 */
export function usePromises(params) {
  return useInfiniteQuery({
    queryKey: ['promises', params],
    queryFn: ({ pageParam = 1 }) => api.getPromises({ ...params, page: pageParam }),
    getNextPageParam: (lastPage) => {
      if (lastPage.pagination?.has_next) {
        return lastPage.pagination.page + 1
      }
      return undefined
    },
    initialPageParam: 1,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  })
}
