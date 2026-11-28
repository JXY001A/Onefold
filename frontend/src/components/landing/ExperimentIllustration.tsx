/** 能力区插图 3：神经网络晶格与实验场（设计稿内联 SVG 原样移植）。 */
export default function ExperimentIllustration() {
  return (
    <svg viewBox="0 0 680 160" fill="none" className="h-full w-full" aria-hidden="true">
      <defs>
        <linearGradient id="landingExpLine" x1="0" y1="80" x2="680" y2="80" gradientUnits="userSpaceOnUse">
          <stop stopColor="#568BFF" stopOpacity="0.1" />
          <stop offset="0.5" stopColor="#9875FF" stopOpacity="0.65" />
          <stop offset="1" stopColor="#62D6E8" stopOpacity="0.15" />
        </linearGradient>
      </defs>
      <path d="M20 110 C120 30, 220 140, 340 72 C450 12, 560 130, 660 55" stroke="url(#landingExpLine)" strokeWidth="1.6" />
      <path
        d="M20 65 C140 130, 260 20, 380 95 C490 155, 580 40, 660 95"
        stroke="#568BFF"
        strokeOpacity="0.32"
        strokeWidth="1.2"
        strokeDasharray="4 4"
      />
      {/* 晶格节点 */}
      <circle cx="120" cy="64" r="4" fill="#668FFF" />
      <circle cx="220" cy="106" r="3.5" fill="#9875FF" />
      <circle cx="340" cy="72" r="7" fill="#0B1020" stroke="#62D6E8" strokeWidth="1.5" />
      <circle cx="340" cy="72" r="2.5" fill="#F1F5FF" />
      <circle cx="465" cy="48" r="4.5" fill="#9875FF" />
      <circle cx="560" cy="98" r="4" fill="#62D6E8" />
      <line x1="120" y1="64" x2="220" y2="106" stroke="#668FFF" strokeOpacity="0.28" />
      <line x1="220" y1="106" x2="340" y2="72" stroke="#9875FF" strokeOpacity="0.35" />
      <line x1="340" y1="72" x2="465" y2="48" stroke="#62D6E8" strokeOpacity="0.35" />
      <line x1="465" y1="48" x2="560" y2="98" stroke="#668FFF" strokeOpacity="0.28" />
    </svg>
  );
}
