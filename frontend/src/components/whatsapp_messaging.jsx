import React, { useEffect, useState, useRef } from "react";
import { Check, CheckCheck } from "lucide-react"; // optional, or replace with inline SVGs
import API_BASE_URL from "../../api_config";

const WhatsAppMessaging = ({ phone }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const wsRef = useRef(null);

  const chatEndRef = useRef(null);

  useEffect(() => {
  chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
}, [messages]);

  // function formatKuwaitNumber(raw) {
  //   if (!raw) return "";

  //   // Remove all non-digit characters
  //   const digits = raw.replace(/\D/g, "");

  //   // Remove leading zeros
  //   const normalized = digits.replace(/^0+/, "");

  //   // If it starts with '965' already, return it
  //   if (normalized.startsWith("965") && normalized.length === 11) {
  //     return normalized;
  //   }

  //   // If it's 8 digits, assume it's local and prepend 965
  //   if (normalized.length === 8) {
  //     return "965" + normalized;
  //   }

  //   // If it's something else (e.g. 00965...), take last 8 digits and prepend 965
  //   if (normalized.length > 8) {
  //     return "965" + normalized.slice(-8);
  //   }

  //   // fallback
  //   return normalized;
  // }

  // const toNumber = formatKuwaitNumber(phone);
  const toNumber = phone
  console.log("📞 Sending to:", toNumber);
  // 🧠 Track message IDs to update status
  const messageIdMap = useRef({}); // local map of sent messages

  useEffect(() => {
      const loadHistory = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/whatsapp-messages?phone=${encodeURIComponent(toNumber)}`);
        const data = await res.json();
        console.log("📜 Loaded history:", data);
        setMessages(data);
      } catch (error) {
        console.error("❌ Error fetching history:", error);
      }
    };

    loadHistory();

    // const ws = new WebSocket("ws://localhost:8000/ws");
  const wsUrl = API_BASE_URL.startsWith("https")
    ? API_BASE_URL.replace("https", "wss")
    : API_BASE_URL.replace("http", "ws");

  const ws = new WebSocket(`${wsUrl}/ws`);
  wsRef.current = ws;

    ws.onopen = () => console.log("🟢 WebSocket connected");
    ws.onclose = () => console.log("🔴 WebSocket disconnected");
    ws.onerror = (e) => console.error("WebSocket error:", e);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const value = data?.entry?.[0]?.changes?.[0]?.value;

      if (value?.messages) {
        const msg = value.messages[0];
        const text = msg?.text?.body || "[no text]";
        const from = msg?.from;
        const timestamp = msg?.timestamp;

        setMessages((prev) => [
          ...prev,
          {
            text,
            from: "them",
            timestamp,
            raw: msg,
          },
        ]);
      } else if (value?.statuses) {
        const status = value.statuses[0];
        const { id, status: statusType, timestamp } = status;

        // Update message status based on ID
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === id
              ? { ...msg, status: statusType, timestamp }
              : msg
          )
        );
      } else {
        // Fallback for unknown events
        setMessages((prev) => [
          ...prev,
          {
            text: "[Unrecognized webhook event]",
            from: "system",
            raw: data,
          },
        ]);
      }
    };

    return () => ws.close();
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const tempId = `temp-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      {
        id: tempId,
        text: input,
        from: "me",
        timestamp: Date.now() / 1000,
        status: "sent", // default
      },
    ]);

    const msgToSend = input;
    setInput("");

    try {
      const res = await fetch(`${API_BASE_URL}/send-message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to_number: toNumber, message: msgToSend }),
      });

      const data = await res.json();
      const messageId = data?.messages?.[0]?.id;

      if (messageId) {
        messageIdMap.current[tempId] = messageId;

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === tempId ? { ...msg, id: messageId } : msg
          )
        );
      }

      console.log("✅ Sent:", data);
    } catch (err) {
      console.error("❌ Error sending:", err);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  const renderStatusIcon = (status) => {
    if (status === "read")
      return <CheckCheck size={14} className="text-blue-500 ml-1 inline" />;
    if (status === "delivered")
      return <CheckCheck size={14} className="text-gray-500 ml-1 inline" />;
    if (status === "sent")
      return <Check size={14} className="text-gray-500 ml-1 inline" />;
    return null;
  };

  return (
    <div className="flex flex-col max-w-md mx-auto mt-10 border rounded shadow-lg h-[600px]">
      <div className="bg-green-600 text-white px-4 py-3 rounded-t">
        <h2 className="text-lg font-semibold">📨 WhatsApp Chat</h2>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-2 bg-gray-50">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`max-w-[75%] px-3 py-2 rounded-lg text-sm relative ${
              msg.from === "me"
                ? "ml-auto bg-green-500 text-white"
                : msg.from === "them"
                ? "mr-auto bg-gray-200 text-gray-900"
                : "mx-auto bg-yellow-100 text-black"
            }`}
          >
            <div>{msg.text}</div>
            <div className="text-xs text-white/70 mt-1 flex justify-end items-center gap-1">
              {msg.timestamp &&
                new Date(msg.timestamp * 1000).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              {msg.from === "me" && renderStatusIcon(msg.status)}
            </div>
          </div>
        ))}
      </div>

      <div className="flex p-2 border-t bg-white">
        <input
          type="text"
          className="flex-1 border rounded px-3 py-2 text-sm focus:outline-none"
          placeholder="Type a message"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
        />
        <button
          onClick={sendMessage}
          className="ml-2 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          Send
        </button>
      </div>
      <div ref={chatEndRef} />
    </div>
  );
};

export default WhatsAppMessaging;
