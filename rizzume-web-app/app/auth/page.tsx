"use client";

import { Suspense, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { LoginForm } from "@/components/auth/login-form";
import { SignupForm } from "@/components/auth/signup-form";
import { ForgotPasswordForm } from "@/components/auth/forgot-password-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Command } from "lucide-react";

function AuthContent() {
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  const view = searchParams.get("view") || "login";

  // Reverse Protection: Redirect to Home if logged in
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return null; // Or a spinner
  }

  // If authenticated, we render null while redirecting
  if (isAuthenticated) {
    return null;
  }

  // View Logic
  let title = "Welcome back";
  let description = "Enter your credentials to sign in to your account";
  let component = <LoginForm />;

  if (view === "signup") {
    title = "Create an account";
    description = "Enter your email below to create your account";
    component = <SignupForm />;
  } else if (view === "forgot-password") {
    title = "Forgot Password";
    description = "Recover your account";
    component = <ForgotPasswordForm />;
  }

  const showHeader = view !== "forgot-password";

  return (
    <div className="min-h-screen w-full lg:grid lg:grid-cols-2">
      {/* Left Column: Branding & Aesthetic */}
      <div className="relative hidden h-full flex-col bg-zinc-900 p-10 text-white lg:flex dark:border-r">
        {/* Background Pattern (Optional aesthetic touch) */}
        <div className="absolute inset-0 bg-zinc-900" />
        <div className="absolute inset-0 bg-[url('/grid-pattern.svg')] opacity-10" /> {/* Suggestion: Add a subtle texture */}

        {/* Logo / Brand */}
        <div className="relative z-20 flex items-center text-lg font-medium tracking-tight">
          <Command className="mr-2 h-6 w-6" />
          Rizzume
        </div>

        {/* Quote / Testimonial */}
        <div className="relative z-20 mt-auto">
          <blockquote className="space-y-2 border-l-2 border-zinc-700 pl-4">
            <p className="text-lg italic text-zinc-300">
              &ldquo;See how good you can Rizz out the JD.&rdquo;
            </p>
            <footer className="text-sm text-zinc-500">– The Team</footer>
          </blockquote>
        </div>
      </div>

      {/* Right Column: Form / Content */}
      <div className="flex h-full items-center justify-center p-4 lg:p-8 bg-background">
        <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[350px]">

          {/* We remove the Card border/shadow on mobile for a cleaner 'app-like' feel, 
              but keep structural padding. */}
          <Card className="border-0 shadow-none bg-transparent">
            {showHeader && (
              <CardHeader className="text-center px-0">
                <CardTitle className="text-2xl font-semibold tracking-tight">
                  {title}
                </CardTitle>
                <CardDescription className="text-sm text-muted-foreground">
                  {description}
                </CardDescription>
              </CardHeader>
            )}
            <CardContent className="px-0">
              {component}
            </CardContent>
          </Card>

          {/* Optional Footer Links area */}
          <p className="px-8 text-center text-sm text-muted-foreground">
            By clicking continue, you agree to our{" "}
            <a href="/terms" className="underline underline-offset-4 hover:text-primary">
              Terms
            </a>{" "}
            and{" "}
            <a href="/privacy" className="underline underline-offset-4 hover:text-primary">
              Privacy Policy
            </a>
            .
          </p>
        </div>
      </div>
    </div>
  );
}

export default function AuthPage() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center">Loading...</div>}>
      <AuthContent />
    </Suspense>
  );
}
