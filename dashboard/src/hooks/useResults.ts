import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../api/client";
import type { CompareRunsPayload, ResultRunMetadata } from "../types";

export function useResults() {
  return useQuery({
    queryKey: ["results"],
    refetchInterval: 5000,
    queryFn: async () => {
      const response = await apiClient.get<ResultRunMetadata[]>("/results");
      return response.data;
    },
  });
}

export function useCompareRuns(runIds: string[], metric: string) {
  return useQuery({
    queryKey: ["compare", runIds, metric],
    enabled: runIds.length > 0,
    queryFn: async () => {
      const response = await apiClient.get<CompareRunsPayload>(
        "/results/compare",
        {
          params: {
            run_ids: runIds.join(","),
            metric,
          },
        },
      );
      return response.data;
    },
  });
}
