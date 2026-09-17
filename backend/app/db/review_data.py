from app.schemas.curriculum import (
    CheckQuestion,
    Lesson,
    LessonSlide,
    Question,
    ReviewData,
    Topic,
    Week,
)


def get_review_data() -> ReviewData:
    """Return the current backend-owned review flow content."""

    topics = {
        "tokenization": Topic(
            id="tokenization",
            name="Tokenization",
            summary="Cách văn bản được cắt thành token và ánh xạ sang Token ID.",
        ),
        "embedding": Topic(
            id="embedding",
            name="Embedding",
            summary="Cách token được biểu diễn thành vector mang ý nghĩa ngữ nghĩa.",
        ),
        "attention": Topic(
            id="attention",
            name="Attention",
            summary="Cách mô hình quyết định token nào cần chú ý khi sinh kết quả.",
        ),
        "tool-calling": Topic(
            id="tool-calling",
            name="Tool Calling",
            summary="Cách mô hình gọi công cụ bên ngoài để lấy dữ liệu hoặc hành động.",
        ),
    }

    weeks = [
        Week(
            id="w1",
            title="Tuần 1 - LLM Foundation",
            subtitle="Khái niệm nền tảng về mô hình ngôn ngữ lớn",
            period="01/09 - 07/09",
            topics=["tokenization"],
            available=False,
        ),
        Week(
            id="w2",
            title="Tuần 2 - How LLM Works",
            subtitle="Từ token tới vector, attention và tool calling",
            period="08/09 - 14/09",
            topics=["tokenization", "embedding", "attention", "tool-calling"],
            available=True,
        ),
        Week(
            id="w3",
            title="Tuần 3 - AI Agents",
            subtitle="Vòng lặp lập kế hoạch và hành động của agent",
            period="15/09 - 21/09",
            topics=["tool-calling"],
            available=False,
        ),
    ]

    questions = [
        Question(
            id="q1",
            topic="tokenization",
            prompt="Token trong một mô hình ngôn ngữ thường tương ứng với điều gì?",
            options=[
                "Luôn luôn là một từ hoàn chỉnh",
                "Một mảnh văn bản, có thể là từ, phần của từ hoặc dấu câu",
                "Một câu hoàn chỉnh",
                "Một ký tự duy nhất",
            ],
            correct=1,
            why="Token là đơn vị văn bản do tokenizer cắt ra, thường nhỏ hơn một từ.",
            misconception="Nhầm token với từ.",
        ),
        Question(
            id="q2",
            topic="embedding",
            prompt="Token ID 105 và 106 nằm cạnh nhau. Điều đó nói lên gì về ý nghĩa của chúng?",
            options=[
                "Chúng có ý nghĩa gần nhau",
                "Không nói lên điều gì về ý nghĩa",
                "Chúng luôn xuất hiện cùng câu",
                "Chúng có cùng embedding vector",
            ],
            correct=1,
            why="Token ID chỉ là số thứ tự trong từ điển, không mang thông tin ngữ nghĩa.",
            misconception="Nhầm Token ID với Embedding Vector.",
        ),
        Question(
            id="q3",
            topic="embedding",
            prompt="Embedding vector của một token biểu diễn điều gì?",
            options=[
                "Vị trí của token trong từ điển",
                "Tần suất token xuất hiện",
                "Đặc trưng ngữ nghĩa của token trong không gian nhiều chiều",
                "Độ dài của token tính theo ký tự",
            ],
            correct=2,
            why="Embedding là vector số học mã hóa đặc trưng ngữ nghĩa, cho phép đo độ tương đồng.",
            misconception="Nhầm Token ID với Embedding Vector.",
        ),
        Question(
            id="q4",
            topic="attention",
            prompt="Cơ chế attention giúp mô hình làm gì?",
            options=[
                "Nén văn bản đầu vào cho ngắn lại",
                "Cân nhắc mức độ liên quan giữa các token khi xử lý",
                "Chọn ngôn ngữ đầu ra",
                "Tăng tốc độ tokenization",
            ],
            correct=1,
            why="Attention tính trọng số liên quan giữa các token để quyết định thông tin nào ảnh hưởng tới đầu ra.",
            misconception="Xem attention như một bước nén dữ liệu.",
        ),
        Question(
            id="q5",
            topic="attention",
            prompt="Trong câu 'Con mèo ngồi trên thảm vì nó ấm', attention giúp mô hình chủ yếu để làm gì?",
            options=[
                "Đếm số token trong câu",
                "Xác định 'nó' đang nói tới 'thảm'",
                "Dịch câu sang tiếng Anh",
                "Chuẩn hóa chữ hoa chữ thường",
            ],
            correct=1,
            why="Attention liên kết đại từ với danh từ phù hợp dựa trên trọng số ngữ cảnh.",
            misconception="Chưa thấy attention hoạt động ở mức ngữ cảnh.",
        ),
        Question(
            id="q6",
            topic="tool-calling",
            prompt="Khi mô hình thực hiện tool calling, điều gì thực sự xảy ra?",
            options=[
                "Mô hình tự chạy mã bên trong trọng số của nó",
                "Mô hình sinh ra một lời gọi có cấu trúc để hệ thống bên ngoài thực thi",
                "Mô hình tải công cụ vào bộ nhớ",
                "Mô hình huấn luyện lại chính nó",
            ],
            correct=1,
            why="Mô hình chỉ sinh ra yêu cầu gọi hàm; phần thực thi nằm ở ứng dụng bên ngoài.",
            misconception="Nghĩ rằng mô hình tự thực thi công cụ.",
        ),
    ]

    lessons = {
        "tokenization": Lesson(
            lesson="Bài 1 - Tokenization",
            slides=[
                LessonSlide(
                    title="Slide 3 - Token là gì?",
                    body=[
                        "Tokenizer cắt văn bản thành các mảnh nhỏ gọi là token.",
                        "Mỗi token được tra cứu trong từ điển để lấy một Token ID.",
                    ],
                )
            ],
        ),
        "embedding": Lesson(
            lesson="Bài 2 - Embedding",
            slides=[
                LessonSlide(
                    title="Slide 4 - Token ID vs Embedding Vector",
                    body=[
                        "Token ID là số thứ tự của token trong từ điển, không mang ý nghĩa.",
                        "Embedding Vector là dãy số học được trong quá trình huấn luyện.",
                        "Hai Token ID gần nhau không đảm bảo hai token có nghĩa gần nhau.",
                    ],
                    note="Phần này liên quan trực tiếp tới lỗi nhầm Token ID với embedding.",
                ),
                LessonSlide(
                    title="Slide 5 - Khoảng cách ngữ nghĩa",
                    body=[
                        "Độ gần nghĩa được đo bằng khoảng cách giữa các embedding vector.",
                        "Các từ gần nghĩa có thể có embedding gần nhau dù Token ID cách xa.",
                    ],
                ),
            ],
        ),
        "attention": Lesson(
            lesson="Bài 3 - Attention",
            slides=[
                LessonSlide(
                    title="Slide 2 - Trọng số chú ý",
                    body=[
                        "Với mỗi token, mô hình tính điểm liên quan tới các token khác.",
                        "Điểm cao nghĩa là token đó ảnh hưởng nhiều hơn tới biểu diễn hiện tại.",
                    ],
                )
            ],
        ),
        "tool-calling": Lesson(
            lesson="Bài 4 - Tool Calling",
            slides=[
                LessonSlide(
                    title="Slide 2 - Vòng đời một lời gọi công cụ",
                    body=[
                        "Mô hình sinh ra JSON mô tả tên hàm và tham số.",
                        "Ứng dụng thực thi hàm rồi trả kết quả lại cho mô hình.",
                    ],
                )
            ],
        ),
    }

    check_questions = {
        "embedding": [
            CheckQuestion(
                prompt="Hai token có Token ID là 105 và 106. Có thể kết luận embedding của chúng gần nhau về ngữ nghĩa không?",
                options=[
                    "Có, vì ID của chúng gần nhau.",
                    "Không, Token ID không biểu diễn khoảng cách ngữ nghĩa.",
                    "Chỉ khi chúng xuất hiện trong cùng một câu.",
                    "Không chắc.",
                ],
                correct=1,
                whyCorrect="Chính xác. Khoảng cách ngữ nghĩa nằm ở embedding vector.",
                whyWrong="Chưa đúng. Token ID chỉ là số thứ tự trong từ điển.",
            )
        ],
        "attention": [
            CheckQuestion(
                prompt="Attention giúp mô hình xử lý điều gì trong câu có đại từ?",
                options=[
                    "Đếm số từ trong câu",
                    "Xác định đại từ tham chiếu tới ai/cái gì",
                    "Cắt câu thành token",
                    "Chuyển câu sang chữ thường",
                ],
                correct=1,
                whyCorrect="Đúng. Attention gắn trọng số giữa đại từ và danh từ phù hợp.",
                whyWrong="Chưa đúng. Tokenization diễn ra trước, không phải nhiệm vụ chính của attention.",
            )
        ],
        "tokenization": [
            CheckQuestion(
                prompt="'unbelievable' có thể được tokenizer cắt thành nhiều token không?",
                options=[
                    "Không, mỗi từ là một token",
                    "Có, ví dụ un / believ / able",
                    "Chỉ khi viết hoa",
                    "Chỉ trong tiếng Việt",
                ],
                correct=1,
                whyCorrect="Đúng. Tokenizer thường cắt từ dài thành các mảnh nhỏ hơn.",
                whyWrong="Chưa đúng. Một từ có thể tương ứng nhiều token.",
            )
        ],
        "tool-calling": [
            CheckQuestion(
                prompt="Ai là người thực sự thực thi hàm khi mô hình gọi công cụ?",
                options=[
                    "Chính mô hình",
                    "Ứng dụng bên ngoài",
                    "Tokenizer",
                    "Người dùng cuối",
                ],
                correct=1,
                whyCorrect="Đúng. Mô hình chỉ sinh lời gọi, ứng dụng mới thực thi.",
                whyWrong="Chưa đúng. Mô hình không tự chạy được công cụ.",
            )
        ],
    }

    return ReviewData(
        topics=topics,
        weeks=weeks,
        questions=questions,
        lessons=lessons,
        check_questions=check_questions,
    )
