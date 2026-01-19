import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, BrainCircuit } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ReasoningBubbleProps {
    content: string;
}

export default function ReasoningBubble({ content }: ReasoningBubbleProps) {
    const [isExpanded, setIsExpanded] = useState(true); // Default to expanded to show the typing
    const [displayedContent, setDisplayedContent] = useState('');
    const [isTyping, setIsTyping] = useState(false);

    // Typewriter effect
    useEffect(() => {
        if (!content) return;
        
        // If content is already fully displayed, don't restart (unless content changed significantly)
        if (displayedContent === content) return;

        // If content grew (streaming), append new chars
        // But since we receive the FULL content at once from the backend (state update),
        // we can just animate from 0 to full if it's a fresh arrival.
        
        if (content.length > displayedContent.length) {
            setIsTyping(true);
            let index = displayedContent.length;
            
            // Adjust speed based on length to not be too slow for long thoughts
            const speed = content.length > 200 ? 5 : 15; 
            
            const timer = setInterval(() => {
                if (index < content.length) {
                    setDisplayedContent(prev => content.slice(0, index + 1));
                    index++;
                } else {
                    clearInterval(timer);
                    setIsTyping(false);
                }
            }, speed);

            return () => clearInterval(timer);
        }
    }, [content]);

    if (!content) return null;

    return (
        <div className="w-full mb-2">
            <div
                className="flex items-center gap-2 cursor-pointer text-gray-500 hover:text-gray-700 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className={`p-1 rounded bg-gray-100 dark:bg-gray-800 ${isTyping ? 'animate-pulse' : ''}`}>
                    <BrainCircuit className="w-4 h-4" />
                </div>
                <span className="text-xs font-medium">
                    {isTyping ? '正在思考...' : '思考过程'}
                </span>
                {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            </div>

            {isExpanded && (
                <div className="mt-2 ml-2 pl-4 border-l-2 border-gray-200 dark:border-gray-700 animate-in fade-in slide-in-from-top-1 duration-200">
                    {(displayedContent || content).split(/\n\s*---\s*\n/).map((part, index, array) => (
                        <div key={index} className="bg-gray-50 dark:bg-gray-900/50 p-3 rounded-lg font-mono leading-relaxed break-words mb-2 last:mb-0">
                            <ReactMarkdown 
                                remarkPlugins={[remarkGfm]}
                                className="prose prose-sm prose-neutral dark:prose-invert max-w-none text-xs text-gray-600 dark:text-gray-400 [&>p]:my-1 [&>ul]:my-1 [&>ol]:my-1 [&>li]:my-0.5"
                            >
                                {part}
                            </ReactMarkdown>
                            {isTyping && index === array.length - 1 && <span className="inline-block w-1.5 h-3 ml-1 bg-blue-400 animate-pulse align-middle"></span>}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
