"use client";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, LayoutDashboard, LogOut } from "lucide-react";
import Link from "next/link";

function HomeContent() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-background flex flex-col item-center justify-center">
      {/* Simple Header */}

      <header className="w-full px-6 md:px-12 sticky top-0 z-50 flex h-16 items-center justify-between border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center gap-2 font-bold">
          <FileText className="h-6 w-6" />
          <span>Rizzume</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground hidden sm:inline-block">
            {user?.email}
          </span>
          <Button variant="ghost" size="sm" onClick={logout}>
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full px-6 md:px-12 flex flex-1 flex-col items-center justify-center py-20">
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl mb-4">
            Hello {user?.name}
          </h1>
          <p className="text-xl text-muted-foreground max-w-[600px]">
            Select an action to continue.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-7xl">
          {/* Action 1: Start Scoring */}
          <Link href="/score" className="group">
            <Card className="h-full transition-all hover:border-primary hover:shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-2xl group-hover:text-primary">
                  <FileText className="h-8 w-8" />
                  Start Scoring
                </CardTitle>
                <CardDescription>
                  Analyze resumes against job descriptions instantly.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                  <li>Multi-select Resumes</li>
                  <li>Paste or Upload JDs</li>
                  <li>Get Detailed AI Scores</li>
                </ul>
              </CardContent>
            </Card>
          </Link>

          {/* Action 2: Go to Dashboard */}
          <Link href="/dashboard/resumes" className="group">
            <Card className="h-full transition-all hover:border-primary hover:shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-2xl group-hover:text-primary">
                  <LayoutDashboard className="h-8 w-8" />
                  Go to Dashboard
                </CardTitle>
                <CardDescription>
                  Manage your uploaded assets and history.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                  <li>View Resume Repository</li>
                  <li>Manage Job Descriptions</li>
                  <li>Review Score History</li>
                </ul>
              </CardContent>
            </Card>
          </Link>
        </div>
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <ProtectedRoute>
      <HomeContent />
    </ProtectedRoute>
  );
}
