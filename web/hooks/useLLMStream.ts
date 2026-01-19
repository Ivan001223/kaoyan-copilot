import { useState, useCallback } from 'react';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  reasoning?: string;
  sources?: { title: string; url: string; content: string }[];
  image?: string; // URL for the image
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

  const sendMessage = useCallback(async (content: string, options?: { web_search_enabled?: boolean, image?: string }) => {
    setIsLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage: Message = { role: 'user', content, image: options?.image };
    setMessages((prev) => [...prev, userMessage]);

    const controller = new AbortController();
    setAbortController(controller);

    try {
      // Prepare backend messages
      const backendMessages = messages.map(msg => {
          if (msg.role === 'user' && msg.image) {
              return {
                  type: 'human',
                  content: [
                      { type: 'text', text: msg.content },
                      { type: 'image_url', image_url: { url: msg.image } }
                  ]
              };
          }
          return {
            type: msg.role === 'user' ? 'human' : 'ai',
            content: msg.content
          };
      });

      // Add current user message
      if (userMessage.image) {
          backendMessages.push({
              type: 'human',
              content: [
                  { type: 'text', text: userMessage.content },
                  { type: 'image_url', image_url: { url: userMessage.image } }
              ]
          });
      } else {
          backendMessages.push({ type: 'human', content: userMessage.content });
      }

      // Use stream_events for granular token streaming
      const response = await fetch('http://localhost:8000/chat/stream_events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: {
            messages: backendMessages,
            web_search_enabled: options?.web_search_enabled
          },
          config: {
            configurable: {}
          },
          version: 'v2' // Request stream_events v2
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Network Error: ${response.status} ${response.statusText} - ${errorText}`);
      }

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let currentReasoning = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('event: data')) {
             // LangServe SSE format:
             // event: data
             // data: {...}
             // But sometimes it is:
             // event: ...
             // data: ...
             // We need to look for lines starting with 'data: '
          }
          
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6);
              const eventData = JSON.parse(jsonStr);
              const eventType = eventData.event;
              const metadata = eventData.metadata || {};
              const node = metadata.langgraph_node;
              
              // console.log("Event:", eventType, "Node:", node, "Data:", eventData.data); // Debug

              // --- 1. Handle Reasoning (from Orchestrator) ---
              // When orchestrator finishes, it yields the RouteDecision
              // 'on_chain_end' for node 'orchestrator'
              if (eventType === 'on_chain_end' && node === 'orchestrator') {
                 // Check if it's the final output of the node
                 const output = eventData.data?.output;
                 if (output && output.reasoning) {
                     currentReasoning = output.reasoning;
                 }
              }

              // --- 2. Handle Content Streaming (from Agents) ---
              if (eventType === 'on_chat_model_stream') {
                // Ignore orchestrator's stream (it's internal decision making)
                if (node === 'orchestrator') continue;

                // Also ignore empty chunks or tool call chunks (which have empty content usually)
                const content = eventData.data?.chunk?.content;
                
                if (content && typeof content === 'string') {
                  setMessages(prev => {
                    const newArr = [...prev];
                    const lastIdx = newArr.length - 1;
                    const lastMsg = newArr[lastIdx];

                    // Helper to separate <think> content
                    const processContent = (rawContent: string) => {
                        let displayContent = rawContent;
                        let thoughtContent = "";
                        
                        // Check for <think> tags
                        const thinkMatch = rawContent.match(/<think>([\s\S]*?)<\/think>/);
                        if (thinkMatch) {
                            thoughtContent = thinkMatch[1];
                            displayContent = rawContent.replace(/<think>[\s\S]*?<\/think>/, '').trim();
                        } else {
                            // Handle partial streaming (e.g., starts with <think> but no closing tag yet)
                            const openMatch = rawContent.match(/<think>([\s\S]*)/);
                            if (openMatch) {
                                thoughtContent = openMatch[1];
                                displayContent = ""; // Hide everything until closing tag or handle partial display if UI supports it
                            }
                        }
                        return { displayContent, thoughtContent };
                    };

                    // Note: Since we are appending chunks, parsing full XML tags in stream is tricky.
                    // A simpler approach for the UI is to store the FULL raw content,
                    // and let the UI component (ChatInterface) parse and separate the <think> block.
                    // So here we just append the raw content.
                    
                    const newRawContent = (lastMsg.role === 'user' ? '' : lastMsg.content) + content;

                    if (lastMsg.role === 'user') {
                      newArr.push({
                        role: 'assistant',
                        content: newRawContent,
                        reasoning: currentReasoning,
                        sources: undefined
                      });
                    } else {
                      newArr[lastIdx] = {
                        ...lastMsg,
                        content: newRawContent,
                        reasoning: currentReasoning || lastMsg.reasoning
                      };
                    }
                    return newArr;
                  });
                }
              }

              // --- 3. Handle Sources (from Final Agent Output) ---
              // The agents return a dict with "messages" list.
              // The last message in that list has 'additional_kwargs.sources'.
              // We can catch 'on_chain_end' for the specific agent node.
              const agentNodes = ['consultant', 'tutor', 'radar', 'politics']; // Add other nodes if they return sources
              if (eventType === 'on_chain_end' && agentNodes.includes(node)) {
                  const outputMessages = eventData.data?.output?.messages;
                  if (outputMessages && Array.isArray(outputMessages)) {
                      const lastMsg = outputMessages[outputMessages.length - 1];
                      // Note: In stream_events, the message object might be serialized differently.
                      // Usually it's a dict with 'content', 'additional_kwargs', etc.
                      const sources = lastMsg?.additional_kwargs?.sources;
                      
                      if (sources && Array.isArray(sources) && sources.length > 0) {
                          setMessages(prev => {
                              const newArr = [...prev];
                              const lastIdx = newArr.length - 1;
                              if (newArr[lastIdx].role === 'assistant') {
                                  newArr[lastIdx] = {
                                      ...newArr[lastIdx],
                                      sources: sources
                                  };
                              }
                              return newArr;
                          });
                      }
                  }
              }

            } catch (e) {
              // Ignore parse errors for partial lines
            }
          }
        }
      }

    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Generation stopped by user');
      } else {
        setError(err.message || 'Error occurred');
      }
    } finally {
      setIsLoading(false);
      setAbortController(null);
    }
  }, [messages]);

  return { messages, sendMessage, stopGeneration, isLoading, error, setMessages };
}
