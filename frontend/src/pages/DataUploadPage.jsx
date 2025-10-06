import FileUpload from "../components/external_analysis/file-upload"
import AnalysisResults  from "../components/external_analysis/analysis-results"
import Header from "../components/external_analysis/header"
import StatsOverview from "../components/external_analysis/stats-overview"

export default function ExternalDataPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/30">
      <Header />
      <main className="container mx-auto px-4 py-8 space-y-12">
        <div className="text-center space-y-6 py-12">
          <div className="space-y-4">
            <h1 className="text-5xl md:text-6xl font-bold text-balance bg-gradient-to-r from-slate-900 via-cyan-800 to-emerald-700 bg-clip-text text-transparent leading-tight">
              AI-Powered Datasheet Analysis
            </h1>
            <p className="text-xl md:text-2xl text-slate-600 max-w-3xl mx-auto text-pretty leading-relaxed">
              Upload your Excel or CSV files and get intelligent insights powered by advanced AI technology. Transform
              your data into actionable business intelligence.
            </p>
          </div>
          <div className="flex justify-center items-center gap-8 pt-6">
            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
            <div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse delay-75"></div>
            <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse delay-150"></div>
          </div>
        </div>

        <StatsOverview />

        <div className="grid lg:grid-cols-1 gap-8">
          <FileUpload />
          {/* <AnalysisResults /> */}
        </div>
      </main>
    </div>
  )
}
