import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

export function useSummary() {
  return useQuery({
    queryKey: ['summary'],
    queryFn: api.getSummary,
  })
}
