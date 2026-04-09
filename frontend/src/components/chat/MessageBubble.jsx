export default function MessageBubble({ message }) {
  const { role, content, timestamp, isError } = message;
  const fmt = (d) => d.toTimeString().slice(0, 8);

  const formatContent = (text) => {
    if (!text) return null;
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
        return (
          <span key={index} className="text-accent-amber font-bold">
            {part.slice(2, -2)}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  if (role === 'assistant') {
    return (
      <div className="flex flex-col">
        <div className={`font-mono text-[13px] leading-relaxed break-words whitespace-pre-wrap ${isError ? 'text-accent-red' : 'text-sys-msg'}`}>
          {formatContent(content)}
        </div>
        <div className="flex justify-end mt-2">
          <span className="font-mono text-[10px] text-text-muted tracking-[0.05em]">
            SYSTEM_CORE // {fmt(timestamp)}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-end">
      <div className="flex flex-col max-w-[85%]">
        <div className="bg-elevated border border-subtle rounded-lg rounded-tr-sm px-4 py-3 font-sans text-[14px] text-text-pri break-words whitespace-pre-wrap">
          {formatContent(content)}
        </div>
        <div className="flex justify-end mt-2">
          <span className="font-mono text-[10px] text-text-muted tracking-[0.05em]">
            OPERATOR // {fmt(timestamp)}
          </span>
        </div>
      </div>
    </div>
  );
}

export function LoadingBubble() {
  return (
    <div className="flex flex-col">
      <div className="flex gap-1.5 items-center h-5">
        <div className="w-1.5 h-1.5 rounded-full bg-text-muted animate-loading-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-1.5 h-1.5 rounded-full bg-text-muted animate-loading-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-1.5 h-1.5 rounded-full bg-text-muted animate-loading-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
}
