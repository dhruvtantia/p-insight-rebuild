import { useMutation, useQuery } from "@tanstack/react-query";

import { billingApi } from "../services/billingApi";

export function useBilling() {
  const plan = useQuery({
    queryKey: ["billing", "plan"],
    queryFn: billingApi.getPlan
  });

  const createCheckoutSession = useMutation({
    mutationFn: billingApi.createCheckoutSession
  });

  return {
    plan,
    createCheckoutSession
  };
}
