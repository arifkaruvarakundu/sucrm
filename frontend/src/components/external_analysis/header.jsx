import Button from "../ui/Button"
import { BarChart3, Brain, FileSpreadsheet } from "lucide-react"
import { useSelector } from "react-redux"
import { Link } from "react-router-dom";

export default function Header() {
const isAuthenticated = useSelector((state) => state.auth.isAuthenticated)

  return (
    <header className="border-b border-slate-200/60 bg-white/80 backdrop-blur-md sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500 to-emerald-500 rounded-xl blur-sm opacity-75"></div>
                <div className="relative flex items-center gap-2 bg-gradient-to-br from-cyan-500 to-emerald-500 p-3 rounded-xl shadow-lg">
                  <Brain className="h-6 w-6 text-white" />
                  <FileSpreadsheet className="h-5 w-5 text-white/90" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                  DataInsight AI
                </h1>
                <p className="text-sm text-slate-500 font-medium">Intelligent Data Analysis</p>
              </div>
            </div>
          </div>

          <nav className="flex items-center gap-3">
            { isAuthenticated ? (
              <>
            <Link to="/dashboard">
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-600 hover:text-slate-800 hover:bg-slate-100/80 transition-all duration-200"
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              Dashboard
            </Button>
            </Link>
            </>
          ) : (
            <>
            <Link to = "/signin">
            <Button
              size="sm"
              className="bg-gradient-to-r from-cyan-500 to-emerald-500 text-white hover:from-cyan-600 hover:to-emerald-600 shadow-lg hover:shadow-xl transition-all duration-300 px-6"
            >
              SignIn
            </Button>
            </Link>
            <Link to = "/register">
            <Button
              size="sm"
              className="bg-gradient-to-r from-cyan-500 to-emerald-500 text-white hover:from-cyan-600 hover:to-emerald-600 shadow-lg hover:shadow-xl transition-all duration-300 px-6"
            >
              Register
            </Button>
            </Link>
            </>
          )}
          </nav>
        </div>
      </div>
    </header>
  )
}
