export default function Card({ title, children, className = '' }) {
  return (
    <div className={`bg-surface border border-subtle rounded-lg p-5 ${className}`}>
      {title && <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-text-label mb-4">{title}</div>}
      {children}
    </div>
  );
}
