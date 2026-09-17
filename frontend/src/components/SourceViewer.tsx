import type { ChatSource } from "@/lib/chat";

type Props = {
  source: ChatSource;
  onClose: () => void;
};

function hasValue(value: string | number | null | undefined): boolean {
  return typeof value === "number"
    ? Number.isFinite(value)
    : typeof value === "string" && value.trim().length > 0;
}

export function SourceViewer({ source, onClose }: Props) {
  const sourceId = source.source_id?.trim() || source.id?.trim();
  const content = source.content?.trim();
  const excerpt = source.excerpt?.trim();
  // Show a document link only for a supplied web URL; do not infer URLs from IDs.
  const url = source.url && /^https?:\/\//i.test(source.url) ? source.url : undefined;

  return (
    <section aria-label="Nguồn đang xem" className="h-full min-w-0 bg-surface p-4 sm:p-7">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          {source.is_demo && <p className="mb-1 text-xs text-muted-foreground">Dữ liệu demo</p>}
          <h2 className="break-words text-lg font-semibold">
            {source.title?.trim() || "Nguồn tham khảo"}
          </h2>
          {sourceId && (
            <p className="mt-1 break-words text-xs text-muted-foreground">Mã nguồn: {sourceId}</p>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-border bg-card px-3 py-2 text-sm"
        >
          Đóng nguồn
        </button>
      </div>
      <div className="space-y-5 rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
        {(hasValue(source.slide) || hasValue(source.page) || hasValue(source.timestamp)) && (
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
            {hasValue(source.slide) && <span>Slide: {source.slide}</span>}
            {hasValue(source.page) && <span>Trang: {source.page}</span>}
            {hasValue(source.timestamp) && <span>Thời gian transcript: {source.timestamp}</span>}
          </div>
        )}
        {content && (
          <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{content}</p>
        )}
        {excerpt && (
          <div>
            <h3 className="mb-2 text-xs font-medium text-muted-foreground">
              Trích dẫn được cung cấp
            </h3>
            <blockquote className="whitespace-pre-wrap break-words border-l-2 border-primary/30 pl-4 text-sm leading-relaxed">
              {source.excerpt}
            </blockquote>
          </div>
        )}
        {!content && (
          <p className="text-sm text-muted-foreground">
            Citation chưa cung cấp nội dung nguồn đầy đủ.
          </p>
        )}
        {url && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-sm text-primary underline"
          >
            Mở tài liệu nguồn
          </a>
        )}
      </div>
    </section>
  );
}
