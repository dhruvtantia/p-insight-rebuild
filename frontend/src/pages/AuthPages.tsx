import { zodResolver } from "@hookform/resolvers/zod";
import { LogIn, UserPlus } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { Button, Card, CardTitle, Input } from "../components/ui";

const authSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
});

type AuthValues = z.infer<typeof authSchema>;

export function LoginPage() {
  return <AuthForm mode="login" />;
}

export function SignupPage() {
  return <AuthForm mode="signup" />;
}

function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const form = useForm<AuthValues>({
    resolver: zodResolver(authSchema),
    defaultValues: { email: "", password: "" }
  });
  const isSignup = mode === "signup";

  return (
    <div className="mx-auto max-w-md py-8">
      <Card>
        <CardTitle>{isSignup ? "Create account" : "Log in"}</CardTitle>
        <p className="mt-2 text-sm text-slate-600">
          Production auth is deferred. This form preserves the future Supabase Auth or Clerk entry point.
        </p>
        <form className="mt-6 space-y-4" onSubmit={form.handleSubmit(() => undefined)}>
          <label className="block space-y-2">
            <span className="text-sm font-medium">Email</span>
            <Input type="email" placeholder="you@example.com" {...form.register("email")} />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-medium">Password</span>
            <Input type="password" placeholder="Minimum 8 characters" {...form.register("password")} />
          </label>
          <Button type="submit" className="w-full">
            {isSignup ? <UserPlus size={16} /> : <LogIn size={16} />}
            {isSignup ? "Create placeholder account" : "Continue with placeholder auth"}
          </Button>
        </form>
        <p className="mt-4 text-sm text-slate-600">
          {isSignup ? "Already have a placeholder account?" : "New to P-insight?"}{" "}
          <Link className="font-semibold text-accent" to={isSignup ? "/login" : "/signup"}>
            {isSignup ? "Log in" : "Sign up"}
          </Link>
        </p>
      </Card>
    </div>
  );
}
