/** Hero 3D 神经网络宇宙引擎：节点/粒子/连线参数与设计稿脚本逐项一致。
 * 负责动画生命周期：reduced-motion 时只渲染静态帧（用户已批准的保护偏差 a），
 * 页面不可见时暂停循环（保护偏差 b），卸载时清理全部监听。 */

const NODE_COUNT = 68;
const PARTICLE_COUNT = 36;
const PALETTE = ["#668FFF", "#568BFF", "#9875FF", "#62D6E8", "#F1F5FF"];

interface Node3D {
  x: number;
  y: number;
  z: number;
  color: string;
  size: number;
  phase: number;
}

interface Particle3D {
  x: number;
  y: number;
  z: number;
  size: number;
  phase: number;
}

export function startNeuralUniverse(canvas: HTMLCanvasElement): () => void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return () => {};

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);

  const nodes: Node3D[] = [];
  for (let i = 0; i < NODE_COUNT; i++) {
    // 斐波那契球面分布
    const phi = Math.acos(1 - (2 * (i + 0.5)) / NODE_COUNT);
    const theta = Math.PI * (1 + Math.sqrt(5)) * i;
    const r = 0.72 + (i % 5) * 0.07;
    nodes.push({
      x: r * Math.sin(phi) * Math.cos(theta),
      y: r * Math.sin(phi) * Math.sin(theta),
      z: r * Math.cos(phi),
      color: PALETTE[i % PALETTE.length],
      size: 1.8 + (i % 4) * 0.85,
      phase: i * 0.45,
    });
  }

  const particles: Particle3D[] = [];
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push({
      x: (Math.random() - 0.5) * 2.4,
      y: (Math.random() - 0.5) * 2.0,
      z: (Math.random() - 0.5) * 1.8,
      size: 0.8 + Math.random() * 1.3,
      phase: Math.random() * Math.PI * 2,
    });
  }

  let width = 0;
  let height = 0;
  let targetX = 0;
  let targetY = 0;
  let currentX = 0;
  let currentY = 0;
  const angleY = 0.4;
  const angleX = 0.22;
  let raf = 0;
  let running = false;

  const draw = (time: number) => {
    const t = time * 0.001;
    ctx.clearRect(0, 0, width, height);

    currentX += (targetX - currentX) * 0.04;
    currentY += (targetY - currentY) * 0.04;

    const rotY = angleY + t * 0.14 + currentX;
    const rotX = angleX + Math.sin(t * 0.2) * 0.08 + currentY;
    const cosY = Math.cos(rotY);
    const sinY = Math.sin(rotY);
    const cosX = Math.cos(rotX);
    const sinX = Math.sin(rotX);

    const radiusScale = Math.min(width, height) * 0.38;
    const cx = width * 0.5;
    const cy = height * 0.5;

    // 轨道环
    ctx.save();
    ctx.translate(cx, cy);
    ctx.strokeStyle = "rgba(102, 143, 255, 0.12)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.ellipse(0, 0, radiusScale * 1.18, radiusScale * 0.42, -0.28, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = "rgba(152, 117, 255, 0.10)";
    ctx.beginPath();
    ctx.ellipse(0, 0, radiusScale * 1.05, radiusScale * 0.36, 0.52, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    // 星尘粒子
    for (const p of particles) {
      const py = p.y + Math.sin(t * 0.6 + p.phase) * 0.06;
      const sx = cx + p.x * radiusScale * 1.25;
      const sy = cy + py * radiusScale * 1.15;
      const alpha = 0.2 + 0.25 * Math.sin(t * 1.2 + p.phase);
      ctx.fillStyle = `rgba(163, 174, 196, ${alpha.toFixed(2)})`;
      ctx.beginPath();
      ctx.arc(sx, sy, p.size, 0, Math.PI * 2);
      ctx.fill();
    }

    // 三维投影
    const projected = nodes.map((n) => {
      const x1 = n.x * cosY - n.z * sinY;
      const z1 = n.z * cosY + n.x * sinY;
      const y2 = n.y * cosX - z1 * sinX;
      const z2 = z1 * cosX + n.y * sinX;
      const perspective = 2.6 / (2.6 - z2);
      return {
        x: cx + x1 * radiusScale * perspective,
        y: cy + y2 * radiusScale * perspective,
        z: z2,
        scale: perspective,
        color: n.color,
        size: n.size,
        phase: n.phase,
      };
    });

    // 突触连线
    const maxDist = radiusScale * 0.68;
    for (let i = 0; i < projected.length; i++) {
      for (let j = i + 1; j < projected.length; j++) {
        const a = projected[i];
        const b = projected[j];
        const dist = Math.hypot(a.x - b.x, a.y - b.y);
        if (dist < maxDist) {
          const depthAlpha = Math.max(0.05, ((a.z + b.z) * 0.5 + 1.2) * 0.16);
          const alpha = depthAlpha * (1 - dist / maxDist);
          ctx.strokeStyle =
            (i + j) % 3 === 0
              ? `rgba(152, 117, 255, ${alpha.toFixed(3)})`
              : `rgba(102, 143, 255, ${alpha.toFixed(3)})`;
          ctx.lineWidth = 0.85;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }

    // 由远及近绘制节点
    projected.sort((a, b) => a.z - b.z);
    for (const p of projected) {
      const pulse = 0.78 + 0.22 * Math.sin(t * 2.2 + p.phase);
      const alpha = Math.min(1, Math.max(0.25, (p.z + 1.2) * 0.48)) * pulse;
      const r = p.size * p.scale;
      if (p.z > 0.25) {
        ctx.fillStyle =
          p.color === "#9875FF"
            ? `rgba(152, 117, 255, ${(alpha * 0.22).toFixed(2)})`
            : `rgba(102, 143, 255, ${(alpha * 0.22).toFixed(2)})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, r * 3.1, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = alpha;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  };

  const resize = () => {
    const rect = canvas.parentElement?.getBoundingClientRect();
    width = rect?.width || 600;
    height = rect?.height || 460;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (reduced) draw(0); // 静态帧随尺寸变化重绘
  };

  const loop = (time: number) => {
    draw(time);
    if (running) raf = requestAnimationFrame(loop);
  };

  const start = () => {
    if (running || reduced) return;
    running = true;
    raf = requestAnimationFrame(loop);
  };

  const stop = () => {
    running = false;
    cancelAnimationFrame(raf);
  };

  const onMouse = (e: MouseEvent) => {
    targetX = (e.clientX / window.innerWidth - 0.5) * 0.35;
    targetY = (e.clientY / window.innerHeight - 0.5) * 0.25;
  };

  const onVisibility = () => (document.hidden ? stop() : start());

  resize();
  window.addEventListener("resize", resize);
  if (!reduced) {
    window.addEventListener("mousemove", onMouse);
    document.addEventListener("visibilitychange", onVisibility);
    start();
  }

  return () => {
    stop();
    window.removeEventListener("resize", resize);
    window.removeEventListener("mousemove", onMouse);
    document.removeEventListener("visibilitychange", onVisibility);
  };
}
