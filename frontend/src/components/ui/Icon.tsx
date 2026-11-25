import clsx from "clsx";

type Props = {
  /** Material Symbols 图标名，如 search / folder_open */
  name: string;
  className?: string;
  /** 字号（px），默认 18，与设计稿图标尺寸一致 */
  size?: number;
  filled?: boolean;
};

/** 设计稿统一图标：Material Symbols Outlined。 */
export default function Icon({ name, className, size = 18, filled = false }: Props) {
  return (
    <span
      aria-hidden="true"
      className={clsx("material-symbols-outlined select-none", className)}
      style={{
        fontSize: size,
        fontVariationSettings: filled ? '"FILL" 1' : '"FILL" 0',
      }}
    >
      {name}
    </span>
  );
}