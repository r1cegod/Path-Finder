import { FolderOpen } from 'lucide-react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

export default function NeuralInterface({ messages, isLoading, onSend }) {
  return (
    <div className="fixed right-0 top-0 w-[340px] h-screen bg-base border-l border-subtle flex flex-col z-50">
      <div className="h-11 flex-shrink-0 flex items-center justify-between px-4 border-b border-subtle">
        <div className="flex gap-2 items-center">
          <FolderOpen className="w-[12px] h-[12px] text-text-muted" />
          <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-sec">GIAO DIỆN</span>
        </div>
        <span className="font-mono text-[10px] text-text-muted tracking-[0.05em]">v1.0.4-LTS</span>
      </div>
      <div className="flex-1 overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading} />
      </div>
      <ChatInput onSend={onSend} isLoading={isLoading} />
    </div>
  );
}
