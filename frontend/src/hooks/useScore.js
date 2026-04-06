import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

export function useScore() {
  return useQuery({
    queryKey: ['score'],
    queryFn: api.getScore,
    staleTime: 1000 * 60 * 60 * 6, // 6 hours
  })
}
