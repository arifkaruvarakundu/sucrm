import { Card } from "../ui/card"
import CardContent  from "../ui/cardContent"
import { TrendingUp, Users, FileText, Zap } from "lucide-react"

const stats = [
  {
    icon: FileText,
    label: "Files Analyzed",
    value: "12,847",
    change: "+23%",
    changeType: "positive",
    gradient: "from-blue-500 to-cyan-500",
    bgGradient: "from-blue-50 to-cyan-50",
  },
  {
    icon: Users,
    label: "Active Users",
    value: "2,341",
    change: "+12%",
    changeType: "positive",
    gradient: "from-emerald-500 to-teal-500",
    bgGradient: "from-emerald-50 to-teal-50",
  },
  {
    icon: TrendingUp,
    label: "Insights Generated",
    value: "45,892",
    change: "+34%",
    changeType: "positive",
    gradient: "from-violet-500 to-purple-500",
    bgGradient: "from-violet-50 to-purple-50",
  },
  {
    icon: Zap,
    label: "Processing Speed",
    value: "2.3s",
    change: "-15%",
    changeType: "positive",
    gradient: "from-orange-500 to-red-500",
    bgGradient: "from-orange-50 to-red-50",
  },
]

export default function StatsOverview() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat, index) => (
        <Card
          key={index}
          className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-lg hover:shadow-xl transition-all duration-300 group overflow-hidden"
        >
          <CardContent className="p-6 relative">
            <div
              className={`absolute inset-0 bg-gradient-to-br ${stat.bgGradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}
            ></div>

            <div className="relative flex items-center justify-between">
              <div className="space-y-3">
                <p className="text-sm text-slate-600 font-medium">{stat.label}</p>
                <p className="text-3xl font-bold text-slate-800 group-hover:text-slate-900 transition-colors">
                  {stat.value}
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-emerald-600 font-semibold bg-emerald-100 px-2 py-1 rounded-full">
                    {stat.change}
                  </span>
                  <span className="text-xs text-slate-500">from last month</span>
                </div>
              </div>

              <div className="relative">
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} rounded-2xl blur-sm opacity-75 group-hover:opacity-100 transition-opacity duration-300`}
                ></div>
                <div
                  className={`relative p-4 bg-gradient-to-br ${stat.gradient} rounded-2xl shadow-lg group-hover:scale-110 transition-transform duration-300`}
                >
                  <stat.icon className="h-7 w-7 text-white" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
