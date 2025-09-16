import { useState } from "react";
import axios from "axios";
import API_BASE_URL from "../../../api_config";

export default function ChatAI() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const askAI = async () => {
    try {
      setError(null);
      setResponse(null);

      const res = await axios.post(`${API_BASE_URL}/ask-ai`, {
        question: question,
      });

      if (res.data.error) {
        setError(res.data.error);
      } else {
        setResponse(res.data);
      }
    } catch (err) {
      setError("Failed to connect to AI service.");
    }
  };

  return (
    <div className="p-4 max-w-lg mx-auto">
      <h1 className="text-xl font-bold mb-2">Ask your CRM</h1>

      <input
        type="text"
        className="w-full border p-2 rounded"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask about customers, orders, etc..."
      />

      <button
        onClick={askAI}
        className="mt-2 bg-blue-600 text-white px-4 py-2 rounded"
      >
        Ask
      </button>

      <div className="mt-4 whitespace-pre-wrap bg-gray-50 p-4 rounded shadow">
        {error && <div className="text-red-600">{error}</div>}

        {response && (
          <div className="space-y-4">
            {/* <div>
              <strong>SQL Query:</strong>
              <pre className="bg-gray-200 p-2 rounded text-sm">
                {response.sql_query}
              </pre>
            </div> */}

            {response.result && response.result.length > 0 && (
              <div>
                <strong>Answer:</strong>
                <ul className="list-disc ml-6 mt-2 space-y-2">
                  {response.result.map((row, idx) => (
                    <li key={idx}>
                      {Object.entries(row).map(([key, value]) => (
                        <div key={key}>
                          <strong>{key}</strong>: {value ?? "0"}
                        </div>
                      ))}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {!response.result && response.answer && (
              <div>
                <strong>Answer:</strong> {response.answer}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

