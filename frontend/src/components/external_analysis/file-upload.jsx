import { useState, useCallback } from "react"
import { Card} from "../ui/card"
import CardContent from "../ui/cardContent"
import  CardHeader from "../ui/cardHeader"
import  CardTitle from "../ui/cardTitle"
import  Button  from "../ui/Button"
import { Upload, FileSpreadsheet, X, CheckCircle } from "lucide-react"
import { cn } from "../../lib/utils"

export default function FileUpload() {
    
  const [files, setFiles] = useState([])
  const [isDragOver, setIsDragOver] = useState(false)

  const handleDragOver = useCallback((e) => {

    e.preventDefault()
    setIsDragOver(true)

  }, [])

  const handleDragLeave = useCallback((e) => {

    e.preventDefault()
    setIsDragOver(false)

  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    processFiles(droppedFiles)

  }, [])

  const handleFileSelect = useCallback((e) => {

    const selectedFiles = Array.from(e.target.files || [])
    processFiles(selectedFiles)

  }, [])

  const processFiles = (fileList) => {

    const newFiles = fileList.map((file) => ({
      name: file.name,
      size: file.size,
      type: file.type,
      status: "uploading",
      progress: 0,
    }))

    setFiles((prev) => [...prev, ...newFiles])

    // Simulate file processing
    newFiles.forEach((_, index) => {
      simulateFileProcessing(files.length + index)
    })
  }

  const simulateFileProcessing = (fileIndex) => {
    const interval = setInterval(() => {
      setFiles((prev) => {
        const updated = [...prev]
        const file = updated[fileIndex]

        if (!file) {
          clearInterval(interval)
          return prev
        }

        if (file.status === "uploading" && file.progress < 100) {
          file.progress += Math.random() * 20
          if (file.progress >= 100) {
            file.progress = 100
            file.status = "processing"
          }
        } else if (file.status === "processing") {
          setTimeout(() => {
            setFiles((prev) => {
              const updated = [...prev]
              if (updated[fileIndex]) {
                updated[fileIndex].status = "completed"
              }
              return updated
            })
          }, 2000)
          clearInterval(interval)
        }

        return updated
      })
    }, 200)
  }

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <Card className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-xl hover:shadow-2xl transition-all duration-300">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-3 text-slate-800">
          <div className="p-2 bg-gradient-to-br from-cyan-500 to-emerald-500 rounded-lg">
            <Upload className="h-5 w-5 text-white" />
          </div>
          Upload Datasheets
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div
          className={cn(
            "border-2 border-dashed rounded-xl p-10 text-center transition-all duration-300 group",
            isDragOver
              ? "border-cyan-400 bg-gradient-to-br from-cyan-50 to-emerald-50 scale-[1.02] shadow-lg"
              : "border-slate-300 hover:border-cyan-400 hover:bg-gradient-to-br hover:from-slate-50 hover:to-cyan-50/30 hover:shadow-md",
          )}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="space-y-6">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-cyan-100 to-emerald-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-lg">
              <FileSpreadsheet className="h-8 w-8 text-cyan-600" />
            </div>
            <div className="space-y-3">
              <p className="text-xl font-semibold text-slate-800">Drop your files here, or click to browse</p>
              <p className="text-slate-600">Supports Excel (.xlsx, .xls) and CSV files up to 10MB</p>
            </div>
            <Button
              onClick={() => document.getElementById("file-input")?.click()}
              className="bg-gradient-to-r from-cyan-500 to-emerald-500 text-white hover:from-cyan-600 hover:to-emerald-600 shadow-lg hover:shadow-xl transition-all duration-300 px-8 py-3 text-lg font-medium"
            >
              Choose Files
            </Button>
            <input
              id="file-input"
              type="file"
              multiple
              accept=".xlsx,.xls,.csv"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        </div>

        {files.length > 0 && (
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-800 text-lg">Uploaded Files</h4>
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-4 p-4 bg-gradient-to-r from-slate-50 to-white rounded-xl border border-slate-200/60 shadow-sm hover:shadow-md transition-all duration-300"
              >
                <div className="flex-1 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-800">{file.name}</span>
                    <div className="flex items-center gap-3">
                      {file.status === "completed" && (
                        <div className="flex items-center gap-2">
                          <CheckCircle className="h-5 w-5 text-emerald-500 animate-pulse" />
                          <span className="text-sm font-medium text-emerald-600">Complete</span>
                        </div>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(index)}
                        className="h-8 w-8 p-0 hover:bg-red-50 hover:text-red-500 transition-colors"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm text-slate-600">
                    <span>{formatFileSize(file.size)}</span>
                    <span className="capitalize font-medium">{file.status}</span>
                  </div>
                  {file.status !== "completed" && (
                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500 transition-all duration-300 ease-out"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
