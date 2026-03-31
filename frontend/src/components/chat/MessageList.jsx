import { useEffect, useRef } from 'react';
import MessageBubble, { LoadingBubble } from './MessageBubble';

export default function MessageList({ messages, isLoading }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isLoading]);

  const lastMessage = messages[messages.length - 1];
  // show bounce dots until first token arrives (last msg is empty assistant bubble)
  const showLoading = isLoading && (
    lastMessage?.role === 'user' ||
    (lastMessage?.role === 'assistant' && !lastMessage?.content)
  );

  return (
    <div ref={containerRef} className="h-full overflow-y-auto px-4 py-4 flex flex-col gap-5">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {showLoading && <LoadingBubble />}
    </div>
  );
}
