import { Bot, Clock, MessageSquare, Plus, Send, Sparkles, Upload } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Badge, Button, Card, CardTitle, EmptyState, ErrorState, LoadingState } from "../components/ui";
import { useAIAdvisor } from "../hooks/useAIAdvisor";
import { useAnalytics } from "../hooks/useAnalytics";
import { useAppStatus } from "../hooks/useAppStatus";
import { usePortfolios } from "../hooks/usePortfolios";
import type { AIAdvisorResponse, AIMessageResponse } from "../types/ai";
import type { Portfolio } from "../types/portfolio";

const SUGGESTED_QUESTIONS = [
  "Summarize my portfolio",
  "Where is my portfolio concentrated?",
  "What are my biggest risks?",
  "Explain my Sharpe ratio",
  "What data is missing?",
  "What changed since my last upload?"
];

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  provider?: string | null;
  created_at?: string;
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
            isLoading={advisor.generateSummary.isPending || advisor.askQuestion.isPending}
            question={question}
            onQuestionChange={setQuestion}
            onSummary={handleSummary}
            onSubmit={handleQuestionSubmit}
            disableActions={!selectedPortfolio?.id}
          />
        </main>

        <aside className="space-y-4">
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
  isLoading,
  question,
  onQuestionChange,
  onSummary,
  onSubmit,
  disableActions
}: {
  messages: ChatMessage[];
  aiProviderMode?: string;
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
          placeholder="Ask about concentration, missing data, performance, or risk..."
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

function ChatBubble({ message, aiProviderMode }: { message: ChatMessage; aiProviderMode?: string }) {
  const isUser = message.role === "user";
  const isMockAiResponse =
    !isUser && (message.provider?.trim().toLowerCase() === "mock" || aiProviderMode?.trim().toLowerCase() === "mock");
  return (
    <div className={isUser ? "self-end" : "self-start"}>
      <div className={["max-w-2xl rounded-md px-4 py-3 text-sm leading-6 shadow-sm", isUser ? "bg-accent text-white" : "bg-white text-slate-700"].join(" ")}>
        {isMockAiResponse ? (
          <div className="mb-2">
            <Badge tone="warning">Mock AI response</Badge>
          </div>
        ) : null}
        {message.content}
      </div>
      {message.created_at ? (
        <p className={["mt-1 text-xs text-slate-500", isUser ? "text-right" : ""].join(" ")}>{formatDateTime(message.created_at)}</p>
      ) : null}
    </div>
  );
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
    created_at: response.created_at
  };
}

function toChatMessage(message: AIMessageResponse): ChatMessage {
  return {
    role: message.role === "user" ? "user" : "assistant",
    content: message.content,
    provider: message.provider,
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
