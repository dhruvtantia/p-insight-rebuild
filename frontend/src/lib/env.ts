export const appEnv = import.meta.env.VITE_APP_ENV || "local";

export const demoModeEnabled = appEnv === "local" || import.meta.env.VITE_ENABLE_DEMO_MODE === "true";

export const betaFeedbackUrl = import.meta.env.VITE_BETA_FEEDBACK_URL?.trim() || "";
