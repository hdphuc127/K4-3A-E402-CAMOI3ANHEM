import type { ChatSource } from "@/lib/chat";

type Props = {
  citations: readonly ChatSource[];
  onOpenSource?: ((source: ChatSource) => void) | undefined;
};

function hasValue(value: string | number | null | undefined): value is string | number {
  return typeof value === "number"
    ? Number.isFinite(value)
    : typeof value === "string" && value.trim().length > 0;
}

export function SourceCitation({ citations, onOpenSource }: Props) {
  const visible = citations.filter((source) =>
    [
      source.source_id,
      source.id,
      source.title,
      source.excerpt,
      source.slide,
      source.page,
      source.timestamp,
      source.confidence,
      source.content,
      source.url,
    ].some(hasValue),
  );

  if (!visible.length) return null;

  return (
    <section
      aria-label="Nguồn tham khảo"
      className="mt-4 border-t border-border pt-3 whitespace-normal"
    >
      <h3 className="mb-2 text-sm font-medium text-muted-foreground">Nguồn tham khảo</h3>
      <ul className="space-y-2">
        {visible.map((source, index) => {
          const sourceId = hasValue(source.source_id) ? source.source_id : source.id;
          const label =
            [
              hasValue(source.title) ? source.title : sourceId,
              hasValue(source.slide) ? `Slide ${source.slide}` : undefined,
              hasValue(source.page) ? `Trang ${source.page}` : undefined,
              hasValue(source.timestamp) ? source.timestamp : undefined,
            ]
              .filter(hasValue)
              .join(" • ") || "Xem nguồn";

          return (
            <li
              key={`${sourceId ?? "source"}-${index}`}
              className="space-y-2 rounded-xl border border-border bg-card p-3 text-xs leading-relaxed"
            >
              {source.is_demo && <p className="text-muted-foreground">Dữ liệu demo</p>}
              {hasValue(source.title) && (
                <p className="break-words font-medium text-foreground">{source.title}</p>
              )}
              {hasValue(sourceId) && (
                <p className="break-words text-muted-foreground">Mã nguồn: {sourceId}</p>
              )}
              {(hasValue(source.slide) || hasValue(source.page) || hasValue(source.timestamp)) && (
                <div className="flex flex-wrap gap-x-3 gap-y-1 text-muted-foreground">
                  {hasValue(source.slide) && <span>Slide: {source.slide}</span>}
                  {hasValue(source.page) && <span>Trang: {source.page}</span>}
                  {hasValue(source.timestamp) && (
                    <span className="break-words">Thời gian transcript: {source.timestamp}</span>
                  )}
                </div>
              )}
              {hasValue(source.excerpt) && (
                <blockquote className="whitespace-pre-line break-words border-l-2 border-primary/30 pl-3 text-foreground">
                  {source.excerpt}
                </blockquote>
              )}
              {hasValue(source.confidence) && (
                <p className="break-words text-muted-foreground">Độ tin cậy: {source.confidence}</p>
              )}
              {onOpenSource && (
                <button
                  type="button"
                  onClick={() => onOpenSource(source)}
                  className="rounded-lg border border-primary/20 bg-accent/50 px-3 py-2 text-left text-xs font-medium text-primary"
                >
                  {label}
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
