import { useEffect, useRef, useState } from 'react';
import { ArrowUp, Plus } from 'lucide-react';

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
      el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
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

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-shrink-0 border-t border-subtle">
      <div className="mx-4 my-3 overflow-hidden rounded-xl border border-subtle bg-elevated">
        <div className="px-4 pb-2 pt-3">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={locked || isLoading}
            placeholder="Nhập tin nhắn..."
            className="w-full resize-none border-0 bg-transparent font-sans text-[14px] leading-relaxed text-text-pri outline-none placeholder:text-text-muted"
            rows={1}
            style={{ minHeight: '24px', maxHeight: '120px', overflowY: 'auto' }}
          />
        </div>

        <div className="flex items-center justify-between px-4 pb-3">
          <div className="flex items-center gap-2">
            <Plus className="h-[14px] w-[14px] text-text-muted" />
            <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-muted">PATHFINDERV0.1</span>
          </div>

          <button
            onClick={handleSend}
            disabled={locked || value.trim() === '' || isLoading}
            className={`flex h-8 w-8 items-center justify-center rounded-full ${
              locked || value.trim() === '' || isLoading
                ? 'cursor-not-allowed bg-subtle'
                : 'cursor-pointer bg-accent-purple hover:opacity-90 active:scale-95'
            }`}
          >
            <ArrowUp className="h-[14px] w-[14px] text-white" />
          </button>
        </div>
      </div>

      <div className="border-t border-subtle px-4 py-2">
        <span className="font-mono text-[9px] uppercase tracking-wider text-text-muted">ENTER ĐỂ GỬI / SHIFT+ENTER XUỐNG DÒNG</span>
      </div>
    </div>
  );
}
