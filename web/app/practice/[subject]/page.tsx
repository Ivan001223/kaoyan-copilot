'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, Question } from '../../../services/api';
import { QuestionCard } from '../../../components/QuestionCard';
import Link from 'next/link';
import { ArrowLeft, Loader2 } from 'lucide-react';

export default function PracticeSession() {
  const params = useParams();
  const subject = params.subject as string;
  
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (subject) {
      loadQuestions();
    }
  }, [subject]);

  const loadQuestions = async () => {
    try {
      setLoading(true);
      const data = await api.getQuestions({ subject, limit: 20 });
      setQuestions(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      alert("本组练习完成！");
    }
  };

  const handleSubmit = async (qid: number, ans: string) => {
     // Using hardcoded user_id for demo
     return await api.submitAnswer('user_1', qid, ans);
  };

  const subjectNames: Record<string, string> = {
      politics: '政治',
      english: '英语',
      math: '数学'
  };

  if (loading) {
      return (
          <div className="min-h-screen flex items-center justify-center bg-gray-50">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <span className="ml-2 text-gray-500">加载题目中...</span>
          </div>
      );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-3xl mx-auto">
        <header className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <Link href="/practice" className="p-2 rounded-full hover:bg-gray-200 transition-colors">
                    <ArrowLeft className="w-5 h-5 text-gray-600" />
                </Link>
                <h1 className="text-xl font-bold text-gray-900">{subjectNames[subject] || subject} 练习</h1>
            </div>
            <div className="text-sm text-gray-500 font-mono bg-white px-3 py-1 rounded-full border">
                {currentIndex + 1} / {questions.length}
            </div>
        </header>

        {questions.length > 0 ? (
            <div className="transition-all duration-300">
                <QuestionCard 
                    question={questions[currentIndex]} 
                    onSubmit={handleSubmit}
                    onNext={currentIndex < questions.length - 1 ? handleNext : undefined}
                />
            </div>
        ) : (
            <div className="text-center py-20 bg-white rounded-xl border border-dashed border-gray-300">
                <div className="text-4xl mb-4">📭</div>
                <div className="text-gray-500 mb-6">暂无该科目的题目。</div>
                <Link href="/practice" className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                    返回选择其他科目
                </Link>
            </div>
        )}
      </div>
    </div>
  );
}
