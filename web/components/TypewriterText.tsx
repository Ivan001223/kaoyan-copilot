import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface TypewriterTextProps {
    content: string;
    onComplete?: () => void;
}

export default function TypewriterText({ content, onComplete }: TypewriterTextProps) {
    const [displayedContent, setDisplayedContent] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    
    // Use a ref to track the current animation target to avoid closures with stale state
    const targetContentRef = useRef(content);
    
    useEffect(() => {
        targetContentRef.current = content;
    }, [content]);

    useEffect(() => {
        // If content is empty, reset
        if (!content) {
            setDisplayedContent('');
            return;
        }

        // If we already displayed everything, do nothing (unless content changed to something shorter? unlikely in append-only)
        if (displayedContent === content) {
            if (isTyping) {
                setIsTyping(false);
                onComplete?.();
            }
            return;
        }

        // If content is longer, we need to type
        setIsTyping(true);
        
        const timer = setInterval(() => {
            setDisplayedContent(prev => {
                const currentLen = prev.length;
                const targetContent = targetContentRef.current;
                
                if (currentLen >= targetContent.length) {
                    clearInterval(timer);
                    setIsTyping(false);
                    onComplete?.();
                    return targetContent;
                }

                // Calculate chunk size based on remaining length to keep animation snappy
                // If there is a LOT to type (e.g. big chunk arrived), type faster
                const remaining = targetContent.length - currentLen;
                const chunkSize = remaining > 100 ? 5 : (remaining > 50 ? 3 : 1);
                
                return targetContent.slice(0, currentLen + chunkSize);
            });
        }, 10); // 10ms interval

        return () => clearInterval(timer);
    }, [content]); // Re-run when content updates

    return (
        <div className="prose prose-sm prose-neutral max-w-none dark:prose-invert break-words">
            <ReactMarkdown
                remarkPlugins={[remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
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
                {displayedContent}
            </ReactMarkdown>
            {isTyping && <span className="inline-block w-1.5 h-4 ml-1 bg-blue-500 animate-pulse align-middle"></span>}
        </div>
    );
}
