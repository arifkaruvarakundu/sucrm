import { useLocation } from "react-router-dom";
import { ColumnMappingForm } from "../components/external_analysis/column-mapping-form";

export default function MappingPage() {
  const location = useLocation();
  const selectedAnalyses = location.state?.selectedTypes || [];

  const handleMappingSubmit = (mapping) => {
    console.log("Mapping submitted:", mapping);
    // Send mapping to backend
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Map Your Data Columns</h1>
      <ColumnMappingForm selectedAnalyses={selectedAnalyses} onMappingSubmit={handleMappingSubmit} />
    </div>
  );
}

