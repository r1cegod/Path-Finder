import { useState, useRef, useEffect } from 'react';
import { Plus, ArrowUp } from 'lucide-react';

export default function ChatInput({ onSend, isLoading, locked }) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  const handleInput = (e) => {
    setValue(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      if (!e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    }
  };

  const handleSend = () => {
    if (value.trim() === '' || isLoading) return;
    onSend(value);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  return (
    <div className="border-t border-subtle flex-shrink-0">
      <div className="mx-4 my-3 bg-elevated border border-subtle rounded-xl overflow-hidden">
        <div className="px-4 pt-3 pb-2">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={locked || isLoading}
            placeholder="Nhập tin nhắn..."
            className="w-full bg-transparent border-0 outline-none resize-none font-sans text-[14px] text-text-pri placeholder:text-text-muted leading-relaxed"
            rows={1}
            style={{ minHeight: '24px', maxHeight: '120px', overflowY: 'auto' }}
          />
        </div>
        <div className="px-4 pb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Plus className="w-[14px] h-[14px] text-text-muted" />
            <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-muted">PATHFINDERV0.1</span>
          </div>
          <button
            onClick={handleSend}
            disabled={locked || value.trim() === '' || isLoading}
            className={`w-8 h-8 rounded-full flex items-center justify-center ${
              locked || value.trim() === '' || isLoading
                ? 'bg-subtle cursor-not-allowed'
                : 'bg-accent-purple cursor-pointer hover:opacity-90 active:scale-95'
            }`}
          >
            <ArrowUp className="w-[14px] h-[14px] text-white" />
          </button>
        </div>
      </div>
      <div className="border-t border-subtle px-4 py-2 flex justify-between">
        <span className="font-mono text-[9px] uppercase tracking-wider text-text-muted">ENTER ĐỂ GỬI / SHIFT+ENTER XUỐNG DÒNG</span>
        <span className="font-mono text-[9px] uppercase tracking-wider text-text-muted">MÃ TOKEN: {value.length}</span>
      </div>
    </div>
  );
}
