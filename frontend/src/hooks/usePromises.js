import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

export function usePromises(params) {
  return useQuery({
    // Add the params stringified into the key so it re-fetches automatically when filters change
    queryKey: ['promises', params],
    queryFn: () => api.getPromises(params),
  })
}
