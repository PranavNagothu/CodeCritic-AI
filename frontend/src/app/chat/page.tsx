'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileCode, Sparkles } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: string[];
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const res = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: input, provider: 'gemini', use_agent: true }),
            });
            const data = await res.json();

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: data.answer || data.response || 'No response received',
                sources: data.sources || [],
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            setMessages((prev) => [
                ...prev,
                {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: 'Error connecting to backend. Please ensure the API is running.',
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const suggestions = [
        'Explain how authentication works',
        'Find all database queries',
        'What are the main entry points?',
        'Show me the API endpoints',
    ];

    return (
        <div className="flex flex-col h-screen">
            {/* Header */}
            <motion.header
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 m-4 mb-0 flex items-center justify-between"
            >
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 to-violet-500 flex items-center justify-center">
                        💬
                    </div>
                    <div>
                        <h1 className="font-bold text-lg">Chat Mode</h1>
                        <p className="text-sm text-slate-400">Ask questions about your codebase</p>
                    </div>
                </div>
            </motion.header>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex flex-col items-center justify-center h-full text-center"
                    >
                        <Sparkles className="w-16 h-16 text-slate-600 mb-4" />
                        <h2 className="text-2xl font-bold bg-gradient-to-r from-sky-400 to-violet-400 bg-clip-text text-transparent mb-2">Ask anything about your code</h2>
                        <p className="text-slate-400 mb-8 max-w-md">
                            I can explain functions, find patterns, suggest improvements, and more.
                        </p>

                        <div className="flex flex-wrap gap-2 justify-center max-w-xl">
                            {suggestions.map((suggestion, i) => (
                                <motion.button
                                    key={suggestion}
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: i * 0.1 }}
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => setInput(suggestion)}
                                    className="px-4 py-2 bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-xl rounded-full text-sm text-slate-300 hover:border-sky-500/50 transition-colors"
                                >
                                    {suggestion}
                                </motion.button>
                            ))}
                        </div>
                    </motion.div>
                ) : (
                    <AnimatePresence>
                        {messages.map((message, i) => (
                            <motion.div
                                key={message.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                            >
                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${message.role === 'user'
                                        ? 'bg-violet-500/20 text-violet-400'
                                        : 'bg-sky-500/20 text-sky-400'
                                    }`}>
                                    {message.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                                </div>

                                <div className={`bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 max-w-[70%] ${message.role === 'user'
                                        ? 'bg-violet-500/10 border-violet-500/20'
                                        : 'border-sky-500/20'
                                    }`}>
                                    {/* Sources */}
                                    {message.sources && message.sources.length > 0 && (
                                        <div className="flex flex-wrap gap-2 mb-3 pb-3 border-b border-white/10">
                                            {message.sources.map((source, i) => (
                                                <span key={i} className="inline-flex items-center gap-1 px-2 py-1 bg-slate-800 rounded text-xs text-slate-400">
                                                    <FileCode className="w-3 h-3" />
                                                    {source}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    <p className="whitespace-pre-wrap">{message.content}</p>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                )}

                {isLoading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex gap-4"
                    >
                        <div className="w-10 h-10 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center">
                            <Bot className="w-5 h-5" />
                        </div>
                        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 border-sky-500/20">
                            <div className="flex gap-1">
                                <span className="w-2 h-2 bg-sky-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                <span className="w-2 h-2 bg-sky-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                <span className="w-2 h-2 bg-sky-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                        </div>
                    </motion.div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <motion.form
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                onSubmit={handleSubmit}
                className="p-4"
            >
                <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 flex items-center gap-4 !p-3">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about your codebase..."
                        className="flex-1 bg-transparent border-none outline-none text-slate-200 placeholder:text-slate-500"
                        disabled={isLoading}
                    />
                    <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="w-10 h-10 bg-gradient-to-r from-sky-500 to-violet-500 rounded-xl flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="w-5 h-5" />
                    </motion.button>
                </div>
            </motion.form>
        </div>
    );
}
