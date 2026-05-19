# Known Limitations

These limitations are acceptable for the private beta MVP and should be disclosed to beta users.

## Authentication

Authentication is still a placeholder. The app uses deterministic development user behavior in backend dependencies until Supabase Auth, Clerk, or another auth provider is fully wired.

## Market Data

Market data defaults to mock provider behavior. Real Polygon or FMP data can be configured later with backend-only API keys, but the beta should not assume full live market coverage.

## Broker Sync

Broker connection screens and APIs are placeholders for future integrations. There is no live broker account sync yet.

## Billing

Stripe billing is not live. Billing screens and backend placeholders exist for product shaping, but beta users should not expect real subscriptions, invoices, or payment collection.

## Analytics History

Analytics history is limited to the data currently stored or uploaded in the app. Long-term performance history, benchmark comparisons, and richer historical time series are not complete yet.
