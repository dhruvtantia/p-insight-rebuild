import { CheckCircle2, Lightbulb, UploadCloud } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Badge, Button, Card, CardTitle, EmptyState, ErrorState, LoadingState, Table, Td, Th } from "../components/ui";
import { usePortfolios } from "../hooks/usePortfolios";
import { useUpload } from "../hooks/useUpload";
import { ApiError } from "../services/apiClient";
import type {
  ColumnMapping,
  ColumnMappingSuggestion,
  ConfirmUploadResponse,
  UploadJob,
  UploadRow,
  ValidateUploadResponse
} from "../types/upload";

const requiredFields = [
  { key: "symbol", label: "Symbol" },
  { key: "quantity", label: "Quantity" }
];

const optionalFields = [
  { key: "company_name", label: "Company Name" },
  { key: "average_cost", label: "Average Cost" },
  { key: "market_value", label: "Market Value" },
  { key: "currency", label: "Currency" },
  { key: "sector", label: "Sector" },
  { key: "asset_class", label: "Asset Class" },
  { key: "exchange", label: "Exchange" }
];

const sampleCsv = `Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange
RELIANCE,Reliance Industries Ltd,10,2850,28500,INR,Energy,Equity,NSE
TCS,Tata Consultancy Services Ltd,5,3800,19000,INR,Information Technology,Equity,NSE`;

export function UploadPage() {
  const portfolios = usePortfolios();
  const [selectedPortfolioId, setSelectedPortfolioId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadJobId, setUploadJobId] = useState<string | null>(null);
  const [mapping, setMapping] = useState<ColumnMapping>({});
  const [validationResult, setValidationResult] = useState<ValidateUploadResponse | null>(null);
  const [confirmResult, setConfirmResult] = useState<ConfirmUploadResponse | null>(null);
  const [step, setStep] = useState(1);
  const upload = useUpload(uploadJobId, selectedPortfolioId || null);

  useEffect(() => {
    if (!selectedPortfolioId && portfolios.data?.length) {
      setSelectedPortfolioId(portfolios.data[0].id);
    }
  }, [portfolios.data, selectedPortfolioId]);

  const uploadJob =
    validationResult?.upload_job ??
    upload.submitMapping.data?.upload_job ??
    upload.createUpload.data ??
    upload.uploadJob.data ??
    null;

  const canSubmitMapping = requiredFields.every((field) => mapping[field.key]);
  const invalidRows = validationResult?.rows.filter((row) => row.status === "invalid") ?? [];
  const warningRows = validationResult?.rows.filter((row) => row.warnings?.length) ?? [];
  const validRows = validationResult?.upload_job.valid_rows ?? 0;
  const fallbackMapping = useMemo(() => guessMapping(uploadJob?.detected_columns ?? []), [uploadJob?.detected_columns]);

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!portfolios.data?.length) {
    return (
      <div className="space-y-6">
        <UploadHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio before uploading holdings." />
        <Link to="/onboarding">
          <Button>Create portfolio</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <UploadHeader />
      <WizardProgress step={step} />

      <Card>
        <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Step 1: Select portfolio</span>
            <select
              className="h-10 rounded-md border border-line bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
              value={selectedPortfolioId}
              onChange={(event) => {
                setSelectedPortfolioId(event.target.value);
                resetUploadState();
              }}
            >
              {portfolios.data.map((portfolio) => (
                <option key={portfolio.id} value={portfolio.id}>
                  {portfolio.name}
                </option>
              ))}
            </select>
          </label>

          <div className="grid gap-2">
            <span className="text-sm font-medium text-ink">Sample CSV template</span>
            <div className="flex flex-wrap gap-2">
              <a
                href={`data:text/csv;charset=utf-8,${encodeURIComponent(sampleCsv)}`}
                download="p-insight-holdings-template.csv"
              >
                <Button type="button" variant="secondary">
                  Download template
                </Button>
              </a>
              <Badge>CSV or XLSX</Badge>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <CardTitle>Step 2: Upload CSV/XLSX</CardTitle>
        <div className="mt-4 grid gap-4">
          <input
            type="file"
            accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            className="block w-full rounded-md border border-line bg-white px-3 py-2 text-sm"
          />
          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              disabled={!selectedPortfolioId || !selectedFile || upload.createUpload.isPending}
              onClick={() => {
                if (!selectedPortfolioId || !selectedFile) return;
                upload.createUpload.mutate(
                  { targetPortfolioId: selectedPortfolioId, file: selectedFile },
                  {
                    onSuccess: (createdUploadJob) => {
                      setUploadJobId(createdUploadJob.id);
                      setMapping(guessMapping(createdUploadJob.detected_columns));
                      setValidationResult(null);
                      setConfirmResult(null);
                      setStep(3);
                    }
                  }
                );
              }}
            >
              <UploadCloud size={16} />
              {upload.createUpload.isPending ? "Uploading" : "Upload and detect columns"}
            </Button>
            {selectedFile ? <span className="self-center text-sm text-slate-600">{selectedFile.name}</span> : null}
          </div>
          {upload.createUpload.isError ? (
            <ErrorState title="Upload failed" detail={upload.createUpload.error.message} />
          ) : null}
        </div>
      </Card>

      {uploadJob ? (
        <Card>
          <CardTitle>Step 3: Preview detected rows</CardTitle>
          <div className="mt-4 grid gap-4">
            <UploadJobSummary uploadJob={uploadJob} />
            <PreviewTable rows={uploadJob.preview_rows} columns={uploadJob.detected_columns} />
          </div>
        </Card>
      ) : null}

      {uploadJob ? (
        <Card>
          <CardTitle>Step 4: Map columns</CardTitle>
          <p className="mt-2 text-sm text-slate-600">
            Map P-insight fields to the detected file columns. Indian symbols and quantity are required.
          </p>
          <MappingSuggestionsPanel
            isLoading={upload.mappingSuggestions.isLoading}
            isError={upload.mappingSuggestions.isError}
            error={upload.mappingSuggestions.error}
            suggestions={upload.mappingSuggestions.data?.suggestions ?? []}
            fallbackMapping={fallbackMapping}
            onAccept={(suggestion) =>
              setMapping((current) => ({
                ...current,
                [suggestion.target_field]: suggestion.source_column
              }))
            }
            onAcceptAll={(suggestions) =>
              setMapping((current) => ({
                ...current,
                ...mappingFromSuggestions(suggestions)
              }))
            }
            onUseFallback={() =>
              setMapping((current) => ({
                ...current,
                ...fallbackMapping
              }))
            }
          />
          <ColumnMappingForm
            detectedColumns={uploadJob.detected_columns}
            mapping={mapping}
            onChange={setMapping}
          />
          <div className="mt-4 flex flex-wrap gap-3">
            <Button
              type="button"
              disabled={!canSubmitMapping || upload.submitMapping.isPending}
              onClick={() => {
                upload.submitMapping.mutate(
                  { targetUploadJobId: uploadJob.id, mapping: compactMapping(mapping) },
                  { onSuccess: () => setStep(5) }
                );
              }}
            >
              {upload.submitMapping.isPending ? "Saving mapping" : "Save mapping"}
            </Button>
            {!canSubmitMapping ? (
              <span className="self-center text-sm text-coral">Map symbol and quantity before validation.</span>
            ) : null}
          </div>
          {upload.submitMapping.isError ? (
            <ErrorState title="Mapping failed" detail={upload.submitMapping.error.message} />
          ) : null}
        </Card>
      ) : null}

      {upload.submitMapping.data ? (
        <Card>
          <CardTitle>Step 5: Validate rows</CardTitle>
          <p className="mt-2 text-sm text-slate-600">
            Validation runs on the backend. Holdings are still not imported at this point.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Button
              type="button"
              disabled={upload.validate.isPending}
              onClick={() => {
                upload.validate.mutate(upload.submitMapping.data!.upload_job.id, {
                  onSuccess: (result) => {
                    setValidationResult(result);
                    setStep(6);
                  }
                });
              }}
            >
              <CheckCircle2 size={16} />
              {upload.validate.isPending ? "Validating" : "Validate upload"}
            </Button>
          </div>
          {upload.validate.isError ? <ErrorState title="Validation failed" detail={upload.validate.error.message} /> : null}
          {validationResult ? (
            <ValidationSummary validation={validationResult} invalidRows={invalidRows} warningRows={warningRows} />
          ) : null}
        </Card>
      ) : null}

      {validationResult ? (
        <Card>
          <CardTitle>Step 6: Confirm import</CardTitle>
          <p className="mt-2 text-sm text-slate-600">
            Confirm import creates holdings from valid rows only. Invalid rows and duplicate symbols are skipped.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Button
              type="button"
              disabled={validRows < 1 || upload.confirm.isPending || Boolean(confirmResult)}
              onClick={() => {
                upload.confirm.mutate(validationResult.upload_job.id, {
                  onSuccess: (result) => {
                    setConfirmResult(result);
                    setStep(7);
                  }
                });
              }}
            >
              {upload.confirm.isPending ? "Importing" : "Confirm import"}
            </Button>
            {validRows < 1 ? (
              <span className="self-center text-sm text-coral">At least one valid row is required to import.</span>
            ) : null}
          </div>
          {upload.confirm.isError ? <ErrorState title="Import failed" detail={upload.confirm.error.message} /> : null}
        </Card>
      ) : null}

      {confirmResult ? <SuccessScreen result={confirmResult} /> : null}
    </div>
  );

  function resetUploadState() {
    setSelectedFile(null);
    setUploadJobId(null);
    setMapping({});
    setValidationResult(null);
    setConfirmResult(null);
    setStep(1);
  }
}

function UploadHeader() {
  return (
    <section>
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Upload</p>
      <h1 className="mt-1 text-3xl font-semibold">Upload holdings wizard</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
        Stage CSV or XLSX rows, map columns, validate data, then confirm import. This page does not calculate analytics.
      </p>
    </section>
  );
}

function WizardProgress({ step }: { step: number }) {
  const labels = ["Portfolio", "File", "Preview", "Mapping", "Validate", "Confirm", "Success"];
  return (
    <div className="grid gap-2 sm:grid-cols-7">
      {labels.map((label, index) => {
        const current = index + 1;
        return (
          <div
            key={label}
            className={`rounded-md border px-3 py-2 text-center text-xs font-semibold ${
              current <= step ? "border-accent bg-accent text-white" : "border-line bg-white text-slate-500"
            }`}
          >
            {current}. {label}
          </div>
        );
      })}
    </div>
  );
}

function UploadJobSummary({ uploadJob }: { uploadJob: UploadJob }) {
  return (
    <div className="grid gap-3 sm:grid-cols-4">
      <Summary label="Status" value={uploadJob.status} />
      <Summary label="Rows" value={String(uploadJob.total_rows)} />
      <Summary label="Valid" value={String(uploadJob.valid_rows)} />
      <Summary label="Invalid" value={String(uploadJob.invalid_rows)} />
    </div>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{label}</p>
      <p className="mt-1 text-base font-semibold text-ink">{value}</p>
    </div>
  );
}

function PreviewTable({ rows, columns }: { rows: Array<Record<string, unknown>>; columns: string[] }) {
  if (!rows.length) {
    return <EmptyState title="No preview rows" detail="The upload parsed columns but has no previewable rows." />;
  }
  return (
    <Table>
      <thead>
        <tr>
          {columns.map((column) => (
            <Th key={column}>{column}</Th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={index}>
            {columns.map((column) => (
              <Td key={column}>{String(row[column] ?? "")}</Td>
            ))}
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

function MappingSuggestionsPanel({
  isLoading,
  isError,
  error,
  suggestions,
  fallbackMapping,
  onAccept,
  onAcceptAll,
  onUseFallback
}: {
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  suggestions: ColumnMappingSuggestion[];
  fallbackMapping: ColumnMapping;
  onAccept: (suggestion: ColumnMappingSuggestion) => void;
  onAcceptAll: (suggestions: ColumnMappingSuggestion[]) => void;
  onUseFallback: () => void;
}) {
  const hasFallback = Object.keys(fallbackMapping).length > 0;
  const isFeatureDisabled = error instanceof ApiError && error.code === "feature_disabled";

  if (isLoading) {
    return (
      <div className="mt-4 flex items-center gap-3 rounded-md border border-line bg-surface px-4 py-3 text-sm text-slate-600">
        <Lightbulb className="text-accent" size={18} />
        Loading mapping suggestions
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mt-4 rounded-md border border-line bg-surface p-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-ink">
              {isFeatureDisabled ? "Mapping suggestions are not enabled" : "Mapping suggestions unavailable"}
            </p>
            <p className="mt-1 text-sm text-slate-600">
              {isFeatureDisabled
                ? "Manual column mapping is still available for this upload."
                : error?.message ?? "Continue by mapping columns manually."}
            </p>
          </div>
          {hasFallback ? (
            <Button type="button" variant="secondary" onClick={onUseFallback}>
              Use local matches
            </Button>
          ) : null}
        </div>
      </div>
    );
  }

  if (!suggestions.length) {
    return (
      <div className="mt-4 rounded-md border border-dashed border-line bg-white p-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-ink">No mapping suggestions found</p>
            <p className="mt-1 text-sm text-slate-600">Choose columns manually or use local column-name matches.</p>
          </div>
          {hasFallback ? (
            <Button type="button" variant="secondary" onClick={onUseFallback}>
              Use local matches
            </Button>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 space-y-3 rounded-md border border-line bg-surface p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-ink">Suggested mappings</p>
          <p className="mt-1 text-sm text-slate-600">
            Suggestions are not saved until you accept or edit them and then save the mapping.
          </p>
        </div>
        <Button type="button" variant="secondary" onClick={() => onAcceptAll(suggestions)}>
          Accept all suggestions
        </Button>
      </div>
      <Table>
        <thead>
          <tr>
            <Th>P-insight field</Th>
            <Th>Detected column</Th>
            <Th>Confidence</Th>
            <Th>Reason</Th>
            <Th>Action</Th>
          </tr>
        </thead>
        <tbody>
          {suggestions.map((suggestion) => (
            <tr key={`${suggestion.target_field}-${suggestion.source_column}`}>
              <Td>{labelForField(suggestion.target_field)}</Td>
              <Td>{suggestion.source_column}</Td>
              <Td>
                <Badge tone={suggestion.confidence >= 0.9 ? "success" : "warning"}>
                  {Math.round(suggestion.confidence * 100)}%
                </Badge>
              </Td>
              <Td>{suggestion.reason}</Td>
              <Td>
                <Button type="button" variant="secondary" onClick={() => onAccept(suggestion)}>
                  Accept
                </Button>
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
}

function ColumnMappingForm({
  detectedColumns,
  mapping,
  onChange
}: {
  detectedColumns: string[];
  mapping: ColumnMapping;
  onChange: (mapping: ColumnMapping) => void;
}) {
  const fields = [
    ...requiredFields.map((field) => ({ ...field, required: true })),
    ...optionalFields.map((field) => ({ ...field, required: false }))
  ];

  return (
    <div className="mt-4 grid gap-3 md:grid-cols-2">
      {fields.map((field) => (
        <label key={field.key} className="grid gap-2">
          <span className="text-sm font-medium text-ink">
            {field.label} {field.required ? <span className="text-coral">*</span> : null}
          </span>
          <select
            className="h-10 rounded-md border border-line bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
            value={mapping[field.key] ?? ""}
            onChange={(event) => {
              onChange({
                ...mapping,
                [field.key]: event.target.value
              });
            }}
          >
            <option value="">Do not map</option>
            {detectedColumns.map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
        </label>
      ))}
    </div>
  );
}

function ValidationSummary({
  validation,
  invalidRows,
  warningRows
}: {
  validation: ValidateUploadResponse;
  invalidRows: UploadRow[];
  warningRows: UploadRow[];
}) {
  return (
    <div className="mt-4 space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <Summary label="Valid rows" value={String(validation.upload_job.valid_rows)} />
        <Summary label="Invalid rows" value={String(validation.upload_job.invalid_rows)} />
        <Summary label="Total rows" value={String(validation.upload_job.total_rows)} />
      </div>

      {invalidRows.length ? (
        <Table>
          <thead>
            <tr>
              <Th>Row</Th>
              <Th>Symbol</Th>
              <Th>Errors</Th>
            </tr>
          </thead>
          <tbody>
            {invalidRows.map((row) => (
              <tr key={row.id}>
                <Td>{row.row_number}</Td>
                <Td>{String(row.mapped_data.symbol ?? "--")}</Td>
                <Td className="text-coral">{row.validation_errors.join("; ")}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        <Badge tone="success">All rows are valid</Badge>
      )}

      {warningRows.length ? (
        <div className="space-y-2">
          <p className="text-sm font-semibold text-ink">Validation warnings</p>
          <Table>
            <thead>
              <tr>
                <Th>Row</Th>
                <Th>Symbol</Th>
                <Th>Warnings</Th>
              </tr>
            </thead>
            <tbody>
              {warningRows.map((row) => (
                <tr key={row.id}>
                  <Td>{row.row_number}</Td>
                  <Td>{String(row.mapped_data.symbol ?? "--")}</Td>
                  <Td className="text-amber-700">{row.warnings.join("; ")}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : null}
    </div>
  );
}

function SuccessScreen({ result }: { result: ConfirmUploadResponse }) {
  return (
    <Card>
      <CardTitle>Step 7: Import complete</CardTitle>
      <div className="mt-4 grid gap-3 sm:grid-cols-5">
        <Summary label="Status" value={result.status.replace("_", " ")} />
        <Summary label="Imported" value={String(result.imported_count)} />
        <Summary label="Skipped" value={String(result.skipped_count)} />
        <Summary label="Invalid" value={String(result.invalid_count)} />
        <Summary label="Duplicates" value={String(result.duplicate_count)} />
      </div>
      {result.warnings.length ? (
        <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-800">Import warnings</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-800">
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {result.rejected_row_reasons.length ? (
        <div className="mt-4 space-y-2">
          <p className="text-sm font-semibold text-ink">Rejected rows</p>
          <Table>
            <thead>
              <tr>
                <Th>Row</Th>
                <Th>Symbol</Th>
                <Th>Reasons</Th>
              </tr>
            </thead>
            <tbody>
              {result.rejected_row_reasons.map((row) => (
                <tr key={`${row.row_number}-${row.symbol ?? "unknown"}`}>
                  <Td>{row.row_number}</Td>
                  <Td>{row.symbol ?? "--"}</Td>
                  <Td className="text-coral">{row.reasons.join("; ")}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : (
        <div className="mt-4">
          <Badge tone="success">No rejected rows</Badge>
        </div>
      )}
      <div className="mt-5 flex flex-wrap gap-3">
        <Link to="/holdings">
          <Button>View holdings</Button>
        </Link>
        <Link to="/dashboard">
          <Button variant="secondary">Go to dashboard</Button>
        </Link>
      </div>
    </Card>
  );
}

function compactMapping(mapping: ColumnMapping) {
  return Object.fromEntries(Object.entries(mapping).filter(([, value]) => value));
}

function mappingFromSuggestions(suggestions: ColumnMappingSuggestion[]): ColumnMapping {
  return Object.fromEntries(suggestions.map((suggestion) => [suggestion.target_field, suggestion.source_column]));
}

function labelForField(field: string) {
  const label = [...requiredFields, ...optionalFields].find((candidate) => candidate.key === field)?.label;
  return label ?? field.replace(/_/g, " ");
}

function guessMapping(columns: string[]): ColumnMapping {
  const guesses: Record<string, string[]> = {
    symbol: ["symbol", "ticker", "security", "instrument"],
    company_name: ["company", "company name", "name"],
    quantity: ["quantity", "shares", "units"],
    average_cost: ["average cost", "avg cost", "cost basis", "average price"],
    market_value: ["market value", "value"],
    currency: ["currency", "ccy"],
    sector: ["sector"],
    asset_class: ["asset class", "class"],
    exchange: ["exchange"]
  };

  const normalizedColumns = columns.map((column) => ({ raw: column, normalized: column.trim().toLowerCase() }));
  const mapping: ColumnMapping = {};
  for (const [field, aliases] of Object.entries(guesses)) {
    const match = normalizedColumns.find((column) => aliases.includes(column.normalized));
    if (match) {
      mapping[field] = match.raw;
    }
  }
  return mapping;
}
