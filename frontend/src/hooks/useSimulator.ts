import { useMutation } from "@tanstack/react-query";

import { simulatePortfolio } from "../services/simulatorApi";
import type { SimulationRequest } from "../types/simulator";

export function useSimulator(portfolioId: string | null | undefined) {
  const simulation = useMutation({
    mutationFn: (input: SimulationRequest) => {
      if (!portfolioId) {
        throw new Error("Select a portfolio before running a simulation.");
      }
      return simulatePortfolio(portfolioId, input);
    }
  });

  return {
    simulation,
    simulate: simulation.mutate,
    simulateAsync: simulation.mutateAsync
  };
}
