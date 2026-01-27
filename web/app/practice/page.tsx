'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function PracticeHub() {
  const subjects = [
    { id: 'politics', name: '政治', icon: '🇨🇳', desc: '马原、毛中特、史纲、思修', color: 'bg-red-50 text-red-700 border-red-200' },
    { id: 'english', name: '英语', icon: '🔤', desc: '阅读、完型、翻译、写作', color: 'bg-blue-50 text-blue-700 border-blue-200' },
    { id: 'math', name: '数学', icon: '📐', desc: '高等数学、线性代数、概率论', color: 'bg-green-50 text-green-700 border-green-200' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8 flex items-center gap-4">
            <Link href="/" className="p-2 rounded-full hover:bg-gray-200 transition-colors">
                <ArrowLeft className="w-5 h-5 text-gray-600" />
            </Link>
            <div>
                <h1 className="text-2xl font-bold text-gray-900">智能刷题</h1>
                <p className="text-gray-500">选择科目开始练习，系统将自动记录错题</p>
            </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {subjects.map((sub) => (
            <Link key={sub.id} href={`/practice/${sub.id}`}>
              <div className={`h-full p-6 rounded-xl border transition-all hover:shadow-lg hover:-translate-y-1 cursor-pointer bg-white shadow-sm hover:border-blue-300 group`}>
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-2xl mb-4 ${sub.color}`}>
                    {sub.icon}
                </div>
                <h2 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">{sub.name}</h2>
                <p className="text-sm text-gray-500">{sub.desc}</p>
              </div>
            </Link>
          ))}
        </div>
        
        <div className="mt-8 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-gray-800">学习工具</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 <Link href="/error-book" className="flex items-center gap-4 p-4 rounded-lg border border-gray-100 hover:bg-orange-50 hover:border-orange-200 transition-colors group">
                    <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 group-hover:scale-110 transition-transform">
                        📚
                    </div>
                    <div>
                        <div className="font-bold text-gray-800 group-hover:text-orange-700">智能错题本</div>
                        <div className="text-xs text-gray-500">自动收录错题，举一反三推荐变式</div>
                    </div>
                 </Link>
                 
                 <div className="flex items-center gap-4 p-4 rounded-lg border border-gray-100 opacity-60 cursor-not-allowed">
                    <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">
                        🏆
                    </div>
                    <div>
                        <div className="font-bold text-gray-800">全真模考</div>
                        <div className="text-xs text-gray-500">即将上线</div>
                    </div>
                 </div>
            </div>
        </div>
      </div>
    </div>
  );
}
