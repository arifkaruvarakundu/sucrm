import { useState } from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../ui/card_selection"
import { Input } from "../ui/mappingform_input"
import { Label } from "../ui/mappingform_lable"
import { Button } from "../ui/mappingform_button"
import { Plus, Trash2 } from "lucide-react"
import api from "../../../api_config"
import { useNavigate } from "react-router-dom"

// Define analysis field options
const analysisFields = {
  order: [
    { key: "orderId", label: "Order ID" },
    { key: "orderDate", label: "Order Date" },
    { key: "quantity", label: "Quantity Ordered" },
    { key: "totalAmount", label: "Total Amount" },
    { key: "orderStatus", label: "Order Status" },
    { key: "customerName", label: "Customer Name" },
    { key: "customerPhone", label: "Customer Phone" },
  ],
  customer: [
    { key: "customerId", label: "Customer ID" },
    { key: "customerName", label: "Customer Name" },
    { key: "email", label: "Customer Email" },
    { key: "phone", label: "Customer Phone" },
    { key: "city", label: "Customer City" },
  ],
  product: [
    { key: "productId", label: "Product ID" },
    { key: "productName", label: "Product Name" },
    { key: "category", label: "Category" },
    { key: "price", label: "Unit Price" },
    { key: "quantity", label: "Quantity Available" },
  ],
}

export function ColumnMappingForm({ selectedAnalyses = [], onMappingSubmit }) {
  const [rows, setRows] = useState([{ id: 1, columnName: "", analysisField: "" }])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const navigate = useNavigate()
  // Get combined dropdown options
  const dropdownOptions = selectedAnalyses.flatMap((type) => analysisFields[type] || [])

  const handleAddRow = () => {
    setRows([...rows, { id: rows.length + 1, columnName: "", analysisField: "" }])
  }

  const handleRemoveRow = (id) => {
    setRows(rows.filter((r) => r.id !== id))
  }

  const handleChange = (id, field, value) => {
    setRows(rows.map((r) => (r.id === id ? { ...r, [field]: value } : r)))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const mapping = {}
      rows.forEach((r) => {
        if (r.analysisField && r.columnName) {
          mapping[r.analysisField] = r.columnName
        }
      })

      if (Object.keys(mapping).length === 0) {
        setError("Please map at least one column before submitting.")
        setLoading(false)
        return
      }

      const payload = { selected_analyses: selectedAnalyses, mapping }

      const response = await api.post("/column-mapping", payload)
      console.log("Mapping submitted:", response.data)
      setSuccess("✅ Mapping submitted successfully!")
      onMappingSubmit && onMappingSubmit(response.data)
      navigate("/dashboard")
    } catch (err) {
      console.error(err)
      setError("Failed to submit mapping. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  if (!selectedAnalyses.length) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-gray-500">
            Please select at least one analysis type before configuring column mappings.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card className="shadow-md">
        <CardHeader className="border-b pb-3">
          <CardTitle className="text-xl font-semibold text-gray-800">
            🧩 Column Mapping Setup
          </CardTitle>
          <CardDescription className="text-gray-600 mt-1">
            Enter your uploaded file’s column names and map them to the correct analysis fields below.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5 mt-4">
          {rows.map((row, idx) => (
            <div
              key={row.id}
              className="flex flex-col md:flex-row gap-4 items-end md:items-center bg-gray-50 p-4 rounded-xl border border-gray-200"
            >
              {/* Column Name Input */}
              <div className="flex-1 w-full">
                <Label htmlFor={`columnName-${row.id}`} className="text-sm font-medium">
                  Column {idx + 1}
                </Label>
                <Input
                  id={`columnName-${row.id}`}
                  value={row.columnName}
                  onChange={(e) => handleChange(row.id, "columnName", e.target.value)}
                  placeholder="e.g. order_date, customer_name, product_id..."
                  required
                />
              </div>

              {/* Dropdown Mapping */}
              <div className="flex-1 w-full">
                <Label htmlFor={`analysisField-${row.id}`} className="text-sm font-medium">
                  Map To
                </Label>
                <select
                  id={`analysisField-${row.id}`}
                  className="border border-gray-300 rounded-md p-2 w-full text-sm bg-white focus:ring-2 focus:ring-blue-400"
                  value={row.analysisField}
                  onChange={(e) => handleChange(row.id, "analysisField", e.target.value)}
                  required
                >
                  <option value="">Select analysis field</option>
                  {dropdownOptions.map((opt) => (
                    <option key={opt.key} value={opt.key}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                {rows.length > 1 && (
                  <Button
                    type="button"
                    variant="outline"
                    title="Remove this mapping"
                    onClick={() => handleRemoveRow(row.id)}
                    className="bg-red-50 hover:bg-red-100 text-red-600 px-3"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
                {/* {idx === rows.length - 1 && (
                  <Button
                    type="button"
                    variant="outline"
                    title="Add another mapping"
                    onClick={handleAddRow}
                    className="bg-blue-50 hover:bg-blue-100 text-blue-600 px-3"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                )} */}
              </div>
            </div>
          ))}

          {/* Add another row button (bottom) */}
          {rows.length > 0 && (
            <div className="flex justify-start">
              <Button
                type="button"
                variant="outline"
                onClick={handleAddRow}
                className="bg-blue-50 hover:bg-blue-100 text-blue-600 mt-2"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Another Column
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Feedback messages */}
      {error && <p className="text-red-500 text-sm font-medium">{error}</p>}
      {success && <p className="text-green-600 text-sm font-medium">{success}</p>}

      {/* Submit Button */}
      <div className="flex justify-end pt-4">
        <Button
          type="submit"
          size="lg"
          className="min-w-[220px] bg-blue-600 hover:bg-blue-700 text-white"
          disabled={loading}
        >
          {loading ? "Submitting..." : "Submit Mapping"}
        </Button>
      </div>
    </form>
  )
}
