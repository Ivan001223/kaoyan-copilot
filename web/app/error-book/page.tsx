'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, RefreshCw, BookOpen, AlertCircle } from 'lucide-react';
import { api, ReviewTask, Question } from '../../services/api';

export default function ErrorBook() {
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewingTask, setReviewingTask] = useState<ReviewTask | null>(null);
  const [questionDetail, setQuestionDetail] = useState<Question | null>(null);
  const [variations, setVariations] = useState<Question[]>([]);
  const [showAnswer, setShowAnswer] = useState(false);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const data = await api.getErrorBook();
      setTasks(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const startReview = async (task: ReviewTask) => {
    setReviewingTask(task);
    setShowAnswer(false);
    setVariations([]);
    
    // If linked to a question, fetch full details
    if (task.question_id) {
        try {
            const q = await api.getQuestion(task.question_id);
            setQuestionDetail(q);
            
            // Also fetch variations
            const vars = await api.getVariations(task.question_id);
            setVariations(vars);
        } catch (e) {
            console.error("Failed to load question detail", e);
        }
    } else {
        setQuestionDetail(null);
    }
  };

  const submitFeedback = async (quality: number) => {
    if (!reviewingTask) return;
    await api.submitReview(reviewingTask.id, quality);
    setReviewingTask(null);
    loadTasks(); // Refresh list
  };

  if (loading) return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-500">
          <RefreshCw className="w-6 h-6 animate-spin mr-2" /> 加载错题本...
      </div>
  );

  // Review Mode View
  if (reviewingTask) {
      return (
          <div className="min-h-screen bg-gray-50 p-4 md:p-8">
              <div className="max-w-2xl mx-auto">
                  <button onClick={() => setReviewingTask(null)} className="mb-4 text-gray-500 hover:text-gray-800 flex items-center gap-1 transition-colors">
                      <ArrowLeft className="w-4 h-4" /> 退出复习
                  </button>
                  
                  <div className="bg-white p-8 rounded-xl shadow-lg mb-6 min-h-[300px] flex flex-col justify-between relative overflow-hidden border border-gray-100">
                      {/* Decorative elements */}
                      <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50 rounded-bl-full -mr-10 -mt-10 opacity-50 pointer-events-none"></div>
                      
                      <div>
                          <div className="text-xs font-bold text-blue-500 uppercase tracking-wide mb-2">Review Mode</div>
                          <div className="text-xl font-medium text-gray-900 mb-6 whitespace-pre-wrap leading-relaxed">
                              {questionDetail ? questionDetail.content : reviewingTask.question_text}
                          </div>
                      </div>
                      
                      {!showAnswer ? (
                          <button 
                            onClick={() => setShowAnswer(true)}
                            className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-bold shadow-md transition-transform active:scale-95"
                          >
                              显示答案
                          </button>
                      ) : (
                          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
                              <div className="bg-green-50 p-4 rounded-lg border border-green-100 mb-6">
                                  <div className="font-bold text-green-800 mb-1">正确答案</div>
                                  <div className="text-gray-800 mb-2 font-medium">{questionDetail?.answer || "See details"}</div>
                                  <div className="text-sm text-gray-600 border-t border-green-200 pt-2 mt-2">
                                    <span className="font-bold text-green-700">解析：</span>
                                    {questionDetail?.explanation || "无详细解析"}
                                  </div>
                              </div>
                              
                              <div className="grid grid-cols-4 gap-2 mb-4">
                                  <button onClick={() => submitFeedback(0)} className="p-2 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm font-bold transition-colors">忘记</button>
                                  <button onClick={() => submitFeedback(3)} className="p-2 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 text-sm font-bold transition-colors">困难</button>
                                  <button onClick={() => submitFeedback(4)} className="p-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm font-bold transition-colors">一般</button>
                                  <button onClick={() => submitFeedback(5)} className="p-2 bg-green-100 text-green-700 rounded hover:bg-green-200 text-sm font-bold transition-colors">简单</button>
                              </div>
                          </div>
                      )}
                  </div>

                  {/* Variations Section */}
                  {showAnswer && variations.length > 0 && (
                      <div className="mt-8 animate-in fade-in duration-500">
                          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                              <RefreshCw className="w-5 h-5 text-purple-500" />
                              举一反三 · 变式推荐
                          </h3>
                          <div className="space-y-4">
                              {variations.map(v => (
                                  <div key={v.id} className="bg-white p-4 rounded-lg border border-purple-100 shadow-sm hover:shadow-md transition-shadow group">
                                      <div className="flex justify-between mb-2">
                                        <span className="text-xs font-bold bg-purple-100 text-purple-700 px-2 py-0.5 rounded uppercase">{v.subject}</span>
                                        <span className="text-xs text-gray-400">{v.year}</span>
                                      </div>
                                      <div className="text-sm text-gray-800 mb-2 line-clamp-2 group-hover:text-purple-900 transition-colors">{v.content}</div>
                                      <Link href={`/practice/${v.subject}?qid=${v.id}`} className="text-xs text-purple-600 hover:underline font-medium inline-flex items-center">
                                          去练习 &rarr;
                                      </Link>
                                  </div>
                              ))}
                          </div>
                      </div>
                  )}
              </div>
          </div>
      );
  }

  // List View
  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <Link href="/practice" className="p-2 rounded-full hover:bg-gray-200 transition-colors">
                    <ArrowLeft className="w-5 h-5 text-gray-600" />
                </Link>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <BookOpen className="w-6 h-6 text-orange-500" />
                    智能错题本
                </h1>
            </div>
            <div className="text-sm text-gray-500 bg-white px-3 py-1 rounded-full border">
                待复习: {tasks.length}
            </div>
        </header>

        {tasks.length === 0 ? (
            <div className="text-center py-20 bg-white rounded-xl border border-dashed border-gray-300">
                <div className="text-4xl mb-4">✨</div>
                <div className="text-gray-500">太棒了！目前没有需要复习的错题。</div>
                <Link href="/practice" className="text-blue-500 hover:underline mt-4 inline-block font-medium">去刷题 &rarr;</Link>
            </div>
        ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tasks.map(task => (
                    <div key={task.id} className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-all group relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-1 h-full bg-orange-500"></div>
                        <div className="mb-3 pr-4">
                            <div className="text-gray-900 font-medium line-clamp-3 mb-2 min-h-[4.5rem]">
                                {task.question_text}
                            </div>
                            <div className="flex gap-2 text-xs text-gray-400">
                                <span>ID: {task.question_id || task.id}</span>
                                <span>•</span>
                                <span>复习阶段: {task.review_stage}</span>
                            </div>
                        </div>
                        
                        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-50">
                            <div className="text-xs text-orange-600 font-bold flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" />
                                待复习
                            </div>
                            <button 
                                onClick={() => startReview(task)}
                                className="px-3 py-1.5 bg-gray-900 text-white text-xs rounded-md hover:bg-gray-800 transition-colors shadow-sm"
                            >
                                开始复习
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        )}
      </div>
    </div>
  );
}
