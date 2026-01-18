import { useState, useCallback } from 'react';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  reasoning?: string; // New field for reasoning
}

export function useLLMStream() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const stopGeneration = useCallback(() => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setIsLoading(false);
    }
  }, [abortController]);

  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true);
    setError(null);

    // 乐观地添加用户消息
    const userMessage: Message = { role: 'user', content };
    setMessages((prev) => [...prev, userMessage]);

    const controller = new AbortController();
    setAbortController(controller);

    try {
      // 1. 准备请求
      // Map frontend 'role' to backend 'type' (human/ai) for LangChain processing
      const backendMessages = messages.map(msg => ({
        type: msg.role === 'user' ? 'human' : 'ai',
        content: msg.content
      }));

      // Add current message
      backendMessages.push({ type: 'human', content: userMessage.content });

      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: {
            messages: backendMessages
          }
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Backend Error:", response.status, errorText);
        throw new Error(`Network Error: ${response.status} ${response.statusText} - ${errorText}`);
      }

      if (!response.body) return;

      // 2. 为助手添加占位符缓冲区
      setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

      // 3. 读取循环
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage: Partial<Message> = { content: '', reasoning: '' }; // Changed to object

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            // Track event type if needed, but we mainly care about data
          }
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6);
              const data = JSON.parse(jsonStr);

              // LangGraph/LangServe distinct event types:

              // 1. "messages" event (Streaming token chunks)
              // This is often for the FINAL answer content
              if (data?.messages && Array.isArray(data.messages)) {
                // Logic to append content chunks...
                // But wait, LangServe usually streams "ops" or "messages".
                // If we use .stream() on the graph, we get state updates.
              }

              // 2. "values" event (Full State Update)
              // This comes from `stream_mode="values"`. It contains the complete new state.
              // We updated the backend to output "reasoning" in the state.
              if (data?.reasoning) {
                // Direct reasoning update (if top-level)
                assistantMessage.reasoning = data.reasoning;
              }

              if (data?.values) {
                if (data.values.reasoning) {
                  assistantMessage.reasoning = data.values.reasoning;
                }
              }

              // 4. Node specific updates (LangGraph streaming)
              if (data?.orchestrator?.reasoning) {
                  assistantMessage.reasoning = data.orchestrator.reasoning;
              }
              
              // Handle other agents' responses which are in 'messages'
              // Iterate over keys to find any agent output containing messages
              Object.keys(data || {}).forEach(key => {
                  if (key === 'orchestrator') return; // Handled above
                  
                  if (data[key]?.messages && Array.isArray(data[key].messages)) {
                      const msgs = data[key].messages;
                      const lastMsg = msgs[msgs.length - 1];
                      // Check for content in various formats (LangChain message or dict)
                      const content = lastMsg.content || lastMsg.kwargs?.content;
                      
                      if (content) {
                          assistantMessage.content = content;
                      }
                  }
              });

              // 3. Content updates
              // If we are getting content chunks
              if (data?.content) {
                assistantMessage.content += data.content;
              } else if (typeof data === 'string') {
                // Check if string itself looks like reasoning (unlikely but possible if misconfigured)
                assistantMessage.content += data;
              }
              // Also check for messages in values
              if (data?.values?.messages) {
                const msgs = data.values.messages;
                const lastMsg = msgs[msgs.length - 1];
                if (lastMsg.type === 'ai') {
                  assistantMessage.content = lastMsg.content;
                }
              }

            } catch (e) {
              // Ignore parse errors for partial chunks
            }
          }
        }

        // Update state
        setMessages((prev) => {
          const newArr = [...prev];
          // Ensure we preserve previous reasoning if not updated in this chunk
          // Actually, we should accumulate or replace based on what we get.
          // For simplicity, let's keep the object reference updated.
          const currentMsg = newArr[newArr.length - 1];
          newArr[newArr.length - 1] = {
            ...currentMsg,
            role: 'assistant',
            content: assistantMessage.content || currentMsg.content || '', // Ensure content is always a string
            reasoning: assistantMessage.reasoning || currentMsg.reasoning
          };
          return newArr;
        });
      }

    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Generation stopped by user');
      } else {
        setError(err.message || '出错了');
      }
    } finally {
      setIsLoading(false);
      setAbortController(null);
    }
  }, [messages]);

  return { messages, sendMessage, stopGeneration, isLoading, error, setMessages };
}
