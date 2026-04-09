import { FolderOpen } from 'lucide-react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

export default function NeuralInterface({ messages, isLoading, onSend, locked }) {
  return (
    <div className="relative z-50 flex h-[42dvh] w-full min-h-0 flex-col border-t border-subtle bg-base md:fixed md:right-0 md:top-0 md:h-dvh md:w-[340px] md:border-l md:border-t-0">
      <div className="h-11 flex-shrink-0 flex items-center justify-between px-4 border-b border-subtle">
        <div className="flex gap-2 items-center">
          <FolderOpen className="w-[12px] h-[12px] text-text-muted" />
          <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-sec">GIAO DIỆN</span>
        </div>
        <span className="font-mono text-[10px] text-text-muted tracking-[0.05em]">v1.0.4-LTS</span>
      </div>
      <div className="min-h-0 flex-1 overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading} />
      </div>
      <ChatInput onSend={onSend} isLoading={isLoading} locked={locked} />
    </div>
  );
}
