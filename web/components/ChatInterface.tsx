"use client";

import React, { useRef, useEffect, useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css'; // Formula styles
import { Send, User, Bot, Loader2, History, Camera, Settings, X, ChevronRight, Square, Image as ImageIcon, Plus, MessageSquare, Trash2, RefreshCw, List, FileText, Globe, Link as LinkIcon } from 'lucide-react';
import ReasoningBubble from './ReasoningBubble';
import TypewriterText from './TypewriterText';
import { useLLMStream, Message } from '@/hooks/useLLMStream';
import SettingsModal from './SettingsModal';
import AlertHistoryModal from './AlertHistoryModal';

// Tailwind + clsx utility (inline for simplicity)
const cn = (...classes: (string | undefined)[]) => classes.filter(Boolean).join(' ');

export default function ChatInterface() {
    const { messages, sendMessage, stopGeneration, isLoading, error, setMessages } = useLLMStream();
    const [input, setInput] = React.useState('');
    const [selectedImage, setSelectedImage] = React.useState<File | null>(null);
    const [isUploading, setIsUploading] = React.useState(false);
    const [isDocUploading, setIsDocUploading] = React.useState(false);
    const [isWebSearchEnabled, setIsWebSearchEnabled] = useState(false);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [isPlusMenuOpen, setIsPlusMenuOpen] = useState(false);
    const [config, setConfig] = useState<any>(null);
    const [daysLeft, setDaysLeft] = useState<number | null>(null);
    const [alerts, setAlerts] = useState<any>(null);
    const [refreshingRadar, setRefreshingRadar] = useState(false);
    const [refreshingPolitics, setRefreshingPolitics] = useState(false);
    
    // Alert Modal State
    const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
    const [alertModalType, setAlertModalType] = useState<'radar' | 'politics' | null>(null);

    // History State
    const [history, setHistory] = useState<any[]>([]);
    const [sessionId, setSessionId] = useState<string>('');
    const [deleteTarget, setDeleteTarget] = useState<any>(null);
    const DEFAULT_USER_ID = "default_user"; // Mock user ID

    const [quote, setQuote] = useState("星光不问赶路人，时光不负有心人。");
    const quoteFetchedRef = useRef(false);

    // Generate Session ID on mount if not exists
    useEffect(() => {
        if (!sessionId) {
            setSessionId(crypto.randomUUID());
        }
        fetchHistory();
        fetchAlerts();
        
        // Fetch Quote from Backend (Prevent double fetch in Strict Mode)
        if (!quoteFetchedRef.current) {
            quoteFetchedRef.current = true;
            fetch('http://localhost:8000/quote')
                .then(res => res.json())
                .then(data => {
                    if (data.quote) setQuote(data.quote);
                })
                .catch(err => console.error("Failed to fetch quote", err));
        }
    }, []);

    // Fetch Alerts
    const fetchAlerts = async () => {
        try {
            const res = await fetch('http://localhost:8000/alerts');
            if (res.ok) {
                const data = await res.json();
                setAlerts(data);
            }
        } catch (err) {
            console.error("Failed to fetch alerts", err);
        }
    };

    // Force Radar Check
    const handleRadarRefresh = async () => {
        if (refreshingRadar) return;
        setRefreshingRadar(true);
        try {
            const res = await fetch('http://localhost:8000/radar/check', { method: 'POST' });
            if (res.ok) await fetchAlerts();
        } catch (e) {
            console.error(e);
        } finally {
            setRefreshingRadar(false);
        }
    };

    // Force Politics Check
    const handlePoliticsRefresh = async () => {
        if (refreshingPolitics) return;
        setRefreshingPolitics(true);
        try {
            const res = await fetch('http://localhost:8000/politics/check', { method: 'POST' });
            if (res.ok) await fetchAlerts();
        } catch (e) {
            console.error(e);
        } finally {
            setRefreshingPolitics(false);
        }
    };

    // Fetch History
    const fetchHistory = async () => {
        try {
            const res = await fetch(`http://localhost:8000/history/${DEFAULT_USER_ID}`);
            if (res.ok) {
                const data = await res.json();
                setHistory(data.history || []);
            }
        } catch (err) {
            console.error("Failed to fetch history", err);
        }
    };

    // Auto-save session when messages change (debounced)
    useEffect(() => {
        if (messages.length === 0) return;
        
        const saveSession = async () => {
            try {
                await fetch(`http://localhost:8000/history/${DEFAULT_USER_ID}/save`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        messages: messages
                    })
                });
                // Refresh history list silently
                fetchHistory();
            } catch (err) {
                console.error("Failed to save session", err);
            }
        };

        const timer = setTimeout(saveSession, 1000);
        return () => clearTimeout(timer);
    }, [messages, sessionId]);

    // Handle "New Chat"
    const handleNewChat = () => {
        setMessages([]); // Clear messages
        setSessionId(crypto.randomUUID()); // New Session ID
        setInput('');
    };

    // Handle History Item Click
    const handleHistoryClick = (session: any) => {
        setMessages(session.messages || []);
        setSessionId(session.id);
    };

    // Handle Delete Session (Trigger Modal)
    const handleDeleteSession = (e: React.MouseEvent, session: any) => {
        e.stopPropagation();
        setDeleteTarget(session);
    };

    // Confirm Delete Action
    const confirmDelete = async () => {
        if (!deleteTarget) return;

        try {
            const res = await fetch(`http://localhost:8000/history/${DEFAULT_USER_ID}/${deleteTarget.id}`, {
                method: 'DELETE',
            });
            if (res.ok) {
                // Remove from list
                setHistory(prev => prev.filter(item => item.id !== deleteTarget.id));
                // If deleted current session, start new chat
                if (deleteTarget.id === sessionId) {
                    handleNewChat();
                }
            }
        } catch (err) {
            console.error("Failed to delete session", err);
        } finally {
            setDeleteTarget(null);
        }
    };

    // Fetch config on mount or when settings close (to update countdown)
    useEffect(() => {
        fetch('http://localhost:8000/settings')
            .then(res => res.json())
            .then(data => {
                setConfig(data);
                if (data.general?.exam_date) {
                    const examDate = new Date(data.general.exam_date);
                    const today = new Date();
                    const diffTime = examDate.getTime() - today.getTime();
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    setDaysLeft(diffDays > 0 ? diffDays : 0);
                }
            })
            .catch(err => console.error("Failed to load config", err));
    }, [isSettingsOpen]);

    const scrollRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);    // For Gallery
    const cameraInputRef = useRef<HTMLInputElement>(null);  // For Camera
    const docInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedImage(e.target.files[0]);
        }
        // Reset value to allow selecting the same file again if needed
        e.target.value = '';
    };

    const handleDocSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const files = Array.from(e.target.files);
            
            // 过滤非 PDF 文件
            const validFiles = files.filter(file => file.type === 'application/pdf' || file.name.endsWith('.pdf'));
            
            if (validFiles.length === 0) {
                alert('请至少选择一个 PDF 文件');
                return;
            }

            if (validFiles.length < files.length) {
                alert(`已自动忽略 ${files.length - validFiles.length} 个非 PDF 文件`);
            }

            setIsDocUploading(true);
            try {
                const formData = new FormData();
                // 注意：后端改为接收 files 列表，这里 key 必须是 files
                validFiles.forEach(file => {
                    formData.append('files', file);
                });
                
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const res = await fetch(`${apiUrl}/upload`, {
                    method: 'POST',
                    body: formData,
                });

                if (!res.ok) {
                    throw new Error('文档上传失败');
                }

                const result = await res.json();
                alert(result.message || `成功上传 ${result.count} 个文件并加入知识库！`);
                
            } catch (err) {
                console.error("Doc upload failed", err);
                alert("文档上传失败，请稍后重试。");
            } finally {
                setIsDocUploading(false);
                if (docInputRef.current) docInputRef.current.value = '';
            }
        }
    };

    // Close Plus Menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            if (!target.closest('.plus-menu-container')) {
                setIsPlusMenuOpen(false);
            }
        };

        if (isPlusMenuOpen) {
            document.addEventListener('click', handleClickOutside);
        }
        return () => {
            document.removeEventListener('click', handleClickOutside);
        };
    }, [isPlusMenuOpen]);

    const handleCameraClick = () => {
        setIsPlusMenuOpen(false);
        if (cameraInputRef.current) {
            cameraInputRef.current.click();
        }
    };

    const handleGalleryClick = () => {
        setIsPlusMenuOpen(false);
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const handleDocClick = () => {
        setIsPlusMenuOpen(false);
        if (docInputRef.current) {
            docInputRef.current.click();
        }
    };


    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if ((!input.trim() && !selectedImage) || isLoading || isUploading) return;

        let fullMessage = input;

        if (selectedImage) {
            setIsUploading(true);
            try {
                const formData = new FormData();
                formData.append('file', selectedImage);

                // Use NEXT_PUBLIC_API_URL if available, otherwise relative path (assuming proxy) or direct localhost
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

                const res = await fetch(`${apiUrl}/upload/image`, {
                    method: 'POST',
                    body: formData,
                });

                if (!res.ok) {
                    throw new Error('图片上传失败');
                }

                const data = await res.json();
                const ocrText = data.text;
                const uploadedImageUrl = data.url; // Get persistent URL from backend
                
                // We'll append OCR text for the backend context, but we also pass the image URL for VLM support
                fullMessage = `${input}\n\n[图片内容]\n${ocrText}`;
                
                // Update local preview to use the server URL if desired, or keep local blob
                // const imageUrl = uploadedImageUrl; 
                
                // Send both text content and image URL to the hook
                sendMessage(fullMessage, { web_search_enabled: isWebSearchEnabled, image: uploadedImageUrl });
                setInput('');
                setSelectedImage(null);
                return; // Exit here as we called sendMessage

            } catch (err) {
                console.error("Upload failed", err);
                alert("图片处理失败，但这不影响文字发送。");
            } finally {
                setIsUploading(false);
            }
        }
        
        // Normal text message sending (no image)
        sendMessage(fullMessage, { web_search_enabled: isWebSearchEnabled });
        setInput('');
    };


    return (
        <div className="flex h-screen bg-gray-50 text-gray-900 font-sans overflow-hidden">
            {/* Settings Modal */}
            <SettingsModal 
                isOpen={isSettingsOpen} 
                onClose={() => {
                    setIsSettingsOpen(false);
                    // Refresh config when settings close
                    fetch('http://localhost:8000/settings').then(res => res.json()).then(setConfig);
                }} 
            />

            {/* Alert History Modal */}
            <AlertHistoryModal 
                isOpen={isAlertModalOpen} 
                onClose={() => setIsAlertModalOpen(false)} 
                type={alertModalType}
                data={alerts}
            />

            {/* Delete Confirmation Modal */}
            {deleteTarget && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 transform transition-all scale-100">
                        <h3 className="text-lg font-bold text-gray-900 mb-2">删除确认</h3>
                        <p className="text-sm text-gray-500 mb-6">
                            确定要删除对话 "{deleteTarget.title || "无标题对话"}" 吗？此操作无法撤销。
                        </p>
                        <div className="flex justify-end space-x-3">
                            <button
                                onClick={() => setDeleteTarget(null)}
                                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                            >
                                取消
                            </button>
                            <button
                                onClick={confirmDelete}
                                className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg shadow-sm transition-colors"
                            >
                                确定删除
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Sidebar */}
            <aside className="w-72 bg-white border-r border-gray-200 hidden md:flex flex-col flex-shrink-0 z-20">
                <div className="px-6 pt-6 pb-2 flex items-center space-x-3">
                    <div className="w-8 h-8 bg-black text-white rounded-lg flex items-center justify-center font-bold text-base shadow-blue-500/20 shadow-lg">K</div>
                    <div>
                        <span className="font-bold text-base block">考研搭子</span>
                    </div>
                </div>

                <div className="flex-1 flex flex-col min-h-0 px-4 py-2 space-y-2">
                    <div className="px-2 py-2">
                        <button
                            onClick={handleNewChat}
                            className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-xl transition-all shadow-md shadow-blue-500/20 mb-6"
                        >
                            <Plus className="w-4 h-4" />
                            <span className="font-medium text-sm">新建对话</span>
                        </button>
                        
                        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">今日概览</h3>
                        {/* Placeholder for dashboard stats */}
                        <div className="bg-blue-50 rounded-xl p-3 border border-blue-100 mb-3">
                            <span className="text-xs text-blue-600 font-medium block mb-1">📅 距离考研</span>
                            <span className="text-2xl font-bold text-blue-800">{daysLeft !== null ? daysLeft : "--"} <span className="text-sm font-normal">天</span></span>
                        </div>

                        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-xl p-3 mb-4 shadow-sm">
                            <p className="text-xs text-blue-800 font-medium italic">"{quote}"</p>
                        </div>
                    </div>

                    <div className="px-2 flex-1 flex flex-col min-h-0">
                        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 mt-2 flex-shrink-0">历史记录</h3>
                        {/* History items */}
                        <div className="space-y-1 flex-1 overflow-y-auto hover-scrollbar pr-1">
                            {history.length > 0 ? (
                                history.map((session) => (
                                    <div
                                        key={session.id}
                                        className={cn(
                                            "w-full px-3 py-2 text-sm rounded-lg transition-colors flex items-center gap-2 group cursor-pointer relative",
                                            session.id === sessionId ? "bg-gray-100 text-gray-900 font-medium" : "text-gray-600 hover:bg-gray-50"
                                        )}
                                        onClick={() => handleHistoryClick(session)}
                                    >
                                        <MessageSquare className="w-3 h-3 flex-shrink-0 opacity-50" />
                                        <span className="truncate flex-1">{session.title || "无标题对话"}</span>
                                        
                                        <button
                                            onClick={(e) => handleDeleteSession(e, session)}
                                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 rounded text-gray-400 hover:text-red-500 transition-all absolute right-2"
                                            title="删除"
                                        >
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))
                            ) : (
                                <p className="text-xs text-gray-400 px-3 py-2 italic">暂无历史记录</p>
                            )}
                        </div>
                    </div>
                </div>

                <div className="p-4">
                    <div className="flex items-center p-2 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-100 to-gray-300 border-2 border-white shadow-sm flex-shrink-0" />
                        <div className="ml-3 flex-1 overflow-hidden">
                            <p className="text-sm font-semibold text-gray-900 truncate">考研战士</p>
                            <p className="text-xs text-gray-500 truncate">Pro 计划</p>
                        </div>
                        <Settings
                            className="w-5 h-5 text-gray-400 hover:text-gray-600 cursor-pointer"
                            onClick={(e) => { e.stopPropagation(); setIsSettingsOpen(true); }}
                        />
                    </div>
                </div>
            </aside>

            {/* Main Chat Area */}
            <main className="flex-1 flex flex-col relative w-full h-full bg-white md:bg-gray-50">
                {/* Header (Top Bar) - Mobile Only */}
                <header className="px-6 py-4 bg-white/80 backdrop-blur-md flex justify-between items-center sticky top-0 z-10 border-b border-gray-100 md:hidden">
                    <div className="flex items-center space-x-2">
                        <button 
                            onClick={handleNewChat}
                            className="w-8 h-8 bg-black text-white rounded-lg flex items-center justify-center font-bold active:scale-95 transition-transform"
                            title="回到首页/新建对话"
                        >
                            <Plus className="w-5 h-5" />
                        </button>
                        <h1 className="text-lg font-bold text-gray-800">考研搭子</h1>
                    </div>
                    <button onClick={() => setIsSettingsOpen(true)} className="p-2 text-gray-600">
                        <Settings className="w-6 h-6" />
                    </button>
                </header>



                {/* Messages Container */}
                <div className="flex-1 overflow-hidden relative flex flex-col">
                    <div
                        ref={scrollRef}
                        className="flex-1 overflow-y-auto px-4 md:px-0 scroll-smooth"
                    >
                        <div className="max-w-[95%] mx-auto py-8 min-h-full">
                            {messages.length === 0 && (
                                <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    <div className="space-y-4">
                                        <div className="w-20 h-20 bg-gradient-to-tr from-blue-600 to-purple-600 rounded-3xl shadow-xl flex items-center justify-center text-white mx-auto transform hover:rotate-6 transition-transform">
                                            <Bot className="w-10 h-10" />
                                        </div>
                                        <h2 className="text-3xl font-bold text-gray-900 tracking-tight">你好，我是总指挥 Agent</h2>
                                        <p className="text-lg text-gray-500 max-w-md mx-auto">
                                            我已经准备好协助你的考研之路。无论是<span className="text-blue-600 font-medium">计划制定</span>、<span className="text-purple-600 font-medium">院校选择</span>还是<span className="text-red-600 font-medium">题目解答</span>。
                                        </p>
                                    </div>

                                    {/* Dashboard Info Area (New) */}
                                    <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-4 px-2 animate-in fade-in slide-in-from-bottom-5 duration-700 delay-100">
                                        {/* University Monitor */}
                                        <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow relative group flex flex-col h-full">
                                            <div className="flex justify-between items-center mb-3">
                                                <h3 className="font-bold text-gray-800 flex items-center">
                                                    <span className="w-2 h-6 bg-purple-500 rounded-full mr-2"></span>
                                                    院校监控
                                                </h3>
                                                <div className="flex items-center gap-2">
                                                    <button 
                                                        onClick={() => { setAlertModalType('radar'); setIsAlertModalOpen(true); }}
                                                        className="p-1.5 rounded-full hover:bg-purple-50 text-purple-500 transition-all"
                                                        title="查看历史记录"
                                                    >
                                                        <List className="w-3.5 h-3.5" />
                                                    </button>
                                                    <button 
                                                        onClick={handleRadarRefresh}
                                                        disabled={refreshingRadar}
                                                        className={cn("p-1.5 rounded-full hover:bg-purple-50 text-purple-500 transition-all", refreshingRadar && "animate-spin")}
                                                        title="立即检查"
                                                    >
                                                        <RefreshCw className="w-3.5 h-3.5" />
                                                    </button>
                                                    <span className="text-[10px] text-gray-400 bg-gray-50 px-2 py-1 rounded-full">Radar Agent</span>
                                                </div>
                                            </div>
                                            <div 
                                                className="space-y-2 cursor-pointer flex-1 flex flex-col"
                                                onClick={() => { setAlertModalType('radar'); setIsAlertModalOpen(true); }}
                                            >
                                                <div className="text-xs text-gray-600 bg-purple-50 p-2.5 rounded-lg border border-purple-100 hover:bg-purple-100 transition-colors flex-1 flex flex-col justify-between">
                                                    <div>
                                                        <span className="font-bold text-purple-700 block mb-1">
                                                            {alerts?.radar?.school_name || config?.radar?.target_school || "目标院校未设置"}
                                                        </span>
                                                        {alerts?.radar?.last_check ? (
                                                            <p className="mb-1 line-clamp-2">{alerts.radar.message}</p>
                                                        ) : (
                                                            <p className="mb-1">暂无最新公告更新。Agent 将在 {config?.radar?.schedule_time || "08:00"} 自动巡检。</p>
                                                        )}
                                                    </div>
                                                    
                                                    {alerts?.radar?.last_check && (
                                                        <div className="flex justify-between items-center mt-2">
                                                            <p className="text-[10px] text-gray-400">
                                                                上次检查: {new Date(alerts.radar.last_check * 1000).toLocaleString()}
                                                            </p>
                                                            <span className="text-[10px] text-purple-500 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                查看详情 <ChevronRight className="w-3 h-3" />
                                                            </span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Politics News */}
                                        <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow relative group flex flex-col h-full">
                                            <div className="flex justify-between items-center mb-3">
                                                <h3 className="font-bold text-gray-800 flex items-center">
                                                    <span className="w-2 h-6 bg-red-500 rounded-full mr-2"></span>
                                                    时政新闻
                                                </h3>
                                                <div className="flex items-center gap-2">
                                                    <button 
                                                        onClick={() => { setAlertModalType('politics'); setIsAlertModalOpen(true); }}
                                                        className="p-1.5 rounded-full hover:bg-red-50 text-red-500 transition-all"
                                                        title="查看历史记录"
                                                    >
                                                        <List className="w-3.5 h-3.5" />
                                                    </button>
                                                    <button 
                                                        onClick={handlePoliticsRefresh}
                                                        disabled={refreshingPolitics}
                                                        className={cn("p-1.5 rounded-full hover:bg-red-50 text-red-500 transition-all", refreshingPolitics && "animate-spin")}
                                                        title="立即检查"
                                                    >
                                                        <RefreshCw className="w-3.5 h-3.5" />
                                                    </button>
                                                    <span className="text-[10px] text-gray-400 bg-gray-50 px-2 py-1 rounded-full">Politics Agent</span>
                                                </div>
                                            </div>
                                            <div 
                                                className="space-y-2 cursor-pointer flex-1 flex flex-col"
                                                onClick={() => { setAlertModalType('politics'); setIsAlertModalOpen(true); }}
                                            >
                                                <div className="text-xs text-gray-600 bg-red-50 p-2.5 rounded-lg border border-red-100 hover:bg-red-100 transition-colors flex-1 flex flex-col justify-between">
                                                    <div>
                                                        <span className="font-bold text-red-700 block mb-1">今日要闻简报</span>
                                                        {alerts?.politics?.last_check ? (
                                                            <>
                                                                {alerts.politics.has_news && alerts.politics.news?.length > 0 ? (
                                                                    <ul className="list-disc pl-4 space-y-1 mb-1">
                                                                        {alerts.politics.news.slice(0, 2).map((item: any, i: number) => (
                                                                            <li key={i} className="line-clamp-1" title={item.title}>{item.title}</li>
                                                                        ))}
                                                                    </ul>
                                                                ) : (
                                                                    <p className="mb-1">今日暂无重要考研时政。</p>
                                                                )}
                                                            </>
                                                        ) : (
                                                            <p className="mb-1">Agent 将在 {config?.politics?.schedule_time || "08:30"} 为您推送最新考研时政热点。</p>
                                                        )}
                                                    </div>

                                                    {alerts?.politics?.last_check && (
                                                        <div className="flex justify-between items-center mt-2">
                                                            <p className="text-[10px] text-gray-400">
                                                                上次检查: {new Date(alerts.politics.last_check * 1000).toLocaleString()}
                                                            </p>
                                                            <span className="text-[10px] text-red-500 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                查看详情 <ChevronRight className="w-3 h-3" />
                                                            </span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-lg">
                                        {[
                                            { text: "📅 为我也生成一份数学复习计划", search: false },
                                            { text: "🏫 帮我分析一下浙江大学计算机", search: true },
                                            { text: "📚 考研英语一和英语二的区别？", search: true },
                                            { text: "💪 我感觉复习不下去了，由于...", search: false }
                                        ].map((item, i) => (
                                            <button
                                                key={i}
                                                onClick={() => {
                                                    // If the preset requires search, force it on; otherwise use current setting or default
                                                    const shouldSearch = item.search || isWebSearchEnabled;
                                                    // Optionally update the UI toggle too if we want to reflect it
                                                    if (item.search && !isWebSearchEnabled) setIsWebSearchEnabled(true);
                                                    
                                                    sendMessage(item.text.substring(2), { web_search_enabled: shouldSearch });
                                                }}
                                                className="px-4 py-3 bg-white border border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-lg hover:-translate-y-0.5 transition-all text-sm text-gray-700 text-left flex items-center justify-between group"
                                            >
                                                <span>{item.text}</span>
                                                <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-blue-400 opacity-0 group-hover:opacity-100 transition-all" />
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="space-y-6 pb-24">
                                {messages.map((msg, index) => (
                                    <div
                                        key={index}
                                        className={cn(
                                            "flex w-full space-x-4 items-start animate-in fade-in slide-in-from-bottom-2 duration-300",
                                            msg.role === 'user' ? "justify-end" : "justify-start"
                                        )}
                                    >
                                        {/* Bot Avatar */}
                                        {msg.role === 'assistant' && (
                                            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 text-white shadow-md mt-1">
                                                <Bot className="w-5 h-5" />
                                            </div>
                                        )}

                                        {/* Message Bubble */}
                                        <div className={cn(
                                            "max-w-[85%] md:max-w-[75%] px-6 py-4 rounded-2xl text-sm leading-relaxed shadow-sm",
                                            msg.role === 'user'
                                                ? "bg-black text-white rounded-tr-none"
                                                : "bg-white text-gray-800 rounded-tl-none border border-gray-100"
                                        )}>
                                            {/* Reasoning Display */}
                                            {msg.role === 'assistant' && (
                                                <>
                                                    {/* Check for <think> tags in content */}
                                                    {(() => {
                                                        const thinkMatch = msg.content.match(/<think>([\s\S]*?)<\/think>/);
                                                        const partialThinkMatch = !thinkMatch && msg.content.match(/<think>([\s\S]*)/);
                                                        
                                                        // Combined reasoning from orchestrator (msg.reasoning) AND model chain-of-thought (<think>)
                                                        const combinedReasoning = [
                                                            msg.reasoning, 
                                                            thinkMatch ? thinkMatch[1] : (partialThinkMatch ? partialThinkMatch[1] : null)
                                                        ].filter(Boolean).join('\n\n---\n\n');

                                                        if (combinedReasoning) {
                                                            return <ReasoningBubble content={combinedReasoning} />;
                                                        } else if (isLoading && index === messages.length - 1 && msg.content.length === 0) {
                                                            return (
                                                                <div className="flex items-center gap-2 text-gray-400 text-xs mb-2 animate-pulse">
                                                                    <Loader2 className="w-3 h-3 animate-spin" />
                                                                    <span>正在深度思考...</span>
                                                                </div>
                                                            );
                                                        }
                                                        return null;
                                                    })()}
                                                </>
                                            )}
                                            {msg.role === 'user' ? (
                                                <div className="flex flex-col gap-2">
                                                    {msg.image && (
                                                        <img 
                                                            src={msg.image} 
                                                            alt="User Upload" 
                                                            className="max-w-full rounded-lg border border-gray-700/50 mb-2 max-h-64 object-contain bg-black/20"
                                                        />
                                                    )}
                                                    <p className="whitespace-pre-wrap font-medium">
                                                        {msg.image 
                                                            ? msg.content.replace(/\n\n\[图片内容\][\s\S]*/, '') // Hide OCR text if image exists
                                                            : msg.content
                                                        }
                                                    </p>
                                                </div>
                                            ) : (
                                                <>
                                                    <ReactMarkdown
                                                        remarkPlugins={[remarkMath, remarkGfm]}
                                                        rehypePlugins={[rehypeKatex]}
                                                        className="prose prose-sm prose-neutral max-w-none dark:prose-invert break-words"
                                                        components={{
                                                            // Style tables for Planner Agent
                                                            table: ({ node, ...props }) => (
                                                                <div className="overflow-x-auto my-3 rounded-lg border border-gray-200 shadow-sm">
                                                                    <table className="min-w-full text-xs divide-y divide-gray-200" {...props} />
                                                                </div>
                                                            ),
                                                            th: ({ node, ...props }) => <th className="bg-gray-50 px-4 py-2 font-semibold text-gray-700 text-left" {...props} />,
                                                            td: ({ node, ...props }) => <td className="px-4 py-2 border-t border-gray-100" {...props} />,
                                                            code: ({ node, className, children, ...props }) => {
                                                                const match = /language-(\w+)/.exec(className || '')
                                                                return match ? (
                                                                    <div className="rounded-md bg-gray-900 mx-[-1rem] my-2 overflow-hidden">
                                                                        <div className="flex items-start justify-between px-4 py-1.5 bg-gray-800 text-xs text-gray-400">
                                                                            <span>{match[1]}</span>
                                                                        </div>
                                                                        <code className={`${className} block p-4 bg-gray-900 text-gray-100 overflow-x-auto`} {...props}>
                                                                            {children}
                                                                        </code>
                                                                    </div>
                                                                ) : (
                                                                    <code className="bg-gray-100 px-1.5 py-0.5 rounded text-red-500 font-mono text-xs" {...props}>
                                                                        {children}
                                                                    </code>
                                                                )
                                                            }
                                                        }}
                                                    >
                                                        {/* Strip <think> tags for main content display */}
                                                        {msg.content.replace(/<think>[\s\S]*?<\/think>/g, '').replace(/<think>[\s\S]*/g, '')}
                                                    </ReactMarkdown>
                                                    
                                                    {/* Blinking Cursor for active generation */}
                                                    {isLoading && index === messages.length - 1 && (
                                                        <span className="inline-block w-1.5 h-4 ml-1 bg-blue-500 animate-pulse align-middle"></span>
                                                    )}
                                                    
                                                    {/* Sources Display */}
                                                    {msg.sources && msg.sources.length > 0 && (
                                                        <div className="mt-4 pt-3 border-t border-gray-100">
                                                            <div className="flex items-center gap-1.5 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                                                <LinkIcon className="w-3 h-3" />
                                                                参考来源
                                                            </div>
                                                            <div className="max-h-40 overflow-y-auto pr-1 space-y-1 hover-scrollbar">
                                                                {msg.sources.map((source, idx) => (
                                                                    <a 
                                                                        key={idx}
                                                                        href={source.url}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="flex items-center gap-2 p-2 rounded-lg bg-gray-50 hover:bg-blue-50 border border-transparent hover:border-blue-100 transition-all group"
                                                                    >
                                                                        <div className="flex-shrink-0 w-4 h-4 rounded bg-white border border-gray-100 flex items-center justify-center text-[10px] font-bold text-gray-400 group-hover:text-blue-500 group-hover:border-blue-200">
                                                                            {idx + 1}
                                                                        </div>
                                                                        <div className="flex-1 min-w-0">
                                                                            <p className="text-xs text-gray-700 truncate group-hover:text-blue-700">
                                                                                {source.title || "未知来源"}
                                                                            </p>
                                                                        </div>
                                                                        <Globe className="w-3 h-3 text-gray-300 group-hover:text-blue-400 flex-shrink-0" />
                                                                    </a>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}

                                                    <div className="mt-2 pt-2 border-t border-gray-100/50">
                                                        <p className="text-[10px] text-gray-400 flex items-center gap-1">
                                                            <span className="inline-block w-1 h-1 rounded-full bg-gray-300"></span>
                                                            AI 可能会犯错，请核对重要信息。
                                                        </p>
                                                    </div>
                                                </>
                                            )}
                                        </div>

                                        {/* User Avatar */}
                                        {
                                            msg.role === 'user' && (
                                                <div className="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 text-gray-500 shadow-inner mt-1">
                                                    <User className="w-5 h-5" />
                                                </div>
                                            )
                                        }
                                    </div>
                                ))}



                                {error && (
                                    <div className="w-full flex justify-center py-4">
                                        <div className="flex items-center space-x-2 bg-red-50 text-red-600 px-4 py-2 rounded-full border border-red-100 text-sm shadow-sm">
                                            <X className="w-4 h-4" />
                                            <span>{error}</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Input Area (Floating) */}
                    <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-white via-white to-transparent">
                        <div className="max-w-[95%] mx-auto">
                            {/* Image Preview */}
                            {selectedImage && (
                                <div className="mb-2 flex items-center bg-white p-2 rounded-xl w-fit border border-gray-200 shadow-sm animate-in zoom-in-95">
                                    <ImageIcon className="w-4 h-4 text-blue-500 mr-2" />
                                    <span className="text-xs text-gray-600 truncate max-w-[150px]">{selectedImage.name}</span>
                                    <button
                                        onClick={() => setSelectedImage(null)}
                                        className="ml-2 p-1 hover:bg-gray-100 rounded-full transition-colors text-gray-400 hover:text-red-500"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                </div>
                            )}

                            <form onSubmit={handleSubmit} className="relative flex items-end gap-2 bg-white rounded-2xl border border-gray-200 shadow-xl shadow-blue-900/5 p-2 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-400 transition-all">
                                {/* Hidden Inputs */}
                                <input
                                    type="file"
                                    accept="image/*"
                                    ref={fileInputRef}
                                    className="hidden"
                                    onChange={handleFileSelect}
                                />
                                <input
                                    type="file"
                                    accept="image/*"
                                    capture="environment"
                                    ref={cameraInputRef}
                                    className="hidden"
                                    onChange={handleFileSelect}
                                />
                                <input
                                    type="file"
                                    accept=".pdf"
                                    ref={docInputRef}
                                    className="hidden"
                                    multiple
                                     onChange={handleDocSelect}
                                 />

                                 {/* Plus Menu Button */}
                                 <div className="relative plus-menu-container">
                                     {isPlusMenuOpen && (
                                         <div className="absolute bottom-14 left-0 bg-white border border-gray-100 rounded-xl shadow-xl p-2 min-w-[140px] flex flex-col gap-1 z-50 animate-in fade-in slide-in-from-bottom-2 duration-200">
                                             <button
                                                 type="button"
                                                 onClick={handleCameraClick}
                                                 className="flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 rounded-lg text-sm text-gray-700 transition-colors text-left"
                                             >
                                                 <div className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
                                                     <Camera className="w-4 h-4" />
                                                 </div>
                                                 <span>拍摄照片</span>
                                             </button>
                                             
                                             <button
                                                 type="button"
                                                 onClick={handleGalleryClick}
                                                 className="flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 rounded-lg text-sm text-gray-700 transition-colors text-left"
                                             >
                                                  <div className="p-1.5 bg-green-50 text-green-600 rounded-lg">
                                                     <ImageIcon className="w-4 h-4" />
                                                  </div>
                                                 <span>相册选择</span>
                                             </button>
                                             
                                             <button
                                                 type="button"
                                                 onClick={handleDocClick}
                                                 className="flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 rounded-lg text-sm text-gray-700 transition-colors text-left"
                                             >
                                                  <div className="p-1.5 bg-orange-50 text-orange-600 rounded-lg">
                                                     {isDocUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                                                  </div>
                                                 <span>上传文档</span>
                                             </button>
                                         </div>
                                     )}
                                     
                                     <button
                                         type="button"
                                         onClick={() => setIsPlusMenuOpen(!isPlusMenuOpen)}
                                         className={cn(
                                             "p-3 rounded-xl transition-all",
                                             isPlusMenuOpen ? "bg-gray-100 text-gray-900 rotate-45" : "text-gray-500 hover:bg-gray-50 hover:text-blue-600"
                                         )}
                                         title="更多功能"
                                         disabled={isLoading || isUploading || isDocUploading}
                                     >
                                         <Plus className="w-5 h-5 transition-transform duration-200" />
                                     </button>
                                 </div>

                                 <input
                                     type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="输入你的问题..."
                                    className="flex-1 bg-transparent border-none py-3 px-2 text-sm focus:ring-0 placeholder:text-gray-400 text-gray-800"
                                    disabled={isLoading || isUploading || isDocUploading}
                                />

                                <div className="flex items-center pb-0.5 gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setIsWebSearchEnabled(!isWebSearchEnabled)}
                                        className={cn(
                                            "p-2.5 rounded-xl transition-all shadow-md flex-shrink-0 flex items-center justify-center",
                                            isWebSearchEnabled
                                                ? "bg-blue-400 text-white"
                                                : "text-gray-500 hover:bg-gray-100"
                                        )}
                                        title={isWebSearchEnabled ? "已开启联网搜索" : "点击开启联网搜索"}
                                        disabled={isLoading}
                                    >
                                        <Globe className="w-5 h-5" />
                                    </button>

                                    <button
                                        type={isLoading ? "button" : "submit"}
                                        onClick={(e) => {
                                            if (isLoading) {
                                                e.preventDefault();
                                                stopGeneration();
                                            }
                                        }}
                                        disabled={(!input.trim() && !selectedImage && !isLoading)}
                                        className={cn(
                                            "p-2.5 rounded-xl transition-all shadow-md flex-shrink-0 flex items-center justify-center",
                                            isLoading
                                                ? "bg-red-500 hover:bg-red-600 text-white"
                                                : "bg-black text-white hover:bg-gray-800 disabled:opacity-50 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed"
                                        )}
                                    >
                                        {isLoading ? <Square className="w-5 h-5 fill-current" /> : <Send className="w-5 h-5" />}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
