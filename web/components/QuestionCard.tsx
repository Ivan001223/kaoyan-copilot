import React, { useState, useEffect } from 'react';
import { Question } from '../services/api';

interface QuestionCardProps {
  question: Question;
  onSubmit: (questionId: number, answer: string) => Promise<{ is_correct: boolean; explanation: string }>;
  onNext?: () => void;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({ question, onSubmit, onNext }) => {
  const [selected, setSelected] = useState<string>('');
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<{ is_correct: boolean; explanation: string } | null>(null);

  // Reset state when question changes
  useEffect(() => {
    setSelected('');
    setSubmitted(false);
    setResult(null);
  }, [question.id]);

  const handleSubmit = async () => {
    if (!selected) return;
    const res = await onSubmit(question.id, selected);
    setResult(res);
    setSubmitted(true);
  };

  const handleSelect = (label: string) => {
      if (submitted) return;
      
      if (question.type === 'multi_choice') {
          // Toggle selection for multi choice
          // Note: Logic for multi-choice strings like "ABCD" needs to be handled
          // Here we just handle single select logic for UI simplicity in this MVP
          // Or implementing basic multi select:
          const current = new Set(selected.split(''));
          if (current.has(label)) current.delete(label);
          else current.add(label);
          setSelected(Array.from(current).sort().join(''));
      } else {
          setSelected(label);
      }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-4 border border-gray-100">
      <div className="flex justify-between items-center mb-4">
        <div className="flex gap-2">
            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full uppercase font-bold">
            {question.subject}
            </span>
            <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
            {question.type === 'multi_choice' ? '多选题' : '单选题'}
            </span>
        </div>
        <span className="text-gray-400 text-sm">{question.year} {question.source}</span>
      </div>
      
      <h3 className="text-lg font-medium mb-4 whitespace-pre-wrap">{question.content}</h3>
      
      <div className="space-y-3 mb-6">
        {Array.isArray(question.options) ? question.options.map((opt: string) => {
            // Extract label A, B, C... safely
            const match = opt.match(/^([A-Z])\./);
            const label = match ? match[1] : opt[0]; 
            
            const isSelected = selected.includes(label);
            const isAnswer = submitted && question.answer.includes(label);
            
            return (
                <div 
                    key={opt}
                    onClick={() => handleSelect(label)}
                    className={`p-3 rounded-md border cursor-pointer transition-colors flex items-start gap-3
                        ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'}
                        ${submitted && isAnswer ? '!bg-green-100 !border-green-500' : ''}
                        ${submitted && isSelected && !isAnswer ? '!bg-red-100 !border-red-500' : ''}
                    `}
                >
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs border shrink-0 mt-0.5
                        ${isSelected ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-500 border-gray-300'}
                        ${submitted && isAnswer ? '!bg-green-500 !border-green-500 !text-white' : ''}
                        ${submitted && isSelected && !isAnswer ? '!bg-red-500 !border-red-500 !text-white' : ''}
                    `}>
                        {label}
                    </div>
                    <div className="text-gray-800">{opt.substring(opt.indexOf('.') + 1) || opt}</div>
                </div>
            );
        }) : (
            <div>Unsupported option format</div>
        )}
      </div>
      
      {!submitted ? (
        <button 
            onClick={handleSubmit}
            disabled={!selected}
            className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-300 transition-colors font-medium"
        >
            提交答案
        </button>
      ) : (
        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className={`p-4 rounded-md mb-4 border ${result?.is_correct ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                <div className="font-bold mb-1 flex items-center gap-2">
                    {result?.is_correct ? (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    )}
                    {result?.is_correct ? '回答正确' : '回答错误'}
                </div>
                <div className="text-sm ml-7">正确答案：<span className="font-bold">{question.answer}</span></div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-md text-sm text-gray-700 mb-4 border border-gray-200">
                <span className="font-bold block mb-1 text-gray-900">🎓 解析：</span>
                <div className="leading-relaxed">{result?.explanation}</div>
            </div>
            
            {onNext && (
                <button 
                    onClick={onNext}
                    className="w-full bg-gray-900 text-white py-2 rounded-md hover:bg-gray-800 transition-colors font-medium"
                >
                    下一题
                </button>
            )}
        </div>
      )}
    </div>
  );
};
