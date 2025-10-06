import { DataTypeSelector } from "../components/external_analysis/data-selection"
import { useState } from "react"

export default function Home() {
  const [selectedTypes, setSelectedTypes] = useState([])

  const handleSelectionChange = (types) => {
    setSelectedTypes(types)
    console.log("[v0] Selected data types:", types)
  }

  const handleContinue = (types) => {
    console.log("[v0] Continuing with data types:", types)
    alert(`You selected: ${types.map((t) => t.charAt(0).toUpperCase() + t.slice(1)).join(", ")} Analysis Data`)
  }

  return (
    <main className="min-h-screen bg-background py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-12 text-center space-y-2">
          <div className="inline-block px-4 py-1 bg-primary/10 text-primary text-sm font-semibold rounded-full mb-4">
            STEP 2: SELECT DATA TYPE
          </div>
          <h1 className="text-4xl font-bold text-foreground">Data Upload Configuration</h1>
        </div>

        <DataTypeSelector
          onSelectionChange={handleSelectionChange}
          onContinue={handleContinue}
        />
      </div>
    </main>
  )
}
