import React from 'react';
import { X, Calendar, School, Newspaper, ExternalLink } from 'lucide-react';

interface AlertHistoryModalProps {
    isOpen: boolean;
    onClose: () => void;
    type: 'radar' | 'politics' | null;
    data: any;
}

export default function AlertHistoryModal({ isOpen, onClose, type, data }: AlertHistoryModalProps) {
    if (!isOpen || !type || !data) return null;

    const history = type === 'radar' ? (data.radar_history || []) : (data.politics_history || []);
    const title = type === 'radar' ? '院校监控历史' : '时政新闻历史';
    const Icon = type === 'radar' ? School : Newspaper;
    
    // Explicit classes for Tailwind JIT
    const bgLight = type === 'radar' ? 'bg-purple-50' : 'bg-red-50';
    const textMain = type === 'radar' ? 'text-purple-600' : 'text-red-600';
    const textDark = type === 'radar' ? 'text-purple-700' : 'text-red-700';

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl animate-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-gray-100">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${bgLight} ${textMain}`}>
                            <Icon className="w-6 h-6" />
                        </div>
                        <h2 className="text-xl font-bold text-gray-800">{title}</h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 bg-gray-50/50 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent">
                    {history.length > 0 ? (
                        <div className="space-y-4">
                            {history.map((item: any, index: number) => (
                                <div key={index} className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                                    {/* Timestamp */}
                                    <div className="flex items-center gap-2 text-xs text-gray-400 mb-2 pb-2 border-b border-gray-50">
                                        <Calendar className="w-3 h-3" />
                                        <span>{new Date(item.timestamp * 1000).toLocaleString()}</span>
                                    </div>

                                    {/* Radar Content */}
                                    {type === 'radar' && (
                                        <div>
                                            <h3 className={`font-bold text-sm mb-1 ${textDark}`}>
                                                {item.school_name}
                                            </h3>
                                            <p className="text-sm text-gray-700 whitespace-pre-wrap">{item.message}</p>
                                            {item.url && (
                                                <a href={item.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs text-blue-500 hover:underline mt-2 w-fit">
                                                    <ExternalLink className="w-3 h-3" />
                                                    查看来源
                                                </a>
                                            )}
                                        </div>
                                    )}

                                    {/* Politics Content */}
                                    {type === 'politics' && (
                                        <div>
                                            {item.has_news && item.news?.length > 0 ? (
                                                <div className="space-y-3">
                                                    {item.news.map((newsItem: any, i: number) => (
                                                        <div key={i} className="pl-3 border-l-2 border-red-100">
                                                            <h4 className="font-bold text-base text-gray-800 mb-1">{newsItem.title}</h4>
                                                            <p className="text-sm text-gray-700 mb-2 line-clamp-3 hover:line-clamp-none transition-all cursor-pointer leading-relaxed">
                                                                {newsItem.summary}
                                                            </p>
                                                            <div className="flex items-center justify-between mt-1">
                                                                <span className="text-xs bg-red-50 text-red-600 px-2 py-1 rounded font-medium">
                                                                    考点: {newsItem.exam_point}
                                                                </span>
                                                                {newsItem.source_url && (
                                                                    <a href={newsItem.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-600">
                                                                        <ExternalLink className="w-3 h-3" />
                                                                    </a>
                                                                )}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-sm text-gray-500 italic">本次检查未发现重要时政新闻。</p>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12 text-gray-400">
                            <p>暂无历史记录</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
