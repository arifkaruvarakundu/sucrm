import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../ui/card_selection";
import { Checkbox } from "../ui/checkbox_selection";
import { Button } from "../ui/button_selection";
import { BarChart3, Package, Users } from "lucide-react";

export function DataTypeSelector({ onSelectionChange }) {
  const [selectedTypes, setSelectedTypes] = useState([]);
  const navigate = useNavigate();

  const dataOptions = [
    {
      id: "order",
      label: "Order Analysis Data",
      description: "Analyze order trends, revenue patterns, and sales performance",
      icon: BarChart3,
    },
    {
      id: "product",
      label: "Product Analysis Data",
      description: "Track product performance, inventory levels, and SKU metrics",
      icon: Package,
    },
    {
      id: "customer",
      label: "Customer Analysis Data",
      description: "Understand customer behavior, demographics, and lifetime value",
      icon: Users,
    },
  ];

  const handleToggle = (type) => {
    const newSelection = selectedTypes.includes(type)
      ? selectedTypes.filter((t) => t !== type)
      : [...selectedTypes, type];

    setSelectedTypes(newSelection);
    if (onSelectionChange) onSelectionChange(newSelection);
  };

  const handleContinue = () => {
    // Navigate to /mappingPage and pass state
    navigate("/mappingPage", { state: { selectedTypes } });
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-8">
      <div className="space-y-3">
        <h2 className="text-3xl font-bold text-foreground text-balance">
          What type of data did you upload?
        </h2>
        <p className="text-muted-foreground text-lg leading-relaxed">
          Select one or more data types to begin your analysis. You can choose multiple options if your dataset contains
          different types of information.
        </p>
      </div>

      <div className="space-y-4">
        {dataOptions.map((option) => {
          const Icon = option.icon;
          const isSelected = selectedTypes.includes(option.id);

          return (
            <Card
              key={option.id}
              className={`relative overflow-hidden transition-all duration-200 cursor-pointer hover:shadow-lg ${
                isSelected
                  ? "border-primary border-[3px] bg-card shadow-md"
                  : "border-border border-[3px] bg-card hover:border-primary/50"
              }`}
              onClick={() => handleToggle(option.id)}
            >
              <div className="p-6 flex items-start gap-4">
                <div className="flex-shrink-0 mt-1">
                  <Checkbox
                    id={option.id}
                    checked={isSelected}
                    onCheckedChange={() => handleToggle(option.id)}
                    className="h-6 w-6 border-2"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <div
                      className={`p-2 rounded-lg transition-colors ${
                        isSelected ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <label htmlFor={option.id} className="text-xl font-semibold text-foreground cursor-pointer">
                      {option.label}
                    </label>
                  </div>
                  <p className="text-muted-foreground leading-relaxed">{option.description}</p>
                </div>

                {isSelected && <div className="absolute top-0 right-0 w-16 h-16 -mr-8 -mt-8 bg-primary rotate-45" />}
              </div>
            </Card>
          );
        })}
      </div>

      <div className="flex items-center justify-between pt-4">
        <p className="text-sm text-muted-foreground">
          {selectedTypes.length === 0 && "Please select at least one data type"}
          {selectedTypes.length === 1 && "1 data type selected"}
          {selectedTypes.length > 1 && `${selectedTypes.length} data types selected`}
        </p>
        <Button
          onClick={handleContinue}
          disabled={selectedTypes.length === 0}
          size="lg"
          className="bg-accent hover:bg-accent/90 text-accent-foreground font-semibold px-8"
        >
          Continue
        </Button>
      </div>
    </div>
  );
}
