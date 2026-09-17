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
            summary="Cach van ban duoc cat thanh token va anh xa sang Token ID.",
        ),
        "embedding": Topic(
            id="embedding",
            name="Embedding",
            summary="Cach token duoc bieu dien thanh vector mang y nghia ngu nghia.",
        ),
        "attention": Topic(
            id="attention",
            name="Attention",
            summary="Cach mo hinh quyet dinh token nao can chu y khi sinh ket qua.",
        ),
        "tool-calling": Topic(
            id="tool-calling",
            name="Tool Calling",
            summary="Cach mo hinh goi cong cu ben ngoai de lay du lieu hoac hanh dong.",
        ),
    }

    weeks = [
        Week(
            id="w1",
            title="Tuan 1 - LLM Foundation",
            subtitle="Khai niem nen tang ve mo hinh ngon ngu lon",
            period="01/09 - 07/09",
            topics=["tokenization"],
            available=False,
        ),
        Week(
            id="w2",
            title="Tuan 2 - How LLM Works",
            subtitle="Tu token toi vector, attention va tool calling",
            period="08/09 - 14/09",
            topics=["tokenization", "embedding", "attention", "tool-calling"],
            available=True,
        ),
        Week(
            id="w3",
            title="Tuan 3 - AI Agents",
            subtitle="Vong lap lap ke hoach va hanh dong cua agent",
            period="15/09 - 21/09",
            topics=["tool-calling"],
            available=False,
        ),
    ]

    questions = [
        Question(
            id="q1",
            topic="tokenization",
            prompt="Token trong mot mo hinh ngon ngu thuong tuong ung voi dieu gi?",
            options=[
                "Luon luon la mot tu hoan chinh",
                "Mot manh van ban, co the la tu, phan cua tu hoac dau cau",
                "Mot cau hoan chinh",
                "Mot ky tu duy nhat",
            ],
            correct=1,
            why="Token la don vi van ban do tokenizer cat ra, thuong nho hon mot tu.",
            misconception="Nham token voi tu.",
        ),
        Question(
            id="q2",
            topic="embedding",
            prompt="Token ID 105 va 106 nam canh nhau. Dieu do noi len gi ve y nghia cua chung?",
            options=[
                "Chung co y nghia gan nhau",
                "Khong noi len dieu gi ve y nghia",
                "Chung luon xuat hien cung cau",
                "Chung co cung embedding vector",
            ],
            correct=1,
            why="Token ID chi la so thu tu trong tu dien, khong mang thong tin ngu nghia.",
            misconception="Nham Token ID voi Embedding Vector.",
        ),
        Question(
            id="q3",
            topic="embedding",
            prompt="Embedding vector cua mot token bieu dien dieu gi?",
            options=[
                "Vi tri cua token trong tu dien",
                "Tan suat token xuat hien",
                "Dac trung ngu nghia cua token trong khong gian nhieu chieu",
                "Do dai cua token tinh theo ky tu",
            ],
            correct=2,
            why="Embedding la vector so hoc ma hoa dac trung ngu nghia, cho phep do do tuong dong.",
            misconception="Nham Token ID voi Embedding Vector.",
        ),
        Question(
            id="q4",
            topic="attention",
            prompt="Co che attention giup mo hinh lam gi?",
            options=[
                "Nen van ban dau vao cho ngan lai",
                "Can nhac muc do lien quan giua cac token khi xu ly",
                "Chon ngon ngu dau ra",
                "Tang toc do tokenization",
            ],
            correct=1,
            why="Attention tinh trong so lien quan giua cac token de quyet dinh thong tin nao anh huong toi dau ra.",
            misconception="Xem attention nhu mot buoc nen du lieu.",
        ),
        Question(
            id="q5",
            topic="attention",
            prompt="Trong cau 'Con meo ngoi tren tham vi no am', attention giup mo hinh chu yeu de lam gi?",
            options=[
                "Dem so token trong cau",
                "Xac dinh 'no' dang noi toi 'tham'",
                "Dich cau sang tieng Anh",
                "Chuan hoa chu hoa chu thuong",
            ],
            correct=1,
            why="Attention lien ket dai tu voi danh tu phu hop dua tren trong so ngu canh.",
            misconception="Chua thay attention hoat dong o muc ngu canh.",
        ),
        Question(
            id="q6",
            topic="tool-calling",
            prompt="Khi mo hinh thuc hien tool calling, dieu gi thuc su xay ra?",
            options=[
                "Mo hinh tu chay ma ben trong trong so cua no",
                "Mo hinh sinh ra mot loi goi co cau truc de he thong ben ngoai thuc thi",
                "Mo hinh tai cong cu vao bo nho",
                "Mo hinh huan luyen lai chinh no",
            ],
            correct=1,
            why="Mo hinh chi sinh ra yeu cau goi ham; phan thuc thi nam o ung dung ben ngoai.",
            misconception="Nghi rang mo hinh tu thuc thi cong cu.",
        ),
    ]

    lessons = {
        "tokenization": Lesson(
            lesson="Bai 1 - Tokenization",
            slides=[
                LessonSlide(
                    title="Slide 3 - Token la gi?",
                    body=[
                        "Tokenizer cat van ban thanh cac manh nho goi la token.",
                        "Moi token duoc tra cuu trong tu dien de lay mot Token ID.",
                    ],
                )
            ],
        ),
        "embedding": Lesson(
            lesson="Bai 2 - Embedding",
            slides=[
                LessonSlide(
                    title="Slide 4 - Token ID vs Embedding Vector",
                    body=[
                        "Token ID la so thu tu cua token trong tu dien, khong mang y nghia.",
                        "Embedding Vector la day so hoc duoc trong qua trinh huan luyen.",
                        "Hai Token ID gan nhau khong dam bao hai token co nghia gan nhau.",
                    ],
                    note="Phan nay lien quan truc tiep toi loi nham Token ID voi embedding.",
                ),
                LessonSlide(
                    title="Slide 5 - Khoang cach ngu nghia",
                    body=[
                        "Do gan nghia duoc do bang khoang cach giua cac embedding vector.",
                        "Cac tu gan nghia co the co embedding gan nhau du Token ID cach xa.",
                    ],
                ),
            ],
        ),
        "attention": Lesson(
            lesson="Bai 3 - Attention",
            slides=[
                LessonSlide(
                    title="Slide 2 - Trong so chu y",
                    body=[
                        "Voi moi token, mo hinh tinh diem lien quan toi cac token khac.",
                        "Diem cao nghia la token do anh huong nhieu hon toi bieu dien hien tai.",
                    ],
                )
            ],
        ),
        "tool-calling": Lesson(
            lesson="Bai 4 - Tool Calling",
            slides=[
                LessonSlide(
                    title="Slide 2 - Vong doi mot loi goi cong cu",
                    body=[
                        "Mo hinh sinh ra JSON mo ta ten ham va tham so.",
                        "Ung dung thuc thi ham roi tra ket qua lai cho mo hinh.",
                    ],
                )
            ],
        ),
    }

    check_questions = {
        "embedding": [
            CheckQuestion(
                prompt="Hai token co Token ID la 105 va 106. Co the ket luan embedding cua chung gan nhau ve ngu nghia khong?",
                options=[
                    "Co, vi ID cua chung gan nhau.",
                    "Khong, Token ID khong bieu dien khoang cach ngu nghia.",
                    "Chi khi chung xuat hien trong cung mot cau.",
                    "Khong chac.",
                ],
                correct=1,
                whyCorrect="Chinh xac. Khoang cach ngu nghia nam o embedding vector.",
                whyWrong="Chua dung. Token ID chi la so thu tu trong tu dien.",
            )
        ],
        "attention": [
            CheckQuestion(
                prompt="Attention giup mo hinh xu ly dieu gi trong cau co dai tu?",
                options=[
                    "Dem so tu trong cau",
                    "Xac dinh dai tu tham chieu toi ai/cai gi",
                    "Cat cau thanh token",
                    "Chuyen cau sang chu thuong",
                ],
                correct=1,
                whyCorrect="Dung. Attention gan trong so giua dai tu va danh tu phu hop.",
                whyWrong="Chua dung. Tokenization dien ra truoc, khong phai nhiem vu chinh cua attention.",
            )
        ],
        "tokenization": [
            CheckQuestion(
                prompt="'unbelievable' co the duoc tokenizer cat thanh nhieu token khong?",
                options=[
                    "Khong, moi tu la mot token",
                    "Co, vi du un / believ / able",
                    "Chi khi viet hoa",
                    "Chi trong tieng Viet",
                ],
                correct=1,
                whyCorrect="Dung. Tokenizer thuong cat tu dai thanh cac manh nho hon.",
                whyWrong="Chua dung. Mot tu co the tuong ung nhieu token.",
            )
        ],
        "tool-calling": [
            CheckQuestion(
                prompt="Ai la nguoi thuc su thuc thi ham khi mo hinh goi cong cu?",
                options=[
                    "Chinh mo hinh",
                    "Ung dung ben ngoai",
                    "Tokenizer",
                    "Nguoi dung cuoi",
                ],
                correct=1,
                whyCorrect="Dung. Mo hinh chi sinh loi goi, ung dung moi thuc thi.",
                whyWrong="Chua dung. Mo hinh khong tu chay duoc cong cu.",
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
