import { AlertTriangleIcon, InfoIcon } from "./icons";

export function Callout({
  variant,
  title,
  content,
}: {
  variant: "warning" | "info" | "definition";
  title: string;
  content: string;
}) {
  const styles = {
    warning: {
      border: "border-rw-yellow-border",
      bg: "bg-rw-yellow-soft",
      icon: <AlertTriangleIcon width={16} height={16} className="mt-0.5 shrink-0 text-rw-yellow" />,
      titleColor: "text-amber-700",
    },
    info: {
      border: "border-rw-blue",
      bg: "bg-rw-blue-soft",
      icon: <InfoIcon width={16} height={16} className="mt-0.5 shrink-0 text-rw-blue" />,
      titleColor: "text-blue-700",
    },
    definition: {
      border: "border-rw-green-border",
      bg: "bg-rw-green-soft",
      icon: <InfoIcon width={16} height={16} className="mt-0.5 shrink-0 text-green-600" />,
      titleColor: "text-green-700",
    },
  };

  const s = styles[variant];

  return (
    <div className={`rounded-lg border ${s.border} ${s.bg} p-5`}>
      <div className="flex items-start gap-2.5">
        {s.icon}
        <div>
          <p className={`font-semibold ${s.titleColor}`}>{title}</p>
          <p className="mt-1.5 text-sm leading-relaxed text-rw-ink-secondary">{content}</p>
        </div>
      </div>
    </div>
  );
}
