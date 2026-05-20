import { Download, Save, ShieldAlert, Trash2, UserRound } from "lucide-react";

import { Badge, Button, Card, CardTitle, Input } from "../components/ui";

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <SettingsHeader />

      <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
        <Card>
          <div className="flex items-start gap-3">
            <UserRound className="mt-0.5 text-accent" size={22} />
            <div>
              <CardTitle>Profile</CardTitle>
              <p className="mt-2 text-sm leading-6 text-slate-600">Auth is still using the development demo user.</p>
            </div>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <Field label="Email">
              <Input value="demo@p-insight.local" disabled />
            </Field>
            <Field label="Display name">
              <Input value="Demo User" disabled />
            </Field>
          </div>
          <Button className="mt-5" disabled>
            <Save size={16} />
            Save profile later
          </Button>
        </Card>

        <Card>
          <CardTitle>Preferences</CardTitle>
          <div className="mt-5 grid gap-4">
            <Field label="Base currency preference">
              <select disabled className="h-10 rounded-md border border-line bg-surface px-3 text-sm text-slate-500">
                <option>INR</option>
              </select>
            </Field>
            <Field label="Default benchmark">
              <Input value="NIFTY50" disabled />
            </Field>
            <Field label="Risk-free rate assumption">
              <Input value="0.065" disabled />
            </Field>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            These assumptions are portfolio-level today. Account-level defaults will be added after auth is finalized.
          </p>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <div className="flex items-start justify-between gap-4">
            <div>
              <CardTitle>Data export</CardTitle>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Export reports and raw portfolio data are planned for a later reporting phase.
              </p>
            </div>
            <Badge>placeholder</Badge>
          </div>
          <Button className="mt-5" variant="secondary" disabled>
            <Download size={16} />
            Export data later
          </Button>
        </Card>

        <Card className="border-coral/30">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 text-coral" size={22} />
            <div>
              <CardTitle>Delete account</CardTitle>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Account deletion will be implemented with formal auth, audit logging, and data retention controls.
              </p>
            </div>
          </div>
          <Button className="mt-5 text-coral" variant="secondary" disabled>
            <Trash2 size={16} />
            Delete account later
          </Button>
        </Card>
      </div>
    </div>
  );
}

function SettingsHeader() {
  return (
    <section>
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Settings</p>
      <h1 className="mt-1 text-3xl font-semibold">Account settings</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
        Indian market defaults are visible as placeholders while auth and preference persistence are formalized.
      </p>
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-medium text-ink">{label}</span>
      {children}
    </label>
  );
}
