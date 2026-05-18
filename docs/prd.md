# P-insight Product Requirements

## Product Summary

P-insight is a portfolio analytics dashboard that helps users upload or later connect portfolio data, validate holdings, review portfolio analytics, see rule-based insights, and ask AI-powered portfolio questions.

The MVP is focused on trusted portfolio data first. Analytics, market data, AI explanations, broker connections, and billing must all depend on clean internal portfolio data.

## MVP User Flow

Landing page -> auth placeholder -> onboarding -> create portfolio -> add or upload holdings -> validate holdings -> dashboard -> analytics -> AI advisor.

## MVP Features

- Landing page that introduces P-insight.
- Safe auth placeholder that can later be replaced by Supabase Auth or Clerk.
- Onboarding flow that guides users to create a portfolio.
- Portfolio creation.
- Manual holding entry or file upload path.
- Upload validation before holdings are saved.
- Dashboard summary based on portfolio data.
- Analytics views for allocation, concentration, and basic portfolio metrics.
- Rule-based insights.
- AI advisor mock that uses structured portfolio context.

## Out-of-Scope Features

- Production auth.
- Real broker connections.
- Live Stripe billing.
- Frontend market data API calls.
- Frontend AI API calls.
- Guaranteed investment advice.
- Mobile app implementation.
- Tax optimization.
- Trading execution.
- Microservices.

## Freemium Plan Direction

Initial plan tiers:
- Free: limited portfolios, limited AI questions, basic analytics.
- Pro: more portfolios, higher AI usage, deeper analytics.
- Premium Later: advanced workflows, broker sync, team/family views, and expanded advisor features.

Billing is a placeholder in the MVP. Live payment collection is intentionally deferred.

## Future Mobile App Direction

A future mobile app should consume the same backend APIs as the web application. Mobile should not introduce a separate portfolio model, direct market data access, or direct AI provider access.
