import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

/**
 * Fetches /api/summary — per-party summary derived from scores.json.
 * Shape: { "DMK 2021": { party, year, score, fulfilled, total, top_category, categories, context, period }, ... }
 */
export function useSummary() {
  return useQuery({
    queryKey: ['summary'],
    queryFn:  api.getSummary,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  })
}
