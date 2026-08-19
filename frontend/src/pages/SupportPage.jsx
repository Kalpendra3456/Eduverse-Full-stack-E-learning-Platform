import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../state/AuthContext";
import { createApiClient } from "../api/client";
import "./SupportPage.css";

const SupportPage = () => {
    const { token } = useAuth();
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [explanation, setExplanation] = useState("");
    const [loading, setLoading] = useState(false);
    const [chatInput, setChatInput] = useState("");
    const [messages, setMessages] = useState([
        { role: "ai", text: "Hello! I'm your Eduverse Career Assistant. How can I help you with your learning goals today?" }
    ]);
    const [chatLoading, setChatLoading] = useState(false);
    const chatEndRef = useRef(null);

    const api = createApiClient(token);

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        try {
            const response = await api.post("support/recommend", { query });
            setResults(response.data.results || []);
            setExplanation(response.data.explanation || "");
        } catch (error) {
            console.error("Search failed:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSendMessage = async () => {
        if (!chatInput.trim() || chatLoading) return;

        const userMessage = chatInput.trim();
        setMessages(prev => [...prev, { role: "user", text: userMessage }]);
        setChatInput("");
        setChatLoading(true);

        try {
            const response = await api.post("support/chat", { message: userMessage });
            setMessages(prev => [...prev, { role: "ai", text: response.data.reply }]);
        } catch (error) {
            setMessages(prev => [...prev, { role: "ai", text: "Error: Could not reach the assistant." }]);
        } finally {
            setChatLoading(false);
        }
    };

    return (
        <div className="support-page">
            <header className="support-header">
                <h1>Support</h1>
                <p className="subtitle">Next course recommendation powered by Eduverse.</p>
            </header>

            <div className="support-search-section">
                <form onSubmit={handleSearch}>
                    <input 
                        type="text" 
                        placeholder="What do you want to learn? (e.g. Python, Finance, Design)" 
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <button type="submit" disabled={loading}>
                        {loading ? "Searching..." : "Find Courses"}
                    </button>
                </form>
            </div>

            {results.length > 0 && (
                <div className="support-results">
                    <h2>Top Recommendations</h2>
                    <div className="results-grid">
                        {results.map((r, i) => (
                            <div className="course-card" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
                                <h3>{r}</h3>
                                <p className="muted">High similarity found based on your interest.</p>
                            </div>
                        ))}
                    </div>


                </div>
            )}

            <div className="chat-section">
                <h2 className="chat-title">Career Assistant</h2>
                <div className="chat-container">
                    <div className="chat-box">
                        {messages.map((msg, i) => (
                            <div key={i} className={`message ${msg.role}-message`}>
                                {msg.text}
                            </div>
                        ))}
                        <div ref={chatEndRef} />
                    </div>
                    <div className="chat-input-group">
                        <input 
                            type="text" 
                            placeholder="Ask about career paths, skills..." 
                            value={chatInput}
                            onChange={(e) => setChatInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        />
                        <button onClick={handleSendMessage} disabled={chatLoading}>
                            {chatLoading ? "..." : "Send"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SupportPage;
