"use client";

import { useState, useEffect } from "react";
import { X, Save, Settings as SettingsIcon, Check } from "lucide-react";

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [config, setConfig] = useState<any>(null);
    const [message, setMessage] = useState("");

    const API_BASE = "http://localhost:8000"; // Adjust if needed

    useEffect(() => {
        if (isOpen) {
            fetchConfig();
        }
    }, [isOpen]);

    const fetchConfig = async () => {
        try {
            const res = await fetch(`${API_BASE}/settings`);
            if (!res.ok) throw new Error("Failed to fetch settings");
            const data = await res.json();
            setConfig(data);
        } catch (err) {
            console.error(err);
            setMessage("Error loading settings.");
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setMessage("");
        try {
            const res = await fetch(`${API_BASE}/settings`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(config),
            });
            if (!res.ok) throw new Error("Failed to save settings");
            const data = await res.json();
            setConfig(data.config); // Update with returned config (merged)
            setMessage("Saved!");
            setTimeout(() => setMessage(""), 2000);
        } catch (err) {
            console.error(err);
            setMessage("Error saving settings.");
        } finally {
            setSaving(false);
        }
    };

    const updateLLM = (field: string, value: string) => {
        setConfig((prev: any) => ({
            ...prev,
            llm: { ...prev.llm, [field]: value },
        }));
    };

    const updateLocalModels = (field: string, value: string) => {
        setConfig((prev: any) => ({
            ...prev,
            local_models: { ...prev.local_models, [field]: value },
        }));
    };

    const updateRadar = (field: string, value: any) => {
        setConfig((prev: any) => ({
            ...prev,
            radar: { ...prev.radar, [field]: value },
        }));
    };

    const updatePolitics = (field: string, value: any) => {
        setConfig((prev: any) => ({
            ...prev,
            politics: { ...prev.politics, [field]: value },
        }));
    };

    const updateSearch = (field: string, value: string) => {
        setConfig((prev: any) => ({
            ...prev,
            search: { ...prev.search, [field]: value },
        }));
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-gray-800 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 animate-in fade-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-gray-100 dark:border-gray-700 sticky top-0 bg-white/95 dark:bg-gray-800/95 backdrop-blur z-10">
                    <div className="flex items-center space-x-2">
                        <SettingsIcon className="w-5 h-5 text-gray-500" />
                        <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">系统设置</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {loading ? (
                        <div className="text-center py-8 text-gray-500">Loading settings...</div>
                    ) : !config ? (
                        <div className="text-center py-8 text-red-500">Error loading config.</div>
                    ) : (
                        <>
                            {/* LLM Section */}
                            <section className="space-y-4">
                                <h3 className="text-sm font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">大模型设置 (LLM)</h3>
                                <div className="grid gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Model Name</label>
                                        <input
                                            type="text"
                                            value={config.llm?.model || ""}
                                            onChange={(e) => updateLLM("model", e.target.value)}
                                            className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                            placeholder="gpt-4o"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Base URL</label>
                                        <input
                                            type="text"
                                            value={config.llm?.base_url || ""}
                                            onChange={(e) => updateLLM("base_url", e.target.value)}
                                            className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                            placeholder="https://api.openai.com/v1"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">API Key</label>
                                        <input
                                            type="password"
                                            value={config.llm?.api_key || ""}
                                            onChange={(e) => updateLLM("api_key", e.target.value)}
                                            className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all font-mono"
                                        />
                                    </div>
                                </div>
                            </section>

                            {/* Local Models Section */}
                            <section className="space-y-4">
                                <h3 className="text-sm font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-wider">本地模型设置 (Local Models)</h3>
                                <div className="grid gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">OCR Model</label>
                                        <input
                                            type="text"
                                            value={config.local_models?.ocr_model || ""}
                                            onChange={(e) => updateLocalModels("ocr_model", e.target.value)}
                                            className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all"
                                            placeholder="Qwen/Qwen2.5-VL-3B-Instruct"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Embedding Model</label>
                                        <input
                                            type="text"
                                            value={config.local_models?.embedding_model || ""}
                                            onChange={(e) => updateLocalModels("embedding_model", e.target.value)}
                                            className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all"
                                            placeholder="Qwen/Qwen3-VL-Embedding-2B"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Rerank Model</label>
                                        <input
                                            type="text"
                                            value={config.local_models?.rerank_model || ""}
                                            onChange={(e) => updateLocalModels("rerank_model", e.target.value)}
                                            className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all"
                                            placeholder="Qwen/Qwen3-VL-Reranker-2B"
                                        />
                                    </div>
                                </div>
                            </section>

                            {/* Search Engine Section */}
                            <section className="space-y-4">
                                <h3 className="text-sm font-semibold text-green-600 dark:text-green-400 uppercase tracking-wider">搜索设置 (Search Engine)</h3>
                                <div className="grid gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Provider</label>
                                        <select
                                            value={config.search?.provider || "duckduckgo"}
                                            onChange={(e) => updateSearch("provider", e.target.value)}
                                            className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition-all"
                                        >
                                            <option value="duckduckgo">DuckDuckGo (免费/无需 Key)</option>
                                            <option value="tavily">Tavily (推荐/需要 Key)</option>
                                        </select>
                                    </div>
                                    {config.search?.provider === "tavily" && (
                                        <div className="animate-in fade-in slide-in-from-top-2 duration-200">
                                            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Tavily API Key</label>
                                            <input
                                                type="password"
                                                value={config.search?.tavily_api_key || ""}
                                                onChange={(e) => updateSearch("tavily_api_key", e.target.value)}
                                                className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition-all font-mono"
                                                placeholder="tvly-..."
                                            />
                                            <p className="text-xs text-gray-500 mt-1">
                                                可在 <a href="https://tavily.com" target="_blank" rel="noreferrer" className="text-blue-500 hover:underline">tavily.com</a> 免费获取。
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </section>

                            {/* General Section */}
                            <section className="space-y-4">
                                <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">通用设置</h3>
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">考研日期</label>
                                    <input
                                        type="date"
                                        value={config.general?.exam_date || ""}
                                        onChange={(e) => setConfig((prev: any) => ({
                                            ...prev,
                                            general: { ...prev.general, exam_date: e.target.value }
                                        }))}
                                        className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 outline-none transition-all"
                                    />
                                    <p className="text-xs text-gray-500 mt-1">设置后将在首页显示倒计时。</p>
                                </div>
                            </section>

                            <hr className="border-gray-100 dark:border-gray-700" />

                            {/* Radar Agent Section */}
                            <section className="space-y-4">
                                <h3 className="text-sm font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-wider">Radar Agent (院校监控)</h3>
                                <div className="space-y-4">
                                    <label className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                        <input
                                            type="checkbox"
                                            checked={config.radar?.enabled ?? true}
                                            onChange={(e) => updateRadar("enabled", e.target.checked)}
                                            className="w-5 h-5 text-purple-600 rounded border-gray-300 focus:ring-purple-500"
                                        />
                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">启用 Radar Agent</span>
                                    </label>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">目标院校</label>
                                            <input
                                                type="text"
                                                value={config.radar?.target_school || ""}
                                                onChange={(e) => updateRadar("target_school", e.target.value)}
                                                className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-purple-500 focus:border-purple-500 outline-none transition-all"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">调度时间 (HH:MM)</label>
                                            <input
                                                type="time"
                                                value={config.radar?.schedule_time || "08:00"}
                                                onChange={(e) => updateRadar("schedule_time", e.target.value)}
                                                className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-purple-500 focus:border-purple-500 outline-none transition-all"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </section>

                            <hr className="border-gray-100 dark:border-gray-700" />

                            {/* Politics Agent Section */}
                            <section className="space-y-4">
                                <h3 className="text-sm font-semibold text-red-600 dark:text-red-400 uppercase tracking-wider">Politics Agent (时政新闻)</h3>
                                <div className="space-y-4">
                                    <label className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                        <input
                                            type="checkbox"
                                            checked={config.politics?.enabled ?? true}
                                            onChange={(e) => updatePolitics("enabled", e.target.checked)}
                                            className="w-5 h-5 text-red-600 rounded border-gray-300 focus:ring-red-500"
                                        />
                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">启用 Politics Agent</span>
                                    </label>

                                    <div>
                                        <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">调度时间 (HH:MM)</label>
                                        <input
                                            type="time"
                                            value={config.politics?.schedule_time || "08:30"}
                                            onChange={(e) => updatePolitics("schedule_time", e.target.value)}
                                            className="w-full p-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-red-500 focus:border-red-500 outline-none transition-all max-w-[150px]"
                                        />
                                    </div>
                                </div>
                            </section>
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-between items-center p-6 border-t border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/50 rounded-b-xl">
                    <div className="text-sm">
                        {message && (
                            <span className={`inline-flex items-center ${message.includes("Error") ? "text-red-600" : "text-green-600"}`}>
                                {message === "Saved!" && <Check className="w-4 h-4 mr-1" />}
                                {message}
                            </span>
                        )}
                    </div>
                    <div className="flex space-x-3">
                        <button
                            onClick={onClose}
                            className="px-5 py-2.5 text-sm font-medium text-gray-600 hover:text-gray-800 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg transition-colors"
                        >
                            关闭
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={saving || loading}
                            className="inline-flex items-center px-5 py-2.5 text-sm font-medium text-white bg-black hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
                        >
                            {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                            保存设置
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Helper for loader
function Loader2({ className }: { className?: string }) {
    return (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
    );
}
