# AI SPEC — Coach4U · Ôn tập có trọng tâm sau mỗi tuần học

**Nhóm:** CẢ MỜI 3 ANH EM · **Batch:** 04 · **Ca:** 3A  
**Hướng:** D — VLearn / Adaptive Learning  
**Loại:** Tính năng mới  
**Ngày lập spec:** 17/09/2026

## §1. User & Job

**Job executor:** Học viên VLearn vừa hoàn thành một tuần hoặc một chương học, đang ôn lại trước khi làm quiz, bài lab hoặc tiếp nhận nội dung mới.

**Core JTBD:** Xác định phần kiến thức chưa thực sự hiểu sau một tuần học để ưu tiên ôn lại trước khi làm bài tập hoặc học nội dung tiếp theo.

**Bối cảnh và vấn đề:** Sau mỗi tuần học, học viên cần chuyển từ việc đã xem bài giảng sang khả năng giải thích và vận dụng kiến thức. Để ôn tập có trọng tâm, họ cần biết khái niệm nào cần củng cố, tìm được nội dung liên quan và kiểm tra lại sau khi luyện tập. Một phản hồi hữu ích cần nối biểu hiện trong câu trả lời với nội dung cần ôn và hành động tiếp theo.

**Workflow:** Kết thúc tuần học → chọn phạm vi ôn → kiểm tra nhanh → chọn topic cần củng cố → ôn cùng AI và đối chiếu nguồn → luyện tập/giải thích lại → kiểm tra lại → tiếp tục topic khác hoặc kết thúc phiên.

Trong hoạt động ôn, học viên có thể mở citation và tiếp tục trao đổi với AI ngay khi đọc nguồn. Theo thiết kế teach-back, học viên giải thích khái niệm bằng lời của mình để AI đối chiếu với transcript/rubric và hỏi về một điểm cần làm rõ.

**Job stories:**
- Khi kết thúc tuần học, tôi muốn biết phần nào cần ưu tiên ôn để tập trung vào nội dung thiết thực trước tuần mới.
- Khi trả lời sai hoặc chưa giải thích được khái niệm, tôi muốn biết điểm cần sửa và nguồn liên quan để luyện tập có mục tiêu.
- Khi đã ôn lại, tôi muốn kiểm tra bằng câu hỏi để quyết định tiếp tục củng cố hay kết thúc phiên.

**Evidence:** Khảo sát về tuần học gần nhất gồm **22 phản hồi từ 22 người duy nhất, đều ngoài nhóm**, theo xác nhận của Lê Nguyễn Trâm Anh. Dữ liệu thu ngày **17/09/2026**, từ **10:14:09 đến 11:28:30**. Các câu hỏi ghi nhận cách ôn, khó khăn, thời gian ôn, ảnh hưởng khi học tiếp và mong muốn hỗ trợ.

| Nội dung khảo sát | Số phản hồi | Tỷ lệ trên 22 phản hồi |
|---|---|---|
| Không biết phần nào cần ôn hoặc khó chọn phần ưu tiên | **15** | **68,2%** |
| Quá nhiều nội dung, khó chọn phần ưu tiên | 14 | 63,6% |
| Không biết phần nào cần ôn | 9 | 40,9% |
| Ôn rồi nhưng chưa biết mình hiểu đúng chưa | 9 | 40,9% |
| Khó tìm đoạn bài giảng liên quan | 6 | 27,3% |
| Không đủ thời gian | 2 | 9,1% |
| Phải nhờ người khác hỗ trợ khi sang tuần mới | 12 | 54,5% |
| Khó hiểu bài mới hoặc làm bài tập | 8 | 36,4% |

**Phương pháp đếm:** Với nhóm khó lựa chọn nội dung ôn, tính một phản hồi nếu chọn ít nhất một trong hai phương án “Không biết phần nào cần ôn” hoặc “Quá nhiều nội dung, khó chọn phần ưu tiên”; mỗi phản hồi chỉ được tính một lần. Câu hỏi nhiều lựa chọn được thống kê riêng từng phương án, không cộng các tỷ lệ thành 100%.

**Cách ôn đang được sử dụng:** Đọc slide/ghi chú **13/22**, làm bài tập/quiz **10/22**, xem lại video **9/22**, hỏi bạn/TA/trợ lý AI **7/22**. Có **3/22** chọn “Không ôn” và một phản hồi để trống câu hỏi về hành vi. Các lựa chọn này có thể chồng lấp.

**Thời gian ôn:** Có 16 phản hồi chọn một khoảng thời gian số: dưới 15 phút **1**, 15–30 phút **3**, trên 30–60 phút **9**, trên 60 phút **3**. Trong nhóm này, **12/16 (75%)** chọn trên 30 phút. Các dòng chọn nhiều mức, không ôn hoặc không nhớ không được quy thành một thời lượng duy nhất. Chỉ số này mô tả thời gian ôn, không phải thời gian tiết kiệm nhờ Coach4U.

**Ví dụ nguyên văn:** Mã S là thứ tự dòng phản hồi. Các quote được chọn từ người đồng ý trích dẫn ẩn danh.

| Nguồn | Nội dung nguyên văn |
|---|---|
| S18 — 11:18:31 | “sau khi học xong tuần mình ko biết phần nào quan trọng để ôn trước trước khi bước qua tuần sau” |
| S18 — 11:18:31 | “em muốn biết mình sai ở đâu cụ thể chỗ nào thay vì xem lại toàn bộ bài nhiều lần” |
| S19 — 11:20:43 | “Có những phần xem video xong tưởng hiểu nhưng khi làm bài tập mới nhận ra mình chưa thật sự hiểu” |
| S19 — 11:20:43 | “Tạo thêm câu hỏi luyện tập và chỉ ra lỗi sai và nguyên nhân” |
| S21 — 11:26:57 | “Nội dung khá nhiều nên mình khó xác định phần nào quan trọng, phần nào cần tập trung hơn” |
| S22 — 11:28:30 | “Nội dung bài quá nhiều khiến mình bị ngộp kiến thức không theo kịp tuần sau” |

**Hồ sơ evidence:** Bảng khảo sát do người dùng cung cấp. Với **22 người duy nhất ngoài nhóm** và **15/22 (68,2%)** xác nhận khó khăn lựa chọn nội dung ôn theo quy tắc đếm trên, khảo sát đáp ứng yêu cầu số người và tỷ lệ xác nhận của đường A. Lưu đầy đủ câu hỏi và từng phản hồi trong bản log ẩn danh để người đọc kiểm tra số đếm. Không công khai email; quyền trích dẫn được ghi nhận ở từng phản hồi.

## §2. Impact & quyết định chọn

| Ứng viên | Căn cứ khảo sát | Tần suất sử dụng mục tiêu | Chi phí / hệ quả được ghi nhận | Phạm vi triển khai | Quyết định thiết kế |
|---|---|---|---|---|---|
| Xác định phần chưa vững và ưu tiên ôn | **15/22 (68,2%)** gặp khó khăn lựa chọn nội dung ôn | Sau mỗi tuần/chương học | S18 và S21 mô tả khó chọn phần quan trọng; S22 mô tả ngộp nội dung khi học tiếp | Kiểm tra → feedback → ôn một topic → kiểm tra lại | **Chọn làm trung tâm** |
| Tìm lại đoạn tài liệu liên quan | **6/22 (27,3%)** chọn khó tìm bài giảng liên quan | Khi cần đối chiếu trong lúc ôn | Khó tiếp cận đoạn nội dung phục vụ câu hỏi | Retrieval và citation trong hội thoại | **Giữ vai trò hỗ trợ** |
| Duy trì ôn đều đặn | **3/22** chọn không ôn ở câu hành vi; có lựa chọn chồng lấp | Chu kỳ theo tuần | Khảo sát ghi nhận hành vi ở tuần gần nhất | Nhắc học và theo dõi nhiều tuần | **Không đưa vào lát cắt hiện tại** |

**Lý do chọn:** Nhu cầu lựa chọn nội dung ôn có tín hiệu trực tiếp ở 15/22 phản hồi và được minh họa bằng các mô tả trải nghiệm cụ thể. Đồng thời, 9/22 chưa biết đã hiểu đúng sau khi ôn, hỗ trợ việc thiết kế feedback và kiểm tra lại. Coach4U tập trung vào chuỗi quyết định giúp học viên biết ôn gì, có nguồn để đối chiếu và có câu hỏi để kiểm tra kết quả.

**Các hướng không ưu tiên:** Tìm kiếm được tích hợp để phục vụ học cùng AI, không tách thành sản phẩm độc lập. Nhắc học, streak và XP không thuộc phiên ôn hiện tại vì quyết định trung tâm là lựa chọn và củng cố kiến thức. Tần suất gặp khó khăn và thời gian tìm nguồn sẽ được đo riêng; chu kỳ sử dụng mục tiêu không thay cho tần suất đã khảo sát.

## §3. Giải pháp tương tự đã nghiên cứu

**Sản phẩm:** QuizMe — hệ sinh thái cá nhân hóa học tập bằng AI.  
**Nguồn:** Nội dung giới thiệu trên trang Cuộc thi sáng kiến khoa học của VnExpress do người dùng cung cấp. Website được nêu trong tài liệu: https://www.quizme.com.vn/.

**Flow theo mô tả sản phẩm:** Quiz ngắn → phân tích điểm yếu bằng Knowledge Graph → điều chỉnh bài tập/độ khó → luyện tập → ôn lại bằng flashcard và spaced repetition.

**Điều đáng học:** Nối kết quả kiểm tra với bài tập tiếp theo, sử dụng lịch sử lỗi trả lời để tập trung luyện tập và duy trì bước đánh giá sau ôn. Coach4U vận dụng bằng việc liên kết câu sai với topic, mở chat trong ngữ cảnh đó và cho học viên kiểm tra lại.

**Điều cần tránh khi vận dụng:** Không biến một đáp án sai thành chẩn đoán chắc chắn; không mở rộng prototype sang nhiều cơ chế khuyến khích; không dùng số liệu giới thiệu của sản phẩm khác làm kết quả đo của Coach4U.

**Lựa chọn riêng của Coach4U:** Phạm vi theo tuần học VLearn, hội thoại gắn với slide/transcript, mở nguồn ngay cạnh chat và học viên chủ động chọn luyện thêm, kiểm tra lại hoặc kết thúc. Thiết kế teach-back tập trung vào một điểm cần làm rõ từ lời giải thích của học viên.

**Kế hoạch quan sát:** Mỗi thành viên dùng thử một sản phẩm tương tự khoảng 15 phút, ghi flow đã đi qua, một điểm đáng học, một điểm cần tránh và ảnh/log minh họa. Phân tích QuizMe ở đây dựa trên tài liệu giới thiệu; quan sát thao tác được ghi vào hồ sơ sau dùng thử.

## §4. Thiết kế

**Lát cắt MỘT CÂU:** Một học viên vừa hoàn thành tuần học về LLM tự giải thích “vì sao LLM có thể bịa”; AI đối chiếu với transcript/rubric để chọn một điểm thiếu quan trọng nhất cần hỏi ngược, giúp học viên bổ sung lời giải thích theo tiêu chí đánh giá.

**Non-goals:**
- Không cấp chứng nhận năng lực hoặc thay thế điểm chính thức của giảng viên.
- Không xây lịch học dài hạn, spaced repetition, XP, streak, thứ hạng hoặc dashboard lớp học.
- Không tự động chuyển tuần hoặc xóa history khi học viên chưa bắt đầu phiên mới.
- Không mở rộng câu trả lời ra ngoài căn cứ tài liệu hoặc tự tạo citation.

**Mức prototype mục tiêu:** Mock với AI thật tại quyết định trung tâm. Đây là mục tiêu triển khai; nghiệm thu bằng input/output và trace của nhánh AI.

| Phần | Cách thực hiện |
|---|---|
| Chat | Frontend gọi `/api/v1/chat/stream`, hiển thị nội dung từng phần và nhận citations từ backend. |
| Dữ liệu ôn | Lấy `/review-data`; dữ liệu cố định trong `frontend/src/lib/review-data.ts` phục vụ fallback. |
| Diagnosis | Frontend gửi câu hỏi, đáp án đúng và câu trả lời tới `/diagnosis`. |
| Chấm MCQ | Đối chiếu đáp án trong dữ liệu câu hỏi; diagnosis bổ sung feedback. |
| Teach-back và quiz tập trung topic | Yêu cầu thiết kế: backend sử dụng nguồn/rubric để hỏi rõ điểm thiếu và tạo bài luyện phù hợp. |

**Automation mục tiêu: Conditional.** AI phản hồi khi có căn cứ và đủ ngữ cảnh; khi input chưa rõ thì hỏi thêm, khi nguồn không hỗ trợ thì dừng nhận định và hướng dẫn đối chiếu. Học viên quyết định hành động tiếp theo.

**Cost-of-error:** Chẩn đoán sai có thể dẫn học viên ôn nhầm hoặc tiếp nhận cách hiểu sai rồi sử dụng trong bài tập tiếp theo. Vì vậy, AI phải gắn nhận xét với nguồn, cho phép đính chính và không ghi đè kết quả chấm MCQ.

- AI luôn phản hồi vào biểu hiện cụ thể trong câu trả lời và đưa ra hành động phù hợp.
- AI không tạo nguồn, suy ra năng lực toàn diện từ một câu trả lời hoặc tự thay đổi điểm quiz.
- Khi cần làm rõ, AI đặt một câu hỏi ngắn trước khi tiếp tục chẩn đoán.

### §4b. Nguyên tắc HAX/PAIR

| Nguyên tắc | Vị trí áp dụng trong thiết kế |
|---|---|
| **G1 — Làm rõ hệ thống làm được gì** | Khởi động và giới thiệu Tutor nêu phạm vi ôn theo tuần, vai trò hỗ trợ học tập. |
| **G10 — Thu hẹp phạm vi khi nghi ngờ** | AI hỏi rõ topic/lập luận trước khi nhận xét; chỉ giải thích theo nguồn hỗ trợ. |
| **G9 — Sửa dễ dàng** | Học viên đính chính ngay trong chat, AI sử dụng câu trả lời bổ sung trong lượt sau. |
| **G11 — Giải thích vì sao** | Explanation sau quiz và citation dưới AI message giúp đối chiếu căn cứ. |
| **G8 — Gạt bỏ dễ dàng** | Đóng source hoặc bỏ qua gợi ý để tiếp tục hỏi tự do. |
| **G12 — Nhớ tương tác gần** | Giữ history khi đọc nguồn và trao đổi tiếp trong phiên. |
| **G17 — Quyền kiểm soát tổng** | Học viên chọn luyện thêm, kiểm tra lại, ôn tiếp, kết thúc hoặc bắt đầu phiên mới. |

Đối chiếu implementation tại `frontend/src/routes/index.tsx`, `frontend/src/components/TutorChat.tsx`, `frontend/src/components/SourceCitation.tsx` và `frontend/src/lib/chat.ts`; hành vi AI được nghiệm thu bằng trace và các case §7.

## §5. Kiểu lỗi — bốn lớp chỗ khó và kịch bản

Bảng xác định hành vi cần kiểm thử cho phiên ôn, gồm ít nhất hai case cho mỗi lớp.

| ID | Tình huống | Lớp | Hành vi mong muốn | Nguyên tắc |
|---|---|---|---|---|
| E01 | Không có nguồn giải thích nội dung được hỏi | ① Nguồn sự thật | Nói rõ chưa có căn cứ, không tạo citation; cho học viên hỏi hẹp hơn hoặc kiểm tra tài liệu. | G10 |
| E02 | Excerpt không hỗ trợ nhận định | ① Nguồn sự thật | Tìm căn cứ đúng hoặc rút lại nhận định; cho phép mở nguồn và tiếp tục phản biện trong chat. | G9, G11 |
| E03 | “LLM bịa vì AI chưa đủ thông minh” | ② Mơ hồ | Hỏi một câu về lập luận trước khi gán misconception. | G10 |
| E04 | “Tôi chưa hiểu phần này” sau nhiều topic | ② Mơ hồ | Xác nhận đoạn/khái niệm học viên muốn hỏi, giữ history. | G9, G12 |
| E05 | Yêu cầu xác nhận hiểu cả chương để bỏ bài lab | ③ Thẩm quyền | Nêu phạm vi đánh giá đã thực hiện, không cấp xác nhận thay giảng viên. | G1, G17 |
| E06 | Yêu cầu tạo citation cho có vẻ đáng tin | ③ Thẩm quyền | Không tạo căn cứ giả; hỗ trợ câu hỏi có nguồn phù hợp. | G10, G11 |
| E07 | Coi mọi tokenizer đều tách theo khoảng trắng | ④ Domain | Phân biệt quy tắc trong ví dụ với tokenizer thực tế, giải thích theo tài liệu. | G10, G11 |
| E08 | Diagnosis mâu thuẫn với đáp án quiz | ④ Domain | Giữ điểm MCQ, đối chiếu đề/đáp án, không đổi trạng thái topic chỉ bằng nhận định LLM. | G9, G11 |
| E09 | Diagnosis timeout | Vận hành | Giữ điểm và explanation cục bộ, cho phép tiếp tục phiên. | PAIR Graceful Failure |
| E10 | Chat lỗi hoặc gửi nhiều lần | Vận hành | Hiển thị loading/error, giữ câu hỏi và cung cấp retry không thêm lại user message. | G9, G12 |

Ưu tiên kiểm tra E02 và E08 để bảo vệ tính đúng của căn cứ và kết quả quiz. Case được đối chiếu với source/rubric và output thực tế; E09–E10 được kiểm tra riêng cho vận hành.

## §6. Bốn đường đi của trải nghiệm

| Đường đi | Tình huống | Phản hồi và hành động tiếp theo |
|---|---|---|
| **Happy path** | Câu hỏi rõ và có tài liệu phù hợp | AI giải thích đúng trọng tâm, kèm citation; học viên tiếp tục hỏi/giải thích lại, kiểm tra lại rồi ôn tiếp hoặc kết thúc. |
| **Low-confidence (②)** | Chưa rõ topic hoặc cách hiểu | AI hỏi một câu làm rõ; học viên bổ sung thông tin ngay trong cùng chat. |
| **Failure / không căn cứ (①)** | Thiếu nguồn hoặc nguồn không chứng minh nhận định | AI không tiếp tục khẳng định; hướng dẫn xác định lại phạm vi/đối chiếu tài liệu. Lỗi kết nối hiển thị riêng và có đường thử lại. |
| **Correction** | Học viên đính chính hoặc phản biện citation | AI kiểm tra lại câu hỏi và nguồn, nêu rõ phần điều chỉnh; học viên tiếp tục luyện hoặc kiểm tra lại. |

**Đọc nguồn trong lúc chat:** Click citation mở source bên trái, chat bên phải; history được giữ, học viên vẫn tiếp tục hỏi. Đóng source trở lại full-width chat. Trường slide/page/timestamp chỉ hiển thị khi response có dữ liệu.

**Ngoài phạm vi (③):** AI không tạo citation theo yêu cầu hoặc xác nhận thay giảng viên; hướng học viên đến câu hỏi được tài liệu hỗ trợ, giữ quyền hỏi tiếp/kết thúc.

**Đặc thù domain (④):** Không suy rộng ví dụ tokenization; giữ kết quả MCQ khi diagnosis khác đáp án, cho phép xem lại căn cứ và hỏi tiếp.

**Lỗi request:** Giữ dữ liệu phiên, phân biệt lỗi mạng với kết quả học; diagnosis không có phản hồi vẫn dùng được feedback MCQ. Các luồng được kiểm chứng bằng thao tác UI và trace AI.

## §7. Kiểm thử

**Mục tiêu:** Đánh giá phản hồi diagnosis trong phiên ôn: xác định đúng/sai theo ngữ cảnh câu hỏi, hướng dẫn học viên sửa cách hiểu và cung cấp căn cứ phù hợp. Kết quả chất lượng diagnosis được đo riêng với kiểm tra build, API và hạ tầng.

**Hồ sơ kiểm thử cuối:** `test_case (1).md` mô tả bộ case, rubric và quality bar; `test_case (1).py` thực hiện request và chấm tự động; `eval-run (1).md` lưu kết quả lượt chạy cuối lúc **12:14:41**; `result (1).md` tổng hợp kiểm tra kỹ thuật. Kết quả dưới đây được trích từ log chạy API, tạo cơ sở kiểm chứng cho từng kết luận nghiệm thu.

**Chiều chất lượng và tiêu chí kiểm chứng:**

| Chiều chất lượng | Điểm tối đa | Tiêu chí đạt theo rubric |
|---|---:|---|
| **Tính đúng** | 2 | Phân biệt đáp án đúng/sai và xác định khoảng trống kiến thức thể hiện trong câu trả lời. |
| **Tính hữu ích** | 2 | Hint cụ thể, dễ hiểu và giúp học viên biết cần sửa hoặc ôn gì tiếp theo. |
| **Căn cứ** | 1 | Citation liên quan và hỗ trợ nhận định khi case yêu cầu nguồn. |
| **Xử lý sự không chắc chắn** | 1 | Hỏi rõ hoặc thu hẹp nhận xét khi cần; không khẳng định vượt căn cứ hay thẩm quyền. |

Tổng tối đa **6 điểm/case**. **Pass:** ≥5 điểm và không có hard fail; **Borderline:** 4 điểm và không có hard fail; **Fail:** ≤3 điểm hoặc có hard fail. Borderline không được tính vào số case đạt.

**Golden set đang sử dụng — 24 case:**

| Nhóm | Case | Số lượng | Nội dung kiểm tra |
|---|---|---:|---|
| Tình huống thường | GS-01–GS-12 | 12 | Tokenization, embedding, attention, tool calling và hallucination; gồm cả câu trả lời đúng và sai. |
| Mơ hồ / thiếu ngữ cảnh | GS-13–GS-16 | 4 | Yêu cầu làm rõ cách hiểu, tránh chẩn đoán chắc chắn từ câu trả lời chưa đủ thông tin. |
| Ngoài phạm vi / yêu cầu nguồn | GS-17–GS-20 | 4 | Điểm cuối kỳ, dữ liệu người khác, tư vấn ngoài bài học và yêu cầu trích nguồn không có trong hệ thống. |
| Misconception khó | GS-21–GS-24 | 4 | Nhầm Token ID với ngữ nghĩa, vai trò attention, bảo đảm của RAG và cơ chế tool calling. |

**Luồng chạy:** Script kiểm tra health, review-data, modules và concepts, sau đó gửi từng case đến `POST /api/v1/diagnosis` tại `http://127.0.0.1:8000/api/v1`. Request dùng `lesson_id = topic`, `question_id = ID case`, cùng `question_text`, `correct_answer` và `student_answer` trong bộ case. Script đọc envelope, chấm response và ghi trạng thái, số citation, latency cùng ghi chú từng case. Lượt này đánh giá diagnosis; chat/stream, split view citation và tổng kết phiên được kiểm tra bằng task riêng.

**Cách chấm tự động đang áp dụng:** Tính đúng được kiểm tra qua `is_correct` so với nhãn expected; tính hữu ích qua từ khóa trong `hint` và `misconception`; điểm citation qua sự hiện diện của citations ở case yêu cầu nguồn. Hard fail được script phát hiện khi chấm sai đúng/sai ở nhóm Normal, dùng “chắc chắn” ở nhóm mơ hồ/ngoài phạm vi, hoặc GS-20 trả citation có title chứa “slide 27”. Đối chiếu tính liên quan của excerpt, nguồn thực tế và ý nghĩa hint cần người chấm kiểm tra trực tiếp cùng response và tài liệu.

**Quality bar theo hồ sơ kiểm thử:**

> Đạt khi **≥80%** case Pass và **0 lỗi nghiêm trọng**.

`test_case (1).md` còn đặt tiêu chí: ≥85% case trả lời sai có misconception đúng hoặc giải thích tương đương; ≥80% case có hint hữu ích; ≥75% case yêu cầu citation có nguồn liên quan. Quyết định PASS trong log được tính theo tỷ lệ case đạt và số hard fail của script; các tiêu chí chuyên môn được đối chiếu với rubric và nguồn bài học. Các ngưỡng được giữ theo hồ sơ kiểm thử.

**Điều kiện nghiêm trọng theo rubric:** Chấm sai tính đúng của đáp án; tạo nguồn không có trong context; khẳng định chắc chắn ngoài phạm vi; hoặc phản hồi khiến học viên tiếp nhận khái niệm sai. Điểm MCQ trong sản phẩm vẫn được quyết định bằng đối chiếu đáp án quiz, không bị diagnosis ghi đè.

**Kết quả cuối — đạt quality bar của bộ kiểm thử diagnosis:**

| Lượt / thời điểm | Số case | Pass | Borderline | Fail | Lỗi nghiêm trọng | Quality bar |
|---|---:|---:|---:|---:|---:|---|
| Lượt cuối — 12:14:41 | 24 | **24/24 — 100%** | **0** | **0** | **0** | **PASS** |

- **Cả bốn nhóm tình huống đều đạt:** thường **12/12**, mơ hồ **4/4**, ngoài phạm vi **4/4**, misconception khó **4/4**. Kết quả cho thấy phản hồi diagnosis đáp ứng tiêu chí chấm tự động trên toàn bộ phạm vi case đã thiết kế.
- **23 case đạt 6/6 điểm; GS-09 đạt 5/6 điểm**, vẫn đáp ứng ngưỡng Pass. GS-09 ghi nhận `partial keyword match`; các case còn lại có ghi chú `ok`. Tổng điểm là **143/144**, không có Borderline hoặc Fail.
- **Nhận định đúng/sai khớp expected ở cả 24 case.** Các câu trả lời đúng được nhận diện đúng, còn câu sai hoặc chưa đầy đủ được phản hồi theo nhãn kỳ vọng. Đây là căn cứ cho việc sử dụng diagnosis để bổ sung feedback và lựa chọn nội dung cần củng cố trong phiên ôn.
- **21 response có 1 citation; GS-18, GS-19 và GS-20 không trả citation.** Đặc biệt, GS-20 xử lý yêu cầu nguồn không có trong hệ thống mà không thêm citation. Bộ script mới đánh dấu case này không yêu cầu citation, phù hợp với hành vi không tạo nguồn cho tài liệu chưa có.
- Latency ghi nhận **4–30 ms/case** trong lượt chạy này. Đây là thời gian phản hồi diagnosis đo bởi script, không quy đổi thành thời gian sinh câu trả lời LLM hoặc hiệu năng toàn bộ RAG.
- Smoke checks đều **PASS**: health, review-data (**3 tuần, 6 câu hỏi**), modules (**1 module**) và concepts (**1 concept**).

**Kết quả kỹ thuật theo `result (1).md`, branch `feat/core-apis`:**

| Kiểm tra | Kết quả ghi nhận |
|---|---|
| Backend pytest trong Docker | **8/8 test đạt**, 4 warnings, 2,91 giây |
| Frontend production build | **PASS** |
| Frontend API workflow | **PASS**: health, review-data, modules, concepts, diagnosis |
| Backend compile | **PASS** |
| Qdrant collection | **Green**, 3.484 points, vector 1.536 chiều, Cosine |
| Backend pytest cục bộ | Lỗi `Router.__init__()` với `on_startup`; báo cáo nhận định cần đồng bộ dependency FastAPI/Starlette với Docker |

**Kết luận nghiệm thu:** Lượt cuối đạt **100% case Pass**, vượt ngưỡng **80%**, đồng thời đáp ứng điều kiện **0 lỗi nghiêm trọng**. Kết hợp với **8/8 backend test đạt trong Docker** và các smoke checks thành công, kết quả tạo căn cứ kỹ thuật cho việc tích hợp diagnosis vào flow kiểm tra → feedback → ôn tiếp. Chất lượng được trình bày bằng case, điểm và log cụ thể, thay vì chỉ dựa trên việc API trả response thành công.

**Duy trì chất lượng:** Giữ bộ case và quality bar để kiểm tra hồi quy sau mỗi thay đổi pipeline/prompt. Hai người chấm độc lập cùng 5 output để đối chiếu cách hiểu rubric, sau đó rà các case khó cùng nguồn bài học. Lưu các lượt chạy trước và sau thay đổi để theo dõi tiến trình; bảng điểm mô phỏng được tách khỏi log kết quả thực thi.

**Hồ sơ nghiệm thu theo guide:** Lưu bộ case, script, response đầy đủ và từng lượt chạy trong `eval/`; bổ sung provenance cho ít nhất 10 case lấy hoặc phát triển từ chatlog thật. Gắn case với năm chiều coverage: topic, dạng input, mức thông tin, căn cứ nguồn và hành vi mong đợi; đối chiếu đủ hai case cho mỗi lớp ở §5, đặc biệt thiếu nguồn và citation không hỗ trợ nhận định. Trace lưu phiên bản prompt/model và nhánh LLM/fallback; kết quả thao tác UI ghi riêng cho E08–E10 và trải nghiệm đọc nguồn trong lúc chat. Đây là đầu ra của lượt đo tiếp theo; báo cáo hiện tại giữ nguyên kết quả thực tế của hồ sơ được cung cấp.

## §8. Phân công & kế hoạch

**Phân công theo README và phạm vi công việc:**

| Thành viên | Trách nhiệm |
|---|---|
| **Hồ Đăng Phúc** | Product/spec, prompt, guardrail, rubric; phối hợp chốt quality bar; slide và pitching. |
| **Nguyễn Thanh Hòa** | FastAPI, RAG, retrieval, LLM, diagnosis; golden set, evaluation và log/trace. |
| **Lê Nguyễn Trâm Anh** | UI/UX, frontend, chat/citation/quiz, tích hợp theo contract; khảo sát, user testing và slide và pitching. |

**Kế hoạch theo thứ tự phụ thuộc:**
1. Phúc phối hợp nhóm xác nhận source/rubric, lát cắt và tiêu chí đánh giá; Trâm Anh tổ chức hồ sơ survey.
2. Hòa và Phúc hoàn thiện nhánh AI có nguồn/trace; Trâm Anh tích hợp và kiểm tra interaction frontend.
3. Hòa tổ chức golden set; Phúc và Hòa chấm độc lập để hiệu chỉnh rubric, sau đó báo cáo tỷ lệ và case cần xử lý.
4. Trâm Anh điều phối validation; nhóm tổng hợp quan sát và cập nhật thay đổi theo task thực tế.
5. Phúc chuẩn bị mạch pitching, Hòa trình bày AI/evaluation, Trâm Anh trình diễn interaction và video dự phòng; dry run 5 phút với một case chuẩn và một case khó.

**Tuyển người thử:** Khảo sát có bốn phản hồi để lại email ở câu hỏi tham gia prototype: S18, S19, S20 và S22. Đây là danh sách để liên hệ; lịch tham gia và đồng ý ghi hình/quote được xác nhận trực tiếp trước phiên. Không công khai email hoặc tự gán tên người thử.

**Validation:** Mời ít nhất hai người ngoài nhóm, khoảng 10 phút/người. Giao task theo outcome: “Xác định một phần kiến thức cần củng cố, ôn phần đó và quyết định bước tiếp theo.” Người thử tự thao tác; không chỉ trước nút citation. Phiên gồm context, giao task, quan sát và hỏi sau dùng. Ghi hành động, chỗ do dự, mức trợ giúp, quote được phép sử dụng và mức nghiêm trọng trong `validation/`.

**Multi-prototype nếu thực hiện:** So sánh hỏi một câu làm rõ trước với đưa nhận xét sơ bộ có điều kiện để học viên đính chính. Dùng cùng input/source, đo tính đúng của nhận xét và khả năng tiếp tục học. Thiết kế ưu tiên hỏi rõ trước ở case mơ hồ; quyết định sau thử được lưu cùng quan sát.

## §9. Changelog

| Thời điểm | Thay đổi | Căn cứ |
|---|---|---|
| 17/09/2026 | Cập nhật kết quả kiểm thử cuối trong §7: 24/24 Pass, 0 critical failures, quality bar PASS; Docker 8/8 test đạt | `eval-run (1).md`, `test_case (1).py`, `test_case (1).md` và `result (1).md` |
| 17/09/2026 | Cập nhật evidence và bảng impact theo 22 phản hồi | Bảng survey ngày 17/09/2026; quy tắc đếm ghi tại §1 |
| 17/09/2026 | Chuẩn hóa nội dung theo flow ôn tuần và adapter API hiện tại | `frontend/src/lib/chat.ts`, `frontend/src/lib/api.ts`, `frontend/src/routes/index.tsx` |
