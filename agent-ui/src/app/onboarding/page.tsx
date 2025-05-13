import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { PlusCircle, FolderOpen } from "lucide-react"
import { AnimatedGridPattern } from "@/components/magicui/animated-grid-pattern"

export default function Home() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 text-zinc-100 p-4 overflow-hidden">
      <AnimatedGridPattern
        className="absolute inset-0 opacity-40 dark:opacity-25"
        width={30}
        height={30}
        numSquares={70}
        maxOpacity={0.3}
        duration={5}
        strokeDasharray={2}
      />
      <div className="relative w-full max-w-4xl mx-auto rounded-2xl border border-zinc-800 bg-zinc-900/90 p-8 shadow-xl backdrop-blur-sm">
        <div className="flex flex-col items-center justify-center space-y-16 py-8">
          <div className="text-center space-y-4 animate-fade-in">
            <h1 className="text-4xl md:text-5xl font-bold text-zinc-100">
              Welcome to <span className="text-red-500">Deriv AI Hub</span>
            </h1>
            <p className="text-zinc-400 max-w-md mx-auto">Your gateway to building and managing powerful AI engines</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl animate-fade-in-up">
            <Card className="group border-zinc-800 bg-zinc-900 hover:bg-zinc-800 transition-all duration-300 shadow-lg hover:shadow-red-900/10">
              <a href="http://localhost:3000/projects/new" className="block p-6">
                <div className="flex flex-col items-center text-center space-y-5">
                  <div className="p-3 rounded-full bg-zinc-800 group-hover:bg-red-950/40 transition-colors">
                    <PlusCircle className="w-8 h-8 text-red-500" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-zinc-100 group-hover:text-red-400 transition-colors">
                      Build an AI Engine
                    </h2>
                    <p className="mt-2 text-sm text-zinc-400">Visit the agent playground for building a new agent orchestration</p>
                  </div>
                  <Button
                    variant="outline"
                    className="mt-2 border-zinc-700 text-zinc-300 hover:bg-red-950/30 hover:text-red-300 hover:border-red-800"
                  >
                    Get Started
                  </Button>
                </div>
              </a>
            </Card>

            <Card className="group border-zinc-800 bg-zinc-900 hover:bg-zinc-800 transition-all duration-300 shadow-lg hover:shadow-red-900/10">
              <Link href="/dashboard" className="block p-6">
                <div className="flex flex-col items-center text-center space-y-5">
                  <div className="p-3 rounded-full bg-zinc-800 group-hover:bg-red-950/40 transition-colors">
                    <FolderOpen className="w-8 h-8 text-red-500" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-zinc-100 group-hover:text-red-400 transition-colors">
                      Visit Existing AI Engines
                    </h2>
                    <p className="mt-2 text-sm text-zinc-400">Visit the existing AI engines built by the teams at Deriv</p>
                  </div>
                  <Button
                    variant="outline"
                    className="mt-2 border-zinc-700 text-zinc-300 hover:bg-red-950/30 hover:text-red-300 hover:border-red-800"
                  >
                    Explore Engines
                  </Button>
                </div>
              </Link>
            </Card>
          </div>

          <div className="flex justify-center mt-8 animate-fade-in">
            <Button variant="ghost" className="text-zinc-500 hover:text-red-400 hover:bg-red-950/20 text-sm">
              Looking for help? Check our documentation
            </Button>
          </div>
        </div>
      </div>
    </main>
  )
}
