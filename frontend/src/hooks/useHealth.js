import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    staleTime: 1000 * 30, // 30 seconds
    retry: false,
  })
}
