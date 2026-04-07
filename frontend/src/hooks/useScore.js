import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

/**
 * Fetches /api/score — returns the full scores.json object.
 * Shape: { "DMK 2021": { score, fulfilled, total, categories, context, period }, ... }
 */
export function useScore() {
  return useQuery({
    queryKey: ['score'],
    queryFn:  api.getScore,
    staleTime: 1000 * 60 * 5,   // 5 minutes
    retry: 2,
  })
}
