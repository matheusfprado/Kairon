import clsx from "clsx";

interface StatusDotProps {
  active: boolean;
  label: string;
}

export function StatusDot({ active, label }: StatusDotProps) {
  return (
    <span
      className="inline-flex items-center gap-2 text-xs text-kairon-muted"
      aria-label={`${label}: ${active ? "ativo" : "inativo"}`}
    >
      <span
        className={clsx(
          "h-2.5 w-2.5 rounded-full border",
          active ? "border-kairon-cyan bg-kairon-cyan shadow-[0_0_16px_rgba(109,231,228,0.7)]" : "border-kairon-line bg-transparent",
        )}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}
