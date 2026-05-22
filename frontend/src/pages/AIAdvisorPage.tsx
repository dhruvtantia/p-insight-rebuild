import { AlertTriangle, Bot, Clock, Info, MessageSquare, Plus, Send, Sparkles, Upload } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Badge, Button, Card, CardTitle, DataStatusBadge, EmptyState, ErrorState, LoadingState } from "../components/ui";
import { useAIAdvisor } from "../hooks/useAIAdvisor";
import { useAnalytics } from "../hooks/useAnalytics";
import { useAppStatus } from "../hooks/useAppStatus";
import { usePortfolios } from "../hooks/usePortfolios";
import type { AIAdvisorContext, AIAdvisorResponse, AIAdvisorStructuredResponse, AIMessageResponse } from "../types/ai";
import type { Portfolio } from "../types/portfolio";

const SUGGESTED_QUESTIONS = [
  "Summarize my portfolio",
  "Where is my portfolio concentrated?",
  "How diversified is this portfolio?",
  "Which risk metrics should I review?",
  "What fundamentals coverage is missing?",
  "How do peers affect this context?",
  "What changed across snapshots?"
];

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  provider?: string | null;
  model?: string | null;
  created_at?: string;
  structuredResponse?: AIAdvisorStructuredResponse | null;
  context?: AIAdvisorContext;
};

export function AIAdvisorPage() {
  const portfolios = usePortfolios();
  const [selectedPortfolioId, setSelectedPortfolioId] = useState("");
  const selectedPortfolio = useMemo(
    () => portfolios.data?.find((portfolio) => portfolio.id === selectedPortfolioId) ?? portfolios.data?.[0] ?? null,
    [portfolios.data, selectedPortfolioId]
  );

  useEffect(() => {
    if (!selectedPortfolioId && portfolios.data?.length) {
      setSelectedPortfolioId(portfolios.data[0].id);
    }
  }, [portfolios.data, selectedPortfolioId]);

  const analytics = useAnalytics(selectedPortfolio?.id);
  const advisor = useAIAdvisor(selectedPortfolio?.id);
  const appStatus = useAppStatus();
  const [question, setQuestion] = useState("");
  const [sessionMessages, setSessionMessages] = useState<ChatMessage[]>([]);

  const historyMessages = advisor.selectedConversation.data?.messages
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map(toChatMessage);
  const visibleMessages = historyMessages?.length ? historyMessages : sessionMessages;
  const advisorContext =
    advisor.selectedConversation.data?.context ??
    [...sessionMessages].reverse().find((message) => message.role === "assistant")?.context;

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!portfolios.data?.length) {
    return (
      <div className="space-y-6">
        <AIAdvisorHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio before using the AI advisor." />
        <Link to="/onboarding">
          <Button>
            <Plus size={16} />
            Create portfolio
          </Button>
        </Link>
      </div>
    );
  }

  const isEmptyPortfolio = analytics.summary.data?.holdings.length === 0;
  const aiError =
    advisor.generateSummary.error?.message ??
    advisor.askQuestion.error?.message ??
    advisor.selectedConversation.error?.message ??
    advisor.error?.message;

  function handleSummary() {
    advisor.setSelectedConversationId(null);
    advisor.generateSummary.mutate(undefined, {
      onSuccess: (response) => setSessionMessages([responseToAssistantMessage(response)])
    });
  }

  function handleQuestionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submitQuestion(question);
  }

  function submitQuestion(value: string) {
    const cleanedQuestion = value.trim();
    if (!cleanedQuestion) {
      return;
    }
    advisor.setSelectedConversationId(null);
    setQuestion("");
    setSessionMessages((messages) => [...messages, { role: "user", content: cleanedQuestion }]);
    advisor.askQuestion.mutate(cleanedQuestion, {
      onSuccess: (response) => {
        setSessionMessages((messages) => [...messages, responseToAssistantMessage(response)]);
      }
    });
  }

  function handleSuggestedQuestion(value: string) {
    if (value === "Summarize my portfolio") {
      handleSummary();
      return;
    }
    submitQuestion(value);
  }

  return (
    <div className="space-y-6">
      <AIAdvisorHeader />

      <div className="grid gap-6 xl:grid-cols-[310px_1fr_330px]">
        <ContextPanel
          portfolios={portfolios.data}
          selectedPortfolioId={selectedPortfolio?.id ?? ""}
          selectedPortfolio={selectedPortfolio}
          onSelectPortfolio={(portfolioId) => {
            setSelectedPortfolioId(portfolioId);
            setSessionMessages([]);
            advisor.setSelectedConversationId(null);
          }}
          summary={analytics.summary.data}
          rulesCount={analytics.rules.data?.length}
          isLoading={analytics.isLoading}
          isError={analytics.isError}
          errorMessage={analytics.error?.message}
        />

        <main className="space-y-4">
          {isEmptyPortfolio ? <EmptyHoldingsCta /> : null}
          {aiError ? <ErrorState title="AI advisor unavailable" detail={aiError} /> : null}
          {analytics.isError ? <ErrorState title="Missing analytics" detail={analytics.error?.message} /> : null}
          <ChatPanel
            messages={visibleMessages}
            aiProviderMode={appStatus.data?.ai_provider_mode}
            advisorContext={advisorContext}
            isLoading={advisor.generateSummary.isPending || advisor.askQuestion.isPending}
            question={question}
            onQuestionChange={setQuestion}
            onSummary={handleSummary}
            onSubmit={handleQuestionSubmit}
            disableActions={!selectedPortfolio?.id}
          />
        </main>

        <aside className="space-y-4">
          <BackendContextPanel context={advisorContext} />
          <SuggestedQuestions
            questions={SUGGESTED_QUESTIONS}
            onSelect={handleSuggestedQuestion}
            disabled={advisor.generateSummary.isPending || advisor.askQuestion.isPending}
          />
          <ConversationHistory
            conversations={advisor.conversations.data ?? []}
            selectedConversationId={advisor.selectedConversationId}
            isLoading={advisor.conversations.isLoading}
            onSelect={(conversationId) => {
              advisor.setSelectedConversationId(conversationId);
              setSessionMessages([]);
            }}
          />
        </aside>
      </div>
    </div>
  );
}

function AIAdvisorHeader() {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">AI Advisor</p>
        <h1 className="mt-1 text-3xl font-semibold">Portfolio Q&A</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Ask questions against backend-built portfolio context. No external AI keys are used in the browser.
        </p>
      </div>
      <Link to="/analytics">
        <Button variant="secondary">Review analytics</Button>
      </Link>
    </section>
  );
}

function ContextPanel({
  portfolios,
  selectedPortfolioId,
  selectedPortfolio,
  onSelectPortfolio,
  summary,
  rulesCount,
  isLoading,
  isError,
  errorMessage
}: {
  portfolios: Portfolio[];
  selectedPortfolioId: string;
  selectedPortfolio: Portfolio | null;
  onSelectPortfolio: (portfolioId: string) => void;
  summary?: {
    total_portfolio_value: number;
    total_unrealized_gain_loss: number;
    total_unrealized_gain_loss_pct: number | null;
    holdings: unknown[];
    largest_holding: { symbol: string; weight: number } | null;
    base_currency: string;
  };
  rulesCount?: number;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
}) {
  return (
    <Card>
      <CardTitle>Portfolio context</CardTitle>
      <label className="mt-4 grid gap-2">
        <span className="text-sm font-medium text-ink">Portfolio</span>
        <select
          className="h-10 rounded-md border border-line bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
          value={selectedPortfolioId}
          onChange={(event) => onSelectPortfolio(event.target.value)}
        >
          {portfolios.map((portfolio) => (
            <option key={portfolio.id} value={portfolio.id}>
              {portfolio.name}
            </option>
          ))}
        </select>
      </label>

      {isLoading ? (
        <div className="mt-4">
          <LoadingState label="Loading context" />
        </div>
      ) : isError ? (
        <div className="mt-4">
          <ErrorState title="Missing analytics" detail={errorMessage} />
        </div>
      ) : (
        <div className="mt-5 grid gap-4">
          <ContextMetric label="Base currency" value={selectedPortfolio?.base_currency ?? "N/A"} />
          <ContextMetric label="Total value" value={formatCurrency(summary?.total_portfolio_value ?? null, summary?.base_currency ?? "INR")} />
          <ContextMetric label="Total P/L" value={formatCurrency(summary?.total_unrealized_gain_loss ?? null, summary?.base_currency ?? "INR")} />
          <ContextMetric label="Total P/L %" value={formatPercent(summary?.total_unrealized_gain_loss_pct ?? null)} />
          <ContextMetric label="Holdings" value={summary ? String(summary.holdings.length) : "N/A"} />
          <ContextMetric label="Largest holding" value={summary?.largest_holding?.symbol ?? "N/A"} />
          <ContextMetric label="Rules active" value={typeof rulesCount === "number" ? String(rulesCount) : "N/A"} />
        </div>
      )}
    </Card>
  );
}

function ChatPanel({
  messages,
  aiProviderMode,
  advisorContext,
  isLoading,
  question,
  onQuestionChange,
  onSummary,
  onSubmit,
  disableActions
}: {
  messages: ChatMessage[];
  aiProviderMode?: string;
  advisorContext?: AIAdvisorContext;
  isLoading: boolean;
  question: string;
  onQuestionChange: (value: string) => void;
  onSummary: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  disableActions: boolean;
}) {
  return (
    <Card className="min-h-[620px]">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>Advisor chat</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Responses come from backend structured context and mock fallback.</p>
        </div>
        <Button type="button" onClick={onSummary} disabled={disableActions || isLoading}>
          <Sparkles size={16} />
          {isLoading ? "Working" : "Generate summary"}
        </Button>
      </div>

      <div className="mt-5 flex min-h-[360px] flex-col gap-3 rounded-md border border-line bg-surface p-4">
        {!messages.length && !isLoading ? (
          <div className="flex h-full min-h-[320px] items-center justify-center text-center">
            <div>
              <Bot className="mx-auto text-accent" size={30} />
              <p className="mt-3 text-sm font-semibold text-ink">Ask a portfolio question</p>
              <p className="mt-1 max-w-md text-sm leading-6 text-slate-600">
                Generate a summary or use a suggested question to start an MVP advisor conversation.
              </p>
            </div>
          </div>
        ) : null}
        {messages.map((message, index) => (
          <ChatBubble
            key={`${message.role}-${index}-${message.created_at ?? ""}`}
            message={message}
            aiProviderMode={aiProviderMode}
            advisorContext={message.context ?? advisorContext}
          />
        ))}
        {isLoading ? (
          <div className="self-start rounded-md bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
            Building response from backend context...
          </div>
        ) : null}
      </div>

      <form className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={onSubmit}>
        <textarea
          className="min-h-24 w-full resize-y rounded-md border border-line bg-white px-3 py-2 text-sm outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-2 focus:ring-accent/15"
          placeholder="Ask about concentration, missing data, performance, risk, fundamentals, peers, or changes..."
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
        />
        <Button type="submit" disabled={disableActions || isLoading || !question.trim()} className="self-end">
          <Send size={16} />
          Ask
        </Button>
      </form>
    </Card>
  );
}

function SuggestedQuestions({
  questions,
  onSelect,
  disabled
}: {
  questions: string[];
  onSelect: (question: string) => void;
  disabled: boolean;
}) {
  return (
    <Card>
      <CardTitle>Suggested questions</CardTitle>
      <div className="mt-4 grid gap-2">
        {questions.map((suggestedQuestion) => (
          <Button
            key={suggestedQuestion}
            type="button"
            variant="secondary"
            className="h-auto justify-start whitespace-normal py-2 text-left"
            disabled={disabled}
            onClick={() => onSelect(suggestedQuestion)}
          >
            <MessageSquare size={15} />
            {suggestedQuestion}
          </Button>
        ))}
      </div>
    </Card>
  );
}

function ConversationHistory({
  conversations,
  selectedConversationId,
  isLoading,
  onSelect
}: {
  conversations: Array<{ id: string; title: string | null; mode: string | null; created_at: string }>;
  selectedConversationId: string | null;
  isLoading: boolean;
  onSelect: (conversationId: string) => void;
}) {
  if (isLoading) {
    return <LoadingState label="Loading conversations" />;
  }

  if (!conversations.length) {
    return <EmptyState title="Conversation history" detail="Generated summaries and questions will appear here." />;
  }

  return (
    <Card>
      <CardTitle>Conversation history</CardTitle>
      <div className="mt-4 grid gap-2">
        {conversations.map((conversation) => (
          <button
            key={conversation.id}
            type="button"
            className={[
              "rounded-md border px-3 py-2 text-left text-sm transition",
              selectedConversationId === conversation.id ? "border-accent bg-accent/5" : "border-line bg-white hover:bg-surface"
            ].join(" ")}
            onClick={() => onSelect(conversation.id)}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold text-ink">{conversation.title ?? "Advisor conversation"}</span>
              {conversation.mode ? <Badge>{conversation.mode}</Badge> : null}
            </div>
            <p className="mt-1 flex items-center gap-1 text-xs text-slate-500">
              <Clock size={12} />
              {formatDateTime(conversation.created_at)}
            </p>
          </button>
        ))}
      </div>
    </Card>
  );
}

function EmptyHoldingsCta() {
  return (
    <Card className="border-dashed">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>No holdings yet</CardTitle>
          <p className="mt-2 text-sm text-slate-600">The advisor can explain that data is missing, but useful answers need holdings.</p>
        </div>
        <Link to="/upload">
          <Button>
            <Upload size={16} />
            Upload holdings
          </Button>
        </Link>
      </div>
    </Card>
  );
}

function BackendContextPanel({ context }: { context?: AIAdvisorContext }) {
  if (!context) {
    return <EmptyState title="Backend context" detail="Generate a summary or ask a question to inspect the backend context used for the answer." />;
  }

  const optionalContext = context.optional_context ?? {};
  const optionalBlocks = [
    optionalContext.dashboard_summary ? "Dashboard" : null,
    optionalContext.performance_history_summary ? "Performance" : null,
    optionalContext.risk_v2_summary ? "Risk" : null,
    optionalContext.fundamentals_summary ? "Fundamentals" : null,
    optionalContext.peer_summary ? "Peers" : null,
    optionalContext.snapshot_change_summary ? "Changes" : null
  ].filter((value): value is string => Boolean(value));
  const summary = context.portfolio_summary;
  const priceFreshness = context.price_freshness;

  return (
    <Card>
      <CardTitle>Backend context</CardTitle>
      <div className="mt-4 grid gap-3">
        <ContextMetric label="Portfolio" value={summary?.name ?? "N/A"} />
        <ContextMetric label="Holdings" value={String(summary?.holdings_count ?? context.holdings?.length ?? 0)} />
        <ContextMetric label="Latest price source" value={priceFreshness?.latest_price_source ?? "N/A"} />
        <ContextMetric
          label="Missing prices"
          value={priceFreshness?.missing_price_symbols?.length ? priceFreshness.missing_price_symbols.join(", ") : "None"}
        />
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Optional context</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {optionalBlocks.length ? optionalBlocks.map((block) => <Badge key={block}>{block}</Badge>) : <Badge tone="neutral">Core only</Badge>}
          </div>
        </div>
        {optionalContext.performance_history_summary?.data_status ? (
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Performance status</p>
            <DataStatusBadge status={optionalContext.performance_history_summary.data_status} />
          </div>
        ) : null}
        {optionalContext.fundamentals_summary?.data_status ? (
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Fundamentals status</p>
            <DataStatusBadge status={optionalContext.fundamentals_summary.data_status} />
          </div>
        ) : null}
      </div>
    </Card>
  );
}

function ChatBubble({
  message,
  aiProviderMode,
  advisorContext
}: {
  message: ChatMessage;
  aiProviderMode?: string;
  advisorContext?: AIAdvisorContext;
}) {
  const isUser = message.role === "user";
  const isMockAiResponse =
    !isUser && (message.provider?.trim().toLowerCase() === "mock" || aiProviderMode?.trim().toLowerCase() === "mock");
  const structuredResponse =
    !isUser && message.structuredResponse
      ? message.structuredResponse
      : !isUser
        ? buildStructuredResponse(message, advisorContext)
        : null;
  return (
    <div className={isUser ? "self-end" : "self-start"}>
      <div className={["max-w-2xl rounded-md px-4 py-3 text-sm leading-6 shadow-sm", isUser ? "bg-accent text-white" : "bg-white text-slate-700"].join(" ")}>
        {isMockAiResponse ? (
          <div className="mb-3 flex flex-wrap gap-2">
            <Badge tone="warning">Mock advisor</Badge>
            {message.model ? <Badge>{message.model}</Badge> : null}
          </div>
        ) : null}
        {structuredResponse ? <StructuredAdvisorResponseView response={structuredResponse} /> : message.content}
      </div>
      {message.created_at ? (
        <p className={["mt-1 text-xs text-slate-500", isUser ? "text-right" : ""].join(" ")}>{formatDateTime(message.created_at)}</p>
      ) : null}
    </div>
  );
}

function StructuredAdvisorResponseView({ response }: { response: AIAdvisorStructuredResponse }) {
  const sections = [
    { title: "Insights", items: response.insights, tone: "neutral" as const },
    { title: "Warnings", items: response.warnings, tone: "warning" as const },
    { title: "Suggestions", items: response.suggestions, tone: "neutral" as const },
    { title: "Limitations", items: response.limitations, tone: "warning" as const },
    { title: "Follow-up questions", items: response.follow_up_questions, tone: "neutral" as const }
  ];

  return (
    <div className="space-y-4">
      {response.provider_metadata ? (
        <div className="flex flex-wrap gap-2">
          <Badge tone={response.provider_metadata.is_mock ? "warning" : "neutral"}>
            {response.provider_metadata.provider}
          </Badge>
          <Badge>{response.provider_metadata.model}</Badge>
        </div>
      ) : null}
      {response.summary ? <p>{response.summary}</p> : null}
      {sections.map((section) =>
        section.items?.length ? (
          <div key={section.title}>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">{section.title}</p>
            <ul className="space-y-2">
              {section.items.map((item) => (
                <li key={item} className="flex gap-2">
                  {section.tone === "warning" ? (
                    <AlertTriangle className="mt-1 shrink-0 text-amber-700" size={14} />
                  ) : (
                    <Info className="mt-1 shrink-0 text-accent" size={14} />
                  )}
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null
      )}
    </div>
  );
}

function buildStructuredResponse(message: ChatMessage, context?: AIAdvisorContext): AIAdvisorStructuredResponse {
  const warnings = collectAdvisorWarnings(context);
  return {
    summary: message.content,
    insights: collectAdvisorInsights(context),
    warnings,
    suggestions: collectAdvisorSuggestions(context),
    limitations: collectAdvisorLimitations(message, context),
    follow_up_questions: [
      "Which concentration areas should I review?",
      "What diversification gaps are visible?",
      "Which risk metrics need more data?",
      "What fundamentals coverage is missing?",
      "What peer context is available?",
      "What changed across recent snapshots?"
    ],
    provider_metadata: {
      provider: message.provider ?? "unknown",
      model: message.model ?? "unknown",
      is_mock: message.provider?.trim().toLowerCase() === "mock"
    }
  };
}

function collectAdvisorInsights(context?: AIAdvisorContext) {
  const insights: string[] = [];
  for (const insight of context?.rule_based_insights ?? []) {
    const text = [insight.title, insight.message].filter(Boolean).join(": ");
    if (text) {
      insights.push(text);
    }
  }
  const largest = context?.portfolio_summary?.largest_holding;
  if (largest?.symbol && typeof largest.weight === "number") {
    insights.unshift(`${largest.symbol} is the largest holding at ${formatPercent(largest.weight)}.`);
  }
  const optionalContext = context?.optional_context;
  if (optionalContext?.peer_summary?.symbol) {
    insights.push(`Peer context is available for ${optionalContext.peer_summary.symbol}.`);
  }
  if (typeof optionalContext?.snapshot_change_summary?.snapshot_count === "number") {
    insights.push(`${optionalContext.snapshot_change_summary.snapshot_count} snapshot(s) are available in advisor context.`);
  }
  return insights;
}

function collectAdvisorWarnings(context?: AIAdvisorContext) {
  const warnings: string[] = [];
  const missingPrices = context?.price_freshness?.missing_price_symbols ?? [];
  if (missingPrices.length) {
    warnings.push(`Missing current prices: ${missingPrices.join(", ")}.`);
  }
  warnings.push(...(context?.optional_context?.fundamentals_summary?.warnings ?? []));
  warnings.push(...(context?.optional_context?.peer_summary?.warnings ?? []));
  const fundamentalsStatus = context?.optional_context?.fundamentals_summary?.data_status;
  if (fundamentalsStatus?.warning) {
    warnings.push(fundamentalsStatus.warning);
  }
  const performanceStatus = context?.optional_context?.performance_history_summary?.data_status;
  if (performanceStatus?.warning) {
    warnings.push(performanceStatus.warning);
  }
  return Array.from(new Set(warnings));
}

function collectAdvisorSuggestions(context?: AIAdvisorContext) {
  const suggestions = ["Review concentration, allocation, risk, data coverage, peer context, and recent changes together."];
  if (context?.optional_context?.fundamentals_summary) {
    suggestions.push("Use the fundamentals page to inspect weighted metrics and missing symbol coverage.");
  }
  if (context?.optional_context?.peer_summary) {
    suggestions.push("Use the peers page to inspect static peer-set quality before relying on comparisons.");
  }
  if (context?.optional_context?.snapshot_change_summary) {
    suggestions.push("Use the changes page to compare saved portfolio snapshots.");
  }
  return suggestions;
}

function collectAdvisorLimitations(message: ChatMessage, context?: AIAdvisorContext) {
  const limitations = [
    "This is deterministic advisor output from backend context, not real-time or personalized investment advice.",
    "External AI calls are not active in this frontend flow."
  ];
  if (message.provider?.trim().toLowerCase() === "mock") {
    limitations.push("The provider is mock; treat the response as an explanatory demo response.");
  }
  const optionalContext = context?.optional_context;
  if (optionalContext?.performance_history_summary?.method) {
    limitations.push(`Performance context uses ${String(optionalContext.performance_history_summary.method).replaceAll("_", " ")} assumptions.`);
  }
  if (optionalContext?.peer_summary?.peer_set_quality) {
    limitations.push("Peer context can use static or sparse peer sets.");
  }
  return limitations;
}

function ContextMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}

function responseToAssistantMessage(response: AIAdvisorResponse): ChatMessage {
  return {
    role: "assistant",
    content: response.response,
    provider: response.provider,
    model: response.model,
    created_at: response.created_at,
    structuredResponse: response.structured_response,
    context: response.context
  };
}

function toChatMessage(message: AIMessageResponse): ChatMessage {
  return {
    role: message.role === "user" ? "user" : "assistant",
    content: message.content,
    provider: message.provider,
    model: message.model,
    structuredResponse: message.structured_response,
    created_at: message.created_at
  };
}

function formatCurrency(value: number | null, currency: string) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(value);
}

function formatPercent(value: number | null) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1
  }).format(value);
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}
