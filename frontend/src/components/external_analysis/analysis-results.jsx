// import React, { useCallback, useMemo, useState } from 'react'
// import axios from 'axios'
// import API_BASE_URL from '../../api_config'

// function inferDelimiter(headerLine) {
//   const candidateDelimiters = [',', ';', '\t', '|']
//   let best = ','
//   let bestCount = -1
//   candidateDelimiters.forEach(delimiter => {
//     const count = headerLine.split(delimiter).length
//     if (count > bestCount) {
//       best = delimiter
//       bestCount = count
//     }
//   })
//   return best
// }

// function parseCsvText(csvText) {
//   const lines = csvText.replace(/\r\n?/g, '\n').split('\n').filter(line => line.length > 0)
//   if (lines.length === 0) return { headers: [], rows: [] }

//   const delimiter = inferDelimiter(lines[0])

//   const parseLine = (line) => {
//     const values = []
//     let current = ''
//     let insideQuotes = false
//     for (let i = 0; i < line.length; i++) {
//       const char = line[i]
//       if (char === '"') {
//         if (insideQuotes && line[i + 1] === '"') {
//           current += '"'
//           i++
//         } else {
//           insideQuotes = !insideQuotes
//         }
//       } else if (char === delimiter && !insideQuotes) {
//         values.push(current)
//         current = ''
//       } else {
//         current += char
//       }
//     }
//     values.push(current)
//     return values
//   }

//   const headers = parseLine(lines[0]).map(h => h.trim())
//   const rows = []
//   for (let i = 1; i < lines.length; i++) {
//     const cols = parseLine(lines[i])
//     const row = {}
//     headers.forEach((h, idx) => {
//       row[h || `col_${idx + 1}`] = (cols[idx] ?? '').trim()
//     })
//     rows.push(row)
//   }
//   return { headers, rows }
// }

// function computeNumericSummaries(headers, rows) {
//   const summaries = {}
//   headers.forEach(header => {
//     let count = 0
//     let sum = 0
//     let min = Number.POSITIVE_INFINITY
//     let max = Number.NEGATIVE_INFINITY
//     rows.forEach(row => {
//       const value = row[header]
//       const numeric = typeof value === 'number' ? value : Number(String(value).replace(/,/g, ''))
//       if (!Number.isNaN(numeric) && String(value).length > 0) {
//         count += 1
//         sum += numeric
//         if (numeric < min) min = numeric
//         if (numeric > max) max = numeric
//       }
//     })
//     if (count > 0) {
//       summaries[header] = {
//         count,
//         mean: sum / count,
//         min,
//         max
//       }
//     }
//   })
//   return summaries
// }

// const dropzoneStyle = {
//   border: '2px dashed rgba(0,0,0,0.15)',
//   borderRadius: '12px',
//   padding: '24px',
//   background: 'var(--main-bg)',
//   textAlign: 'center',
//   cursor: 'pointer'
// }

// export default function AnalyseExternalData() {
//   const [fileName, setFileName] = useState('')
//   const [headers, setHeaders] = useState([])
//   const [rows, setRows] = useState([])
//   const [errorMessage, setErrorMessage] = useState('')
//   const [isDragging, setIsDragging] = useState(false)
//   const [selectedFile, setSelectedFile] = useState(null)

//   // Backend analysis state
//   const [question, setQuestion] = useState('')
//   const [apiLoading, setApiLoading] = useState(false)
//   const [apiError, setApiError] = useState('')
//   const [serverSummary, setServerSummary] = useState(null)
//   const [serverAnalysis, setServerAnalysis] = useState(null)

//   const handleParsed = useCallback((text) => {
//     try {
//       const { headers, rows } = parseCsvText(text)
//       setHeaders(headers)
//       setRows(rows)
//       setErrorMessage('')
//     } catch (err) {
//       setErrorMessage('Failed to parse CSV. Please check the file and try again.')
//       setHeaders([])
//       setRows([])
//     }
//   }, [])

//   const onFileSelected = useCallback((file) => {
//     if (!file) return
//     setFileName(file.name)
//     setSelectedFile(file)
//     const reader = new FileReader()
//     reader.onload = (e) => {
//       const text = e.target?.result || ''
//       handleParsed(String(text))
//     }
//     reader.onerror = () => setErrorMessage('File read error. Please try again.')
//     reader.readAsText(file)
//   }, [handleParsed])

//   const onInputChange = useCallback((event) => {
//     const file = event.target.files?.[0]
//     onFileSelected(file)
//   }, [onFileSelected])

//   const onDrop = useCallback((event) => {
//     event.preventDefault()
//     setIsDragging(false)
//     const file = event.dataTransfer.files?.[0]
//     if (file) onFileSelected(file)
//   }, [onFileSelected])

//   const onDragOver = useCallback((event) => {
//     event.preventDefault()
//     setIsDragging(true)
//   }, [])

//   const onDragLeave = useCallback(() => setIsDragging(false), [])

//   const clearData = useCallback(() => {
//     setFileName('')
//     setHeaders([])
//     setRows([])
//     setErrorMessage('')
//     setSelectedFile(null)
//     setQuestion('')
//     setApiLoading(false)
//     setApiError('')
//     setServerSummary(null)
//     setServerAnalysis(null)
//   }, [])

//   const numericSummaries = useMemo(() => computeNumericSummaries(headers, rows), [headers, rows])

//   const previewRows = useMemo(() => rows.slice(0, 50), [rows])

//   const uploadToServer = useCallback(async () => {
//     if (!selectedFile) return
//     try {
//       setApiLoading(true)
//       setApiError('')
//       setServerSummary(null)
//       setServerAnalysis(null)

//       const formData = new FormData()
//       formData.append('file', selectedFile)
//       if (question && question.trim().length > 0) {
//         formData.append('question', question.trim())
//       }

//       const res = await axios.post(`${API_BASE_URL}/csv/analyze`, formData, {
//         headers: { 'Content-Type': 'multipart/form-data' }
//       })

//       setServerSummary(res.data?.summary || null)
//       setServerAnalysis(res.data?.analysis || null)
//     } catch (err) {
//       setApiError('Analysis request failed. Please ensure backend is running and try again.')
//     } finally {
//       setApiLoading(false)
//     }
//   }, [selectedFile, question])

//   return (
//     <div>
//       <div className="page-header">Analyse External Data</div>

//       <div className="card">
//         <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
//           <input
//             id="csv-input"
//             type="file"
//             accept=".csv,text/csv"
//             onChange={onInputChange}
//           />
//           {fileName ? <div style={{ opacity: 0.8 }}>{fileName}</div> : null}
//           {fileName ? (
//             <button className="btn" onClick={clearData} style={{ padding: '8px 12px', borderRadius: 8, background: 'var(--second-bg)' }}>
//               Clear
//             </button>
//           ) : null}
//         </div>

//         {selectedFile ? (
//           <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12, flexWrap: 'wrap' }}>
//             <input
//               type="text"
//               placeholder="Optional: What do you want to focus on?"
//               value={question}
//               onChange={(e) => setQuestion(e.target.value)}
//               style={{ padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(0,0,0,0.1)', minWidth: 260 }}
//             />
//             <button
//               onClick={uploadToServer}
//               disabled={apiLoading}
//               className="btn"
//               style={{ padding: '8px 14px', borderRadius: 8, background: 'var(--main-color)', color: 'var(--txt-white)' }}
//             >
//               {apiLoading ? 'Analysing…' : 'Analyse on Server'}
//             </button>
//           </div>
//         ) : null}

//         <div
//           onDrop={onDrop}
//           onDragOver={onDragOver}
//           onDragLeave={onDragLeave}
//           style={{
//             ...dropzoneStyle,
//             marginTop: 16,
//             background: isDragging ? 'var(--second-bg)' : 'var(--main-bg)'
//           }}
//         >
//           <div style={{ fontWeight: 600, marginBottom: 6 }}>Drag & drop CSV here</div>
//           <div style={{ opacity: 0.7 }}>or click above to choose a file</div>
//         </div>

//         {errorMessage ? (
//           <div style={{ color: '#fb0b12', marginTop: 16 }}>{errorMessage}</div>
//         ) : null}
//         {apiError ? (
//           <div style={{ color: '#fb0b12', marginTop: 8 }}>{apiError}</div>
//         ) : null}
//       </div>

//       {serverSummary ? (
//         <div className="card">
//           <div style={{ fontWeight: 600, marginBottom: 12 }}>Dataset Summary (from server)</div>
//           <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 12 }}>
//             <div style={{ padding: 12, background: 'var(--second-bg)', borderRadius: 10 }}>Rows: {serverSummary.rows}</div>
//             <div style={{ padding: 12, background: 'var(--second-bg)', borderRadius: 10 }}>Columns: {serverSummary.cols}</div>
//           </div>

//           <div style={{ marginTop: 8, overflowX: 'auto' }}>
//             <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
//               <thead>
//                 <tr>
//                   <th style={{ textAlign: 'left', padding: '10px 12px' }}>Column</th>
//                   <th style={{ textAlign: 'left', padding: '10px 12px' }}>Kind</th>
//                   <th style={{ textAlign: 'left', padding: '10px 12px' }}>DType</th>
//                   <th style={{ textAlign: 'right', padding: '10px 12px' }}>Non-null</th>
//                   <th style={{ textAlign: 'right', padding: '10px 12px' }}>Nulls</th>
//                   <th style={{ textAlign: 'right', padding: '10px 12px' }}>Missing %</th>
//                   <th style={{ textAlign: 'left', padding: '10px 12px' }}>Example values</th>
//                 </tr>
//               </thead>
//               <tbody>
//                 {serverSummary.columns?.slice(0, 50).map((col) => (
//                   <tr key={col.name}>
//                     <td style={{ padding: '8px 12px' }}>{col.name}</td>
//                     <td style={{ padding: '8px 12px' }}>{col.kind}</td>
//                     <td style={{ padding: '8px 12px' }}>{col.dtype}</td>
//                     <td style={{ padding: '8px 12px', textAlign: 'right' }}>{col.non_null}</td>
//                     <td style={{ padding: '8px 12px', textAlign: 'right' }}>{col.nulls}</td>
//                     <td style={{ padding: '8px 12px', textAlign: 'right' }}>{(col.missing_ratio * 100).toFixed(2)}%</td>
//                     <td style={{ padding: '8px 12px' }}>{Array.isArray(col.example_values) ? col.example_values.join(', ') : ''}</td>
//                   </tr>
//                 ))}
//               </tbody>
//             </table>
//           </div>

//           {serverSummary.sample && serverSummary.sample.length > 0 ? (
//             <div style={{ marginTop: 16 }}>
//               <div style={{ fontWeight: 600, marginBottom: 8 }}>Sample Rows</div>
//               <div style={{ overflow: 'auto' }}>
//                 <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
//                   <thead>
//                     <tr>
//                       {Object.keys(serverSummary.sample[0]).map((key) => (
//                         <th key={key} style={{ textAlign: 'left', padding: '10px 12px' }}>{key}</th>
//                       ))}
//                     </tr>
//                   </thead>
//                   <tbody>
//                     {serverSummary.sample.map((row, idx) => (
//                       <tr key={idx}>
//                         {Object.keys(serverSummary.sample[0]).map((key) => (
//                           <td key={key} style={{ padding: '8px 12px', borderBottom: '1px solid rgba(0,0,0,0.05)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden', maxWidth: 260 }}>
//                             {String(row[key] ?? '')}
//                           </td>
//                         ))}
//                       </tr>
//                     ))}
//                   </tbody>
//                 </table>
//               </div>
//             </div>
//           ) : null}
//         </div>
//       ) : null}

//       {serverAnalysis ? (
//         <div className="card">
//           <div style={{ fontWeight: 600, marginBottom: 12 }}>AI Analysis</div>
//           {Array.isArray(serverAnalysis.insights) && serverAnalysis.insights.length > 0 ? (
//             <div style={{ marginBottom: 16 }}>
//               <div style={{ fontWeight: 600, marginBottom: 8 }}>Key Insights</div>
//               <ul style={{ paddingLeft: 18 }}>
//                 {serverAnalysis.insights.map((item, idx) => (
//                   <li key={idx} style={{ marginBottom: 6 }}>{item}</li>
//                 ))}
//               </ul>
//             </div>
//           ) : null}

//           {Array.isArray(serverAnalysis.risks) && serverAnalysis.risks.length > 0 ? (
//             <div style={{ marginBottom: 16 }}>
//               <div style={{ fontWeight: 600, marginBottom: 8 }}>Risks</div>
//               <ul style={{ paddingLeft: 18 }}>
//                 {serverAnalysis.risks.map((item, idx) => (
//                   <li key={idx} style={{ marginBottom: 6 }}>{item}</li>
//                 ))}
//               </ul>
//             </div>
//           ) : null}

//           {Array.isArray(serverAnalysis.quality_issues) && serverAnalysis.quality_issues.length > 0 ? (
//             <div style={{ marginBottom: 16 }}>
//               <div style={{ fontWeight: 600, marginBottom: 8 }}>Data Quality Issues</div>
//               <ul style={{ paddingLeft: 18 }}>
//                 {serverAnalysis.quality_issues.map((item, idx) => (
//                   <li key={idx} style={{ marginBottom: 6 }}>{item}</li>
//                 ))}
//               </ul>
//             </div>
//           ) : null}

//           {Array.isArray(serverAnalysis.suggested_actions) && serverAnalysis.suggested_actions.length > 0 ? (
//             <div style={{ marginBottom: 16 }}>
//               <div style={{ fontWeight: 600, marginBottom: 8 }}>Recommended Actions</div>
//               <ul style={{ paddingLeft: 18 }}>
//                 {serverAnalysis.suggested_actions.map((item, idx) => (
//                   <li key={idx} style={{ marginBottom: 6 }}>{item}</li>
//                 ))}
//               </ul>
//             </div>
//           ) : null}

//           {serverAnalysis.simple_metrics && Object.keys(serverAnalysis.simple_metrics).length > 0 ? (
//             <div style={{ marginTop: 8 }}>
//               <div style={{ fontWeight: 600, marginBottom: 8 }}>Simple Metrics</div>
//               <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
//                 {Object.entries(serverAnalysis.simple_metrics).map(([k, v]) => (
//                   <div key={k} style={{ padding: 12, background: 'var(--second-bg)', borderRadius: 10 }}>
//                     <div style={{ opacity: 0.7 }}>{k}</div>
//                     <div style={{ fontWeight: 600 }}>{String(v)}</div>
//                   </div>
//                 ))}
//               </div>
//             </div>
//           ) : null}
//         </div>
//       ) : null}

//       {headers.length > 0 ? (
//         <div className="card">
//           <div style={{ fontWeight: 600, marginBottom: 12 }}>Summary</div>
//           <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
//             <div style={{ padding: 12, background: 'var(--second-bg)', borderRadius: 10 }}>
//               Rows: {rows.length}
//             </div>
//             <div style={{ padding: 12, background: 'var(--second-bg)', borderRadius: 10 }}>
//               Columns: {headers.length}
//             </div>
//           </div>

//           {Object.keys(numericSummaries).length > 0 ? (
//             <div style={{ marginTop: 16, overflowX: 'auto' }}>
//               <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
//                 <thead>
//                   <tr>
//                     <th style={{ textAlign: 'left', padding: '10px 12px' }}>Column</th>
//                     <th style={{ textAlign: 'right', padding: '10px 12px' }}>Count</th>
//                     <th style={{ textAlign: 'right', padding: '10px 12px' }}>Mean</th>
//                     <th style={{ textAlign: 'right', padding: '10px 12px' }}>Min</th>
//                     <th style={{ textAlign: 'right', padding: '10px 12px' }}>Max</th>
//                   </tr>
//                 </thead>
//                 <tbody>
//                   {Object.entries(numericSummaries).map(([col, s]) => (
//                     <tr key={col}>
//                       <td style={{ padding: '8px 12px' }}>{col}</td>
//                       <td style={{ padding: '8px 12px', textAlign: 'right' }}>{s.count}</td>
//                       <td style={{ padding: '8px 12px', textAlign: 'right' }}>{s.mean.toFixed(3)}</td>
//                       <td style={{ padding: '8px 12px', textAlign: 'right' }}>{s.min}</td>
//                       <td style={{ padding: '8px 12px', textAlign: 'right' }}>{s.max}</td>
//                     </tr>
//                   ))}
//                 </tbody>
//               </table>
//             </div>
//           ) : (
//             <div style={{ marginTop: 16, opacity: 0.7 }}>No numeric columns detected yet.</div>
//           )}
//         </div>
//       ) : null}

//       {headers.length > 0 ? (
//         <div className="card">
//           <div style={{ fontWeight: 600, marginBottom: 12 }}>Preview (first {previewRows.length} rows)</div>
//           <div style={{ overflow: 'auto', maxHeight: 500 }}>
//             <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
//               <thead>
//                 <tr>
//                   {headers.map(h => (
//                     <th key={h} style={{ position: 'sticky', top: 0, background: 'var(--main-bg)', textAlign: 'left', padding: '10px 12px', borderBottom: '1px solid rgba(0,0,0,0.08)' }}>
//                       {h || '—'}
//                     </th>
//                   ))}
//                 </tr>
//               </thead>
//               <tbody>
//                 {previewRows.map((row, idx) => (
//                   <tr key={idx}>
//                     {headers.map(h => (
//                       <td key={h} style={{ padding: '8px 12px', borderBottom: '1px solid rgba(0,0,0,0.05)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden', maxWidth: 280 }}>
//                         {String(row[h] ?? '')}
//                       </td>
//                     ))}
//                   </tr>
//                 ))}
//               </tbody>
//             </table>
//           </div>
//         </div>
//       ) : null}
//     </div>
//   )
// }

"use client"

import  { Card } from "../ui/card"
import  CardContent  from "../ui/cardContent"
import  CardTitle  from "../ui/cardTitle"
import  CardHeader  from "../ui/cardHeader"
import  Button  from "../ui/Button"
import  Badge  from "../ui/badge"
import {BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"
import { Download, Eye, Brain, TrendingUp, AlertTriangle, Target } from "lucide-react"

const sampleData = [
  { month: "Jan", revenue: 4000, expenses: 2400 },
  { month: "Feb", revenue: 3000, expenses: 1398 },
  { month: "Mar", revenue: 2000, expenses: 9800 },
  { month: "Apr", revenue: 2780, expenses: 3908 },
  { month: "May", revenue: 1890, expenses: 4800 },
  { month: "Jun", revenue: 2390, expenses: 3800 },
]

const pieData = [
  { name: "Product A", value: 400, color: "#6366f1" },
  { name: "Product B", value: 300, color: "#84cc16" },
  { name: "Product C", value: 200, color: "#fbbf24" },
  { name: "Product D", value: 100, color: "#f472b6" },
]

const insights = [
  {
    type: "trend",
    title: "Revenue Growth Trend",
    description: "Revenue shows a declining trend over the past 6 months, with a 40% decrease from January to May.",
    severity: "warning",
    icon: TrendingUp,
  },
  {
    type: "anomaly",
    title: "Expense Spike Detected",
    description: "March expenses are significantly higher than average, indicating potential cost management issues.",
    severity: "error",
    icon: AlertTriangle,
  },
  {
    type: "opportunity",
    title: "Product Performance",
    description: "Product A accounts for 40% of total sales, suggesting strong market demand and growth potential.",
    severity: "success",
    icon: Target,
  },
]

export default function AnalysisResults() {
  return (
    <Card className="bg-white/80 backdrop-blur-sm border-slate-200/60 shadow-xl hover:shadow-2xl transition-all duration-300">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-3 text-slate-800">
          <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-500 rounded-lg">
            <Brain className="h-5 w-5 text-white" />
          </div>
          AI Analysis Results
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-8">
        <div className="space-y-4">
          <h4 className="font-semibold text-slate-800 text-lg flex items-center gap-2">
            <div className="w-2 h-2 bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-full"></div>
            Key Insights
          </h4>
          {insights.map((insight, index) => (
            <div
              key={index}
              className="p-5 bg-gradient-to-r from-slate-50 to-white rounded-xl border border-slate-200/60 shadow-sm hover:shadow-md transition-all duration-300 group"
            >
              <div className="flex items-start gap-4">
                <div
                  className={`p-2 rounded-lg ${
                    insight.severity === "error"
                      ? "bg-red-100 text-red-600"
                      : insight.severity === "warning"
                        ? "bg-amber-100 text-amber-600"
                        : "bg-emerald-100 text-emerald-600"
                  }`}
                >
                  <insight.icon className="h-5 w-5" />
                </div>
                <div className="flex-1 space-y-2">
                  <div className="flex items-center justify-between">
                    <h5 className="font-semibold text-slate-800 group-hover:text-slate-900 transition-colors">
                      {insight.title}
                    </h5>
                    <Badge
                      variant={
                        insight.severity === "error"
                          ? "destructive"
                          : insight.severity === "warning"
                            ? "secondary"
                            : "default"
                      }
                      className={`text-xs font-medium ${
                        insight.severity === "success" ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200" : ""
                      }`}
                    >
                      {insight.severity}
                    </Badge>
                  </div>
                  <p className="text-slate-600 leading-relaxed">{insight.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-8">
          <div className="p-6 bg-gradient-to-br from-slate-50 to-white rounded-xl border border-slate-200/60">
            <h4 className="font-semibold text-slate-800 mb-6 flex items-center gap-2">
              <div className="w-2 h-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"></div>
              Revenue vs Expenses Trend
            </h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sampleData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e2e8f0",
                      borderRadius: "12px",
                      boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                    }}
                  />
                  <Bar dataKey="revenue" fill="url(#revenueGradient)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="expenses" fill="url(#expenseGradient)" radius={[4, 4, 0, 0]} />
                  <defs>
                    <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#06b6d4" />
                      <stop offset="100%" stopColor="#0891b2" />
                    </linearGradient>
                    <linearGradient id="expenseGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10b981" />
                      <stop offset="100%" stopColor="#059669" />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="p-6 bg-gradient-to-br from-slate-50 to-white rounded-xl border border-slate-200/60">
            <h4 className="font-semibold text-slate-800 mb-6 flex items-center gap-2">
              <div className="w-2 h-2 bg-gradient-to-r from-violet-500 to-purple-500 rounded-full"></div>
              Product Distribution
            </h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="flex gap-4 pt-6 border-t border-slate-200">
          <Button className="flex-1 bg-gradient-to-r from-cyan-500 to-emerald-500 text-white hover:from-cyan-600 hover:to-emerald-600 shadow-lg hover:shadow-xl transition-all duration-300 py-3">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
          <Button
            variant="outline"
            className="flex-1 border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400 transition-all duration-300 py-3 bg-transparent"
          >
            <Eye className="h-4 w-4 mr-2" />
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}