/** 能力区插图 1：信息节点与知识综合（设计稿内联 SVG 原样移植）。 */
export default function ResearchIllustration() {
  return (
    <svg viewBox="0 0 540 180" fill="none" className="h-full w-full" aria-hidden="true">
      <defs>
        <radialGradient id="landingResGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#668FFF" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#668FFF" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="540" height="180" fill="url(#landingResGlow)" />
      {/* 连线 */}
      <path d="M90 55 L210 90 L330 52 L445 90" stroke="#568BFF" strokeOpacity="0.4" strokeWidth="1.2" />
      <path d="M110 132 L210 90 L315 130 L445 90" stroke="#9875FF" strokeOpacity="0.35" strokeWidth="1.2" />
      <path
        d="M210 90 L270 36 L330 52"
        stroke="#62D6E8"
        strokeOpacity="0.45"
        strokeWidth="1"
        strokeDasharray="3 3"
      />
      {/* 文档节点 */}
      <rect x="44" y="36" width="92" height="38" rx="6" fill="#111A2B" stroke="#668FFF" strokeOpacity="0.35" />
      <line x1="56" y1="50" x2="104" y2="50" stroke="#F1F5FF" strokeOpacity="0.55" strokeWidth="2" strokeLinecap="round" />
      <line x1="56" y1="60" x2="120" y2="60" stroke="#6E7E99" strokeOpacity="0.7" strokeWidth="2" strokeLinecap="round" />
      <rect x="64" y="114" width="92" height="36" rx="6" fill="#111A2B" stroke="#9875FF" strokeOpacity="0.35" />
      <line x1="76" y1="128" x2="124" y2="128" stroke="#A3AEC4" strokeOpacity="0.5" strokeWidth="2" strokeLinecap="round" />
      <line x1="76" y1="138" x2="138" y2="138" stroke="#6E7E99" strokeOpacity="0.6" strokeWidth="2" strokeLinecap="round" />
      {/* 中心综合核心 */}
      <circle cx="210" cy="90" r="22" fill="#0B1020" stroke="#62D6E8" strokeOpacity="0.6" strokeWidth="1.4" />
      <circle cx="210" cy="90" r="6" fill="#62D6E8" />
      {/* 右侧结构化输出 */}
      <circle cx="330" cy="52" r="5" fill="#668FFF" />
      <circle cx="315" cy="130" r="4.5" fill="#9875FF" />
      <circle cx="270" cy="36" r="3.5" fill="#62D6E8" />
      <rect x="405" y="64" width="102" height="52" rx="8" fill="#111A2B" stroke="#62D6E8" strokeOpacity="0.45" />
      <line x1="420" y1="81" x2="480" y2="81" stroke="#F1F5FF" strokeOpacity="0.8" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="420" y1="93" x2="492" y2="93" stroke="#668FFF" strokeOpacity="0.7" strokeWidth="2" strokeLinecap="round" />
      <line x1="420" y1="103" x2="466" y2="103" stroke="#6E7E99" strokeOpacity="0.7" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
