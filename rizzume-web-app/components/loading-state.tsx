"use client"

export function LoadingState() {
  return (
    <div className="min-h-screen py-12 px-4 bg-background flex items-center justify-center">
      <div className="max-w-2xl w-full space-y-8 animate-in fade-in duration-700">
        {/* Loading bar */}
        <div className="h-1 bg-muted/30 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full"
            style={{
              animation: "progress 2s ease-in-out infinite",
            }}
          />
        </div>

        {/* Loading content */}
        <div className="text-center space-y-3">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground">Analyzing your resume…</h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            We're matching your experience to the job description and collecting evidence from your resume.
          </p>
        </div>

        {/* Skeleton cards */}
        <div className="space-y-3 pt-8">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-3 p-4 rounded-lg border border-border/50 bg-card/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <div className="h-6 w-20 bg-muted/50 rounded animate-pulse" />
                  <div className="h-6 w-16 bg-muted/50 rounded animate-pulse" />
                </div>
                <div className="h-6 w-12 bg-muted/50 rounded animate-pulse" />
              </div>
              <div className="h-4 bg-muted/50 rounded animate-pulse w-full" />
              <div className="h-4 bg-muted/50 rounded animate-pulse w-5/6" />
            </div>
          ))}
        </div>

        <style jsx>{`
          @keyframes progress {
            0% {
              width: 0%;
            }
            50% {
              width: 100%;
            }
            100% {
              width: 100%;
            }
          }
        `}</style>
      </div>
    </div>
  )
}
