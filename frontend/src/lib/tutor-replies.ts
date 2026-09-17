import { TOPICS, type TopicId } from "./review-data";

export type ChatContext = {
  label: string;
  topic?: TopicId | undefined;
};

export const QUICK_ACTIONS = [
  "Giải thích dễ hiểu hơn",
  "Cho tôi ví dụ khác",
] as const;

const EMBEDDING: Record<string, string> = {
  "Tại sao tôi sai câu này?":
    "Cả 2 câu Embedding bạn chọn đều dựa trên Token ID để suy ra ý nghĩa. Token ID chỉ là số thứ tự tra cứu trong từ điển — nó không mang ngữ nghĩa. Thông tin ngữ nghĩa nằm ở embedding vector.",
  "Giải thích dễ hiểu hơn":
    "Token ID giống số báo danh của học sinh: số 105 và 106 ngồi cạnh nhau nhưng chẳng nói gì về tính cách. Embedding giống bản mô tả đặc điểm của học sinh đó — hai bản mô tả giống nhau mới nghĩa là hai bạn giống nhau.",
  "Cho tôi ví dụ khác":
    "Ví dụ: “ngân hàng” (nơi gửi tiền) và “ngân hàng” (bờ sông) có thể cùng Token ID, nhưng trong ngữ cảnh khác nhau mô hình tạo ra biểu diễn khác nhau. Ngược lại “mèo” và “chó” có ID cách xa hàng nghìn đơn vị nhưng embedding lại rất gần.",
  "So sánh 2 khái niệm":
    "Token ID: số nguyên, do từ điển quy định, không học được, không so sánh được về nghĩa.\nEmbedding Vector: dãy số thực nhiều chiều, học được khi huấn luyện, so sánh được bằng cosine similarity.",
  "Tóm tắt phần này":
    "1) Tokenizer cắt văn bản → token. 2) Mỗi token có Token ID để tra cứu. 3) Token ID được đổi thành embedding vector. 4) Chỉ embedding mới đo được độ gần nghĩa.",
  "Tôi vẫn chưa hiểu":
    "Không sao. Thử theo hướng này: bạn hãy tưởng tượng từ điển là một danh sách được sắp xếp ngẫu nhiên. Vị trí trong danh sách (ID) là tuỳ ý. Còn embedding là toạ độ trên một tấm bản đồ ý nghĩa — từ nào gần nhau trên bản đồ thì gần nghĩa. Bạn muốn mình ra một câu kiểm tra nhỏ để xem chỗ nào còn vướng không?",
  "Tôi nên ôn phần nào trước?":
    "Ưu tiên Embedding: bạn sai 2 câu và cả 2 đều cùng một hiểu nhầm. Attention chỉ sai 1 câu nên để sau.",
};

const ATTENTION: Record<string, string> = {
  "Tại sao tôi sai câu này?":
    "Bạn đang xem attention như một bước xử lý văn bản (nén, cắt, dịch). Thực ra attention là bước tính trọng số liên quan giữa các token để quyết định thông tin nào ảnh hưởng tới đầu ra.",
  "Giải thích dễ hiểu hơn":
    "Attention giống việc bạn đọc một câu và tự hỏi “từ này đang nói về cái gì phía trước?”. Mô hình cho điểm cho từng từ phía trước, từ nào điểm cao thì được chú ý nhiều hơn.",
  "Cho tôi ví dụ khác":
    "“Nam để chìa khoá trong túi vì nó an toàn.” — attention phải gán trọng số cao giữa “nó” và “túi”, không phải “chìa khoá”, để hiểu đúng ý câu.",
  "So sánh 2 khái niệm":
    "Embedding trả lời “token này nghĩa là gì”. Attention trả lời “trong câu này, token nào liên quan tới token nào”. Một cái là ý nghĩa tĩnh, một cái là quan hệ theo ngữ cảnh.",
  "Tóm tắt phần này":
    "Attention = tính điểm liên quan giữa các token → chuẩn hoá thành trọng số → trộn thông tin theo trọng số đó.",
  "Tôi vẫn chưa hiểu":
    "Mình chưa đủ dữ kiện để kết luận bạn đang vướng ở đâu (mới có 1 câu sai). Hãy làm thêm một câu kiểm tra để mình xác định chính xác hơn nhé.",
  "Tôi nên ôn phần nào trước?":
    "Nếu Embedding đã được xác nhận hiểu, giờ là lúc ôn Attention.",
};

const GENERIC: Record<string, string> = {
  "Tôi nên ôn phần nào trước?":
    "Dựa trên bài kiểm tra, hãy bắt đầu với phần có nhiều câu sai nhất và các câu sai cùng một nguyên nhân.",
  "Tóm tắt phần này": "Phần này tập trung vào cách mô hình biểu diễn và xử lý token trong ngữ cảnh.",
};

export function tutorReply(input: string, ctx: ChatContext): string {
  const table = ctx.topic === "attention" ? ATTENTION : ctx.topic === "embedding" ? EMBEDDING : GENERIC;
  const hit = table[input.trim()];
  if (hit) return hit;

  const lower = input.toLowerCase();
  const keyed = Object.keys(table).find((k) =>
    lower.includes(k.toLowerCase().slice(0, 12)),
  );
  if (keyed) return table[keyed]!;

  if (lower.includes("ví dụ")) return table["Cho tôi ví dụ khác"] ?? GENERIC["Tóm tắt phần này"]!;
  if (lower.includes("so sánh")) return table["So sánh 2 khái niệm"] ?? GENERIC["Tóm tắt phần này"]!;
  if (lower.includes("sai")) return table["Tại sao tôi sai câu này?"] ?? GENERIC["Tôi nên ôn phần nào trước?"]!;

  const topicName = ctx.topic ? TOPICS[ctx.topic].name : "phần đang xem";
  return `Mình đang theo dõi bối cảnh: ${ctx.label}. Với ${topicName}, mình chưa đủ thông tin để kết luận bạn đang hiểu nhầm chỗ nào. Bạn thử bấm “Kiểm tra lại tôi” để mình ra một câu hỏi và xác định chính xác hơn nhé.`;
}
