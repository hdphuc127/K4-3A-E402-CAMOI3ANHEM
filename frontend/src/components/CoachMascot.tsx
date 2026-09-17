import { useState } from "react";

export function CoachMascot({
  className = "",
  large = false,
}: {
  className?: string;
  large?: boolean;
}) {
  const [unavailable, setUnavailable] = useState(false);

  return (
    <div className={`coach-mascot ${className}`}>
      {unavailable ? (
        <div className="flex h-full w-full flex-col items-center justify-center rounded-[inherit] bg-secondary text-primary">
          <span className={large ? "text-6xl font-bold" : "text-sm font-bold"}>C4U</span>
          {large && <span className="mt-3 text-sm">Your AI Learning Coach</span>}
        </div>
      ) : (
        <img
          src="/coach4u-fox.jpg"
          alt={large ? "Mascot cáo Coach4U cầm kính lúp" : ""}
          className="h-full w-full object-contain"
          onError={() => setUnavailable(true)}
        />
      )}
    </div>
  );
}
