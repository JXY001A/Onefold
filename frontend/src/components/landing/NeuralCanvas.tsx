import { useEffect, useRef } from "react";
import { startNeuralUniverse } from "./neuralEngine";

/** Hero 右侧三维神经网络宇宙画布；动画参数见 neuralEngine.ts。 */
export default function NeuralCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    return startNeuralUniverse(canvas);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="block h-full w-full"
      role="img"
      aria-label="Onefold 三维神经网络宇宙核心"
    />
  );
}
