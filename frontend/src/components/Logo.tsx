interface LogoProps {
  size?: number
  animated?: boolean
  className?: string
  'aria-hidden'?: boolean
}

export function Logo({ size = 40, animated = true, className = '', 'aria-hidden': ariaHidden }: LogoProps) {
  const s = size

  return (
    <svg
      width={s}
      height={s}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden={ariaHidden}
    >
      <defs>
        <linearGradient id="hackerSmile" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#06b6d4" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
        <filter id="hackerGlow">
          <feGaussianBlur stdDeviation="1.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <circle cx="20" cy="21" r="17" stroke="url(#hackerSmile)" strokeWidth="2.5" fill="none" filter="url(#hackerGlow)" />

      <circle cx="14" cy="15" r="2" fill="url(#hackerSmile)" />
      <circle cx="26" cy="15" r="2" fill="url(#hackerSmile)" />

      <path
        d="M 12.5 27 Q 20 33 27.5 27"
        stroke="url(#hackerSmile)"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      >
        {animated && (
          <animate
            attributeName="d"
            values="M 12.5 27 Q 20 33 27.5 27;M 12.5 27 Q 20 31 27.5 27;M 12.5 27 Q 20 33 27.5 27"
            dur="3s"
            repeatCount="indefinite"
          />
        )}
      </path>

      <line x1="6" y1="21" x2="34" y2="21" stroke="url(#hackerSmile)" strokeWidth="0.5" opacity="0.25" />
      <line x1="20" y1="3" x2="20" y2="39" stroke="url(#hackerSmile)" strokeWidth="0.5" opacity="0.25" />
    </svg>
  )
}
