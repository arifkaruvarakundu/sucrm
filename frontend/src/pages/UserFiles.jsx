import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card_selection";
import { Button } from "../components/ui/button_selection";
import {
  FileText,
  Loader2,
  Folder,
  BarChart3,
  Download,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FileUpload from "../components/external_analysis/file-upload";
import api from "../../api_config"; // axios instance

const YourFiles = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchFiles = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await api.get("/files", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setFiles(response.data.files || []);
    } catch (error) {
      console.error("Error fetching files:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleAnalyze = (fileId) => {
    localStorage.setItem("selectedFileId", fileId);
    navigate("/dashboard");
  };

  const handleDownload = async (fileId, filename) => {
    try {
      const token = localStorage.getItem("token");
      const response = await api.get(`/files/${fileId}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      });
  
      const { download_url } = response.data;
      if (!download_url) {
        alert("Download link not available for this file.");
        return;
      }
  
      // Trigger browser download
      const link = document.createElement("a");
      link.href = download_url;
      link.download = filename || "file";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.click();
    } catch (error) {
      console.error("Error downloading file:", error);
      alert("Failed to download file.");
    }
  };
  

  return (
    <div className="p-6 min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="max-w-6xl mx-auto">
        <motion.h1
          className="text-3xl font-bold text-gray-800 mb-6 flex items-center gap-2"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Folder className="w-8 h-8 text-blue-600" />
          Your Files
        </motion.h1>

        {loading ? (
          <div className="flex justify-center items-center h-40">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
        ) : files.length === 0 ? (
          <div className="text-center text-gray-500 mt-10">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p className="mb-4">
              No files found. Upload some data to get started!
            </p>
            <FileUpload onUploadComplete={fetchFiles} />
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {files.map((file) => (
              <motion.div
                key={file.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="shadow-md hover:shadow-lg transition rounded-2xl">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-gray-700">
                      <FileText className="text-blue-500" />
                      {file.name || "Untitled File"}
                    </CardTitle>
                  </CardHeader>

                  <CardContent>
                    <p className="text-sm text-gray-500 mb-3">
                      Uploaded on:{" "}
                      {file.uploadedAt
                        ? new Date(file.uploadedAt).toLocaleString()
                        : "Unknown"}
                    </p>

                    <div className="flex flex-col sm:flex-row gap-2">
                      <Button
                        onClick={() => handleAnalyze(file.id)}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-2"
                      >
                        <BarChart3 className="w-4 h-4" /> Analyze
                      </Button>

                      <Button
                        variant="outline"
                        onClick={() => handleDownload(file.id, file.name)}
                        className="flex-1 border border-gray-300 hover:bg-gray-100 text-gray-700 flex items-center justify-center gap-2"
                        >
                        <Download className="w-4 h-4" /> Download
                      </Button>

                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default YourFiles;
