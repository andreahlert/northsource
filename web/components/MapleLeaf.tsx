export default function MapleLeaf({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden="true" focusable="false">
      <path
        fill="currentColor"
        d="M50 3 L56 17 L64 12 L61 30 L80 21 L74 34 L94 42 L85 49 L92 63 L64 58 L57 72 L52 65 L52 97 L48 97 L48 65 L43 72 L36 58 L8 63 L15 49 L6 42 L26 34 L20 21 L39 30 L36 12 L44 17 Z"
      />
    </svg>
  );
}
