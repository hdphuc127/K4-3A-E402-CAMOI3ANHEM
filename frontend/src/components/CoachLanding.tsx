import { CoachMascot } from "./CoachMascot";

const benefits = [
  {
    icon: "⌕",
    title: "Tìm đúng nội dung",
    text: "Hỏi tự do về kiến thức VLearn và xem nguồn ngay trong câu trả lời.",
  },
  {
    icon: "◎",
    title: "Ôn tập theo điểm yếu",
    text: "Nhìn rõ phần còn nhầm lẫn, rồi cùng AI Tutor ôn lại từng khái niệm.",
  },
  {
    icon: "↗",
    title: "Kiểm tra & tiến bộ",
    text: "Củng cố hiểu biết với adaptive quiz và giải thích cho từng câu sai.",
  },
];

export function CoachLanding({ onStart }: { onStart: () => void }) {
  return (
    <div className="review-app coach-landing min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-5 sm:px-8">
        <div className="flex items-center gap-2.5">
          <CoachMascot className="h-11 w-11 rounded-xl" />
          <span className="text-2xl font-bold tracking-tight text-foreground">
            Coach<span className="text-primary">4U</span>
          </span>
        </div>
        <button
          type="button"
          onClick={onStart}
          className="rounded-full border border-primary/20 bg-card px-5 py-2.5 text-sm font-semibold text-primary"
        >
          Bắt đầu ôn tập <span aria-hidden="true">↗</span>
        </button>
      </header>
      <main className="mx-auto max-w-6xl px-5 pb-12 sm:px-8">
        <section className="grid items-center gap-8 py-10 md:grid-cols-[1.2fr_1fr] md:py-16">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-card/80 px-4 py-2 text-xs font-semibold text-primary">
              <span aria-hidden="true">✦</span> Học cùng AI · Hiểu sâu hơn mỗi ngày
            </span>
            <h1 className="mt-6 text-4xl font-bold leading-tight sm:text-5xl lg:text-6xl">
              Coach4U <span className="mt-2 block coach-gradient-text">Your AI Learning Coach</span>
            </h1>
            <p className="mt-6 text-xl font-medium text-foreground sm:text-2xl">
              Learn smarter. Review what you missed.
            </p>
            <p className="mt-4 max-w-lg text-base leading-7 text-muted-foreground">
              Tìm kiến thức VLearn, ôn lại điểm yếu cùng AI Tutor và củng cố hiểu biết qua adaptive
              quiz. Một người bạn đồng hành cho mỗi phiên học.
            </p>
            <button
              type="button"
              onClick={onStart}
              className="mt-8 rounded-full bg-primary px-7 py-3.5 text-base font-semibold text-primary-foreground shadow-lg shadow-primary/20"
            >
              Bắt đầu ôn tập{" "}
              <span className="ml-3" aria-hidden="true">
                →
              </span>
            </button>
          </div>
          <div className="coach-hero-art relative mx-auto w-full max-w-lg rounded-[3rem] p-2 sm:p-3">
            <CoachMascot large className="aspect-square w-full rounded-[2rem]" />
          </div>
        </section>
        <section aria-label="Lợi ích Coach4U" className="grid gap-4 md:grid-cols-3">
          {benefits.map((benefit) => (
            <article
              key={benefit.title}
              className="rounded-3xl border border-border bg-card/90 p-6 shadow-sm"
            >
              <span
                aria-hidden="true"
                className="mb-4 grid h-11 w-11 place-items-center rounded-2xl bg-secondary text-2xl text-primary"
              >
                {benefit.icon}
              </span>
              <h2 className="text-lg font-semibold">{benefit.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{benefit.text}</p>
            </article>
          ))}
        </section>
        <section className="mt-14 rounded-[2rem] border border-border bg-card/70 p-6 sm:p-9">
          <h2 className="text-center text-2xl font-bold sm:text-3xl">
            Chỉ 3 bước để ôn tập hiệu quả
          </h2>
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            {[
              {
                number: "01",
                title: "Kiểm tra nhanh",
                text: "Nhận diện những phần kiến thức cần ôn.",
              },
              {
                number: "02",
                title: "Ôn cùng AI",
                text: "Đặt câu hỏi và khám phá nội dung từ nguồn trích dẫn.",
              },
              {
                number: "03",
                title: "Kiểm tra lại",
                text: "Luyện tập và hiểu vì sao mình trả lời sai.",
              },
            ].map((item) => (
              <div key={item.number} className="flex items-start gap-4">
                <span className="text-3xl font-bold text-primary/35">{item.number}</span>
                <div>
                  <h3 className="text-base font-semibold">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.text}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
      <footer className="border-t border-border py-5 text-center text-xs text-muted-foreground">
        Coach4U · Your AI Learning Coach
      </footer>
    </div>
  );
}
