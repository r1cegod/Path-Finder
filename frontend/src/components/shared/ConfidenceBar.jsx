export default function ConfidenceBar({ value }) {
  const getColor = (val) => {
    if (val >= 0.8) return 'bg-[#10B981]';
    if (val >= 0.5) return 'bg-[#F59E0B]';
    return 'bg-[#EF4444]';
  };

  return (
    <div>
      <div className="w-full h-1.5 bg-subtle rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full ${getColor(value)}`} 
          style={{ width: `${value * 100}%` }} 
        />
      </div>
      <div className="font-mono text-[10px] text-text-muted tracking-[0.05em] text-right mt-1">
        {value.toFixed(2)}
      </div>
    </div>
  );
}
