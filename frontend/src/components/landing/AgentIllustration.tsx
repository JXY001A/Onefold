/** 能力区插图 2：智能体工作流与工具连接（设计稿内联 SVG 原样移植）。 */
export default function AgentIllustration() {
  return (
    <svg viewBox="0 0 360 180" fill="none" className="h-full w-full" aria-hidden="true">
      <defs>
        <radialGradient id="landingAgentGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#9875FF" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#9875FF" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="360" height="180" fill="url(#landingAgentGlow)" />
      {/* 输入 → 工具 → 输出 连线 */}
      <path d="M56 90 C105 90, 110 46, 165 46" stroke="#668FFF" strokeOpacity="0.55" strokeWidth="1.4" />
      <path d="M56 90 L165 90" stroke="#9875FF" strokeOpacity="0.7" strokeWidth="1.4" />
      <path d="M56 90 C105 90, 110 134, 165 134" stroke="#62D6E8" strokeOpacity="0.5" strokeWidth="1.4" />
      <path d="M215 46 C260 46, 262 90, 304 90" stroke="#668FFF" strokeOpacity="0.45" strokeWidth="1.4" />
      <path d="M215 90 L304 90" stroke="#9875FF" strokeOpacity="0.6" strokeWidth="1.4" />
      <path d="M215 134 C260 134, 262 90, 304 90" stroke="#62D6E8" strokeOpacity="0.45" strokeWidth="1.4" />
      {/* 输入节点 */}
      <circle cx="56" cy="90" r="14" fill="#111A2B" stroke="#668FFF" strokeWidth="1.4" />
      <circle cx="56" cy="90" r="4" fill="#F1F5FF" />
      {/* 工具 / Skill 节点 */}
      <rect x="165" y="32" width="50" height="28" rx="6" fill="#111A2B" stroke="#668FFF" strokeOpacity="0.55" />
      <circle cx="179" cy="46" r="3" fill="#668FFF" />
      <line x1="187" y1="46" x2="205" y2="46" stroke="#A3AEC4" strokeWidth="2" strokeLinecap="round" />
      <rect x="165" y="76" width="50" height="28" rx="6" fill="#111A2B" stroke="#9875FF" strokeOpacity="0.7" />
      <circle cx="179" cy="90" r="3" fill="#9875FF" />
      <line x1="187" y1="90" x2="205" y2="90" stroke="#F1F5FF" strokeWidth="2" strokeLinecap="round" />
      <rect x="165" y="120" width="50" height="28" rx="6" fill="#111A2B" stroke="#62D6E8" strokeOpacity="0.55" />
      <circle cx="179" cy="134" r="3" fill="#62D6E8" />
      <line x1="187" y1="134" x2="205" y2="134" stroke="#A3AEC4" strokeWidth="2" strokeLinecap="round" />
      {/* 输出节点 */}
      <circle cx="304" cy="90" r="16" fill="#0B1020" stroke="#9875FF" strokeWidth="1.5" />
      <circle cx="304" cy="90" r="5" fill="#62D6E8" />
    </svg>
  );
}
