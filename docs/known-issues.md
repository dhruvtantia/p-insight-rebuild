# Known Issues

- Production auth is not implemented. The backend uses a deterministic development demo user.
- Billing is a placeholder. No Stripe checkout or webhook verification is active.
- Broker connections are placeholders. No real broker OAuth, token exchange, or sync runs.
- Market data defaults to deterministic mock prices. Polygon/Massive and FMP providers are placeholders.
- AI Advisor defaults to deterministic mock responses. Provider keys are not used for live AI calls yet.
- Historical portfolio value, volatility, Sharpe ratio, and max drawdown return insufficient-history placeholders.
- Vite reports a bundle-size warning because Recharts and dashboard visualizations are bundled eagerly. The frontend build still passes.
