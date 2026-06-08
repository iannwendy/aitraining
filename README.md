# YouTube Depression Comment Crawler

Dự án Python dùng YouTube Data API v3 chính thức để tự động tìm video và thu thập comment công khai phục vụ đề tài: **Phát hiện dấu hiệu trầm cảm trong văn bản tiếng Việt trên mạng xã hội sử dụng các mô hình học sâu**.

Chương trình không dùng Selenium, không lấy reply comment, không lưu tên người dùng, không lưu avatar và không tự gán nhãn `depression/normal`.

## Cấu trúc dự án

```text
youtube_depression_crawler/
├── main.py
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── Dockerfile
├── docker-compose.yml
├── yt_depression_crawler/
│   ├── core/
│   │   ├── config.py
│   │   └── keywords.py
│   ├── ingestion/
│   │   ├── youtube_client.py
│   │   └── crawler.py
│   ├── processing/
│   │   ├── cleaner.py
│   │   └── storage.py
│   ├── labeling/
│   │   ├── label_config.py
│   │   ├── auto_labeler.py
│   │   ├── dataset_sampler.py
│   │   ├── review_sampler.py
│   │   ├── gold_builder.py
│   │   ├── review_evaluator.py
│   │   └── gold_baseline_eval.py
│   ├── modeling/
│   │   ├── train_splitter.py
│   │   ├── baseline/
│   │   │   └── baseline_model.py
│   │   └── phobert/
│   │       ├── phobert_utils.py
│   │       ├── phobert_train.py
│   │       ├── phobert_predict.py
│   │       └── phobert_postprocess.py
│   ├── pipelines/
│   │   ├── labeling_pipeline.py
│   │   ├── ml_pipeline.py
│   │   ├── gold_pipeline.py
│   │   └── phobert_pipeline.py
│   └── web/
│       ├── app.py
│       └── web_manager.py
├── logs/
├── models/
└── data/
    ├── raw_comments.csv
    ├── cleaned_comments.csv
    ├── processed_videos.txt
    └── video_metadata.csv
```

## 1. Tạo YouTube API key

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/).
2. Tạo project mới hoặc chọn project đang có.
3. Vào **APIs & Services** > **Library**.
4. Tìm và bật **YouTube Data API v3**.
5. Vào **APIs & Services** > **Credentials**.
6. Chọn **Create credentials** > **API key**.
7. Sao chép API key vừa tạo.

Khuyến nghị: giới hạn API key theo API **YouTube Data API v3** trong phần key restrictions để giảm rủi ro lộ key.

## 2. Tạo file `.env`

Trong thư mục dự án, tạo file `.env` từ file mẫu:

```bash
cd youtube_depression_crawler
cp .env.example .env
```

Mở `.env` và thay giá trị:

```env
YOUTUBE_API_KEY=your_real_api_key_here
```

Không hard-code API key vào source code và không commit file `.env` lên GitHub.

## 3. Cài thư viện

Khuyến nghị dùng virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Chạy chương trình

```bash
python main.py
```

Khi chạy, chương trình sẽ tự động:

1. Load API key từ `.env`.
2. Sinh danh sách keyword tiếng Việt trong `yt_depression_crawler/core/keywords.py` và keyword bổ sung trong `yt_depression_crawler/core/config.py`.
3. Search video YouTube theo từng keyword.
4. Lấy `video_id`, title, channel, thời gian đăng.
5. Crawl top-level comment công khai.
6. Lưu dần comment vào `data/raw_comments.csv` sau mỗi video.
7. Lưu metadata video vào `data/video_metadata.csv`.
8. Ghi video đã xử lý vào `data/processed_videos.txt` để lần sau không crawl lại.
9. Làm sạch dữ liệu và xuất `data/cleaned_comments.csv`.
10. Ghi log tiến trình vào `logs/crawler.log`.

## 4.1. Chạy dashboard web

Dự án có dashboard Flask để theo dõi trạng thái crawl theo thời gian thực và điều khiển bằng nút **Start/Stop**.

Chạy local không dùng Docker:

```bash
source .venv/bin/activate
python app.py
```

Mở trình duyệt tại:

```text
http://127.0.0.1:8000
```

Dashboard hiển thị:

- Trạng thái API hiện tại: `ready`, `running`, `stopping`, `completed`, `stopped`, `quota_exceeded`, `error`, `missing_api_key`.
- Số comment raw hiện có.
- Số comment cleaned hiện có.
- Số video đã xử lý.
- Tiến độ tới mốc `TARGET_RAW_COMMENTS`.
- Keyword/video đang xử lý.
- Log gần nhất.

Nút **Stop** là dừng mềm. Nếu crawler đang chờ YouTube API trả kết quả, chương trình sẽ dừng sau khi request hiện tại hoàn tất.

## 4.2. Chạy bằng Docker

Yêu cầu Docker Desktop hoặc Docker Engine đang chạy.

Build và chạy:

```bash
docker compose up --build
```

Mở dashboard:

```text
http://127.0.0.1:8000
```

Dừng container:

```bash
docker compose down
```

`docker-compose.yml` mount thư mục `data/` và `logs/` từ máy host vào container, nên dữ liệu CSV, trạng thái resume và log vẫn được giữ sau khi restart container.

## 5. Chỉnh số lượng crawl

Mở `yt_depression_crawler/core/config.py` và chỉnh các biến sau:

```python
MAX_KEYWORDS = None
MAX_VIDEOS_PER_KEYWORD = 100
MAX_COMMENTS_PER_VIDEO = 100
TARGET_RAW_COMMENTS = 500_000
SEARCH_ORDER = "relevance"
ADDITIONAL_KEYWORDS = []
```

Ý nghĩa:

- `MAX_KEYWORDS`: số keyword tối đa cần dùng. `None` nghĩa là dùng toàn bộ keyword.
- `MAX_VIDEOS_PER_KEYWORD`: số video tối đa tìm cho mỗi keyword.
- `MAX_COMMENTS_PER_VIDEO`: số top-level comment tối đa lấy từ mỗi video.
- `TARGET_RAW_COMMENTS`: dừng pipeline khi `raw_comments.csv` đạt mốc này. `None` nghĩa là không đặt mốc dừng.
- `SEARCH_ORDER`: thứ tự search của YouTube, ví dụ `relevance`, `date`, `viewCount`, `rating`, `title`.
- `ADDITIONAL_KEYWORDS`: keyword tự bổ sung, ví dụ:

```python
ADDITIONAL_KEYWORDS = ["áp lực thi đại học", "mất phương hướng tuổi 20"]
```

Cấu hình mặc định hiện tại hướng tới tập dữ liệu khoảng 500.000 comment raw. Với khoảng 50 keyword, trần lý thuyết là khoảng `50 * 100 * 100 = 500.000` comment trước lọc, nhưng thực tế thường thấp hơn vì video có thể ít comment, tắt comment, bị trùng hoặc bị lọc spam/ngắn.

## 6. Resume khi dừng giữa chừng

Chương trình lưu video đã xử lý vào:

```text
data/processed_videos.txt
```

Nếu bị dừng hoặc mất mạng, chạy lại:

```bash
python main.py
```

Các video đã có trong `processed_videos.txt` sẽ được bỏ qua. Dữ liệu comment cũng được chống trùng theo nội dung comment.

## 7. File dữ liệu đầu ra

`data/raw_comments.csv` gồm các cột:

- `comment_id`
- `video_id`
- `video_title`
- `keyword`
- `comment_text`
- `like_count`
- `published_at`

`data/cleaned_comments.csv` là bản đã:

- Xóa dòng rỗng.
- Xóa comment dưới 5 ký tự.
- Xóa trùng theo `comment_id` nếu có.
- Chuẩn hóa khoảng trắng.
- Xóa trùng theo `comment_text`.
- Lọc spam cơ bản như URL, quảng cáo đăng ký kênh, chuỗi ký tự lặp quá dài.
- Giữ Unicode tiếng Việt và emoji vì emoji có thể biểu đạt cảm xúc.

`data/video_metadata.csv` gồm:

- `video_id`
- `title`
- `channel`
- `published_at`
- `keyword`

## 8. Xử lý lỗi thường gặp

### Missing YOUTUBE_API_KEY

Kiểm tra đã tạo file `.env` trong đúng thư mục `youtube_depression_crawler/` và có dòng:

```env
YOUTUBE_API_KEY=your_real_api_key_here
```

### Quota exceeded

YouTube Data API có quota theo ngày. Khi gặp lỗi quota:

- Chờ quota reset vào ngày tiếp theo.
- Giảm `MAX_KEYWORDS`, `MAX_VIDEOS_PER_KEYWORD`, `MAX_COMMENTS_PER_VIDEO`.
- Dùng `SEARCH_ORDER = "relevance"` hoặc cấu hình phù hợp để hạn chế search dư thừa.
- Kiểm tra quota trong Google Cloud Console.

Chương trình sẽ ghi lỗi quota vào `logs/crawler.log` và dừng crawl để tránh đánh dấu nhầm video chưa xử lý.

### Comments disabled

Một số video tắt bình luận. Chương trình sẽ ghi warning vào log và tiếp tục video khác.

### Lỗi mạng tạm thời

Google API client có retry cơ bản. Nếu vẫn lỗi, chương trình log lỗi và tiếp tục, hoặc bạn có thể chạy lại sau nhờ cơ chế resume.

## 9. Lưu ý đạo đức dữ liệu

- Chỉ thu thập comment công khai trên YouTube.
- Không lưu tên người dùng.
- Không lưu avatar.
- Không lưu thông tin cá nhân không cần thiết.
- Không dùng dữ liệu để chẩn đoán y tế cho cá nhân.
- Không tự kết luận một người bị trầm cảm chỉ từ comment.
- Chỉ sử dụng dữ liệu cho nghiên cứu học thuật, phân tích tổng hợp hoặc huấn luyện mô hình theo quy trình đạo đức dữ liệu phù hợp.
- Khi công bố nghiên cứu, nên ẩn hoặc rút gọn trích dẫn comment để giảm rủi ro tái định danh.

## 10. Ghi chú kỹ thuật

- Dùng Python 3.
- Dùng `google-api-python-client`, `pandas`, `python-dotenv`, `tqdm`.
- Không dùng database để sinh viên dễ chạy.
- Không crawl reply comment để giữ pipeline đơn giản.
- Không gọi API ngoài YouTube.

## 11. Auto-label bằng keyword scoring

Sau khi đã có `data/cleaned_comments.csv`, có thể chạy pipeline weak labeling:

```bash
python -m yt_depression_crawler.pipelines.labeling_pipeline
```

Pipeline này tạo 3 file:

```text
data/auto_labeled_comments.csv
data/initial_train.csv
data/labeling_report.json
```

`auto_labeled_comments.csv` có đúng các cột:

```text
comment_text
weak_label
confidence
depression_score
matched_keywords
need_review
```

Luật scoring mặc định trong `yt_depression_crawler/core/config.py`:

```python
DEPRESSION_STRONG_WEIGHT = 5
DEPRESSION_MEDIUM_WEIGHT = 3
NORMAL_WEIGHT = -2
DEPRESSION_AUTO_THRESHOLD = 5
NORMAL_AUTO_THRESHOLD = -2
```

Nhãn tạm:

- `score >= 5`: `depression_auto`
- `score <= -2`: `normal_auto`
- Còn lại: `uncertain`

`initial_train.csv` chỉ lấy mẫu tự tin cao, `need_review == False`, không trùng nội dung, độ dài hợp lý. Mặc định cố gắng lấy:

```python
INITIAL_TRAIN_DEPRESSION_SAMPLES = 10_000
INITIAL_TRAIN_NORMAL_SAMPLES = 10_000
```

Nếu dữ liệu hiện tại chưa đủ mẫu high-confidence, chương trình lấy tối đa số mẫu đủ điều kiện và ghi số liệu vào `labeling_report.json`.

Dashboard web cũng có các nút:

- **Label Pipeline**: chạy auto-label và build initial train.
- **Auto Label**: chỉ tạo `auto_labeled_comments.csv`.
- **Build Train**: chỉ tạo `initial_train.csv` từ file auto-labeled hiện có.

Lưu ý: đây là weak label để tạo tập train ban đầu, không phải nhãn y tế hay nhãn ground truth. Các mẫu `uncertain` hoặc `need_review=True` nên được review thủ công nếu dùng cho đánh giá chất lượng mô hình.

## 12. Chuẩn bị train và baseline model

Sau khi đã có `initial_train.csv`, chạy pipeline ML:

```bash
python -m yt_depression_crawler.pipelines.ml_pipeline
```

Pipeline này tạo:

```text
data/review_samples.csv
data/train.csv
data/val.csv
data/test.csv
models/tfidf_logreg.joblib
models/baseline_metrics.json
```

Ý nghĩa:

- `review_samples.csv`: 5 nhóm mẫu để kiểm tra thủ công gồm `depression_high`, `normal_high`, `uncertain`, `need_review`, `boundary`.
- `train.csv`, `val.csv`, `test.csv`: split stratified từ `initial_train.csv`, label số `normal=0`, `depression=1`.
- `tfidf_logreg.joblib`: baseline model TF-IDF + Logistic Regression.
- `baseline_metrics.json`: accuracy, precision, recall, F1 và confusion matrix trên validation/test.

Dashboard web có thêm các nút:

- **ML Pipeline**: tạo review samples, tạo split và train baseline.
- **Review Set**: chỉ tạo `review_samples.csv`.
- **Split**: chỉ tạo `train.csv`, `val.csv`, `test.csv`.
- **Baseline**: chỉ train baseline từ split hiện có.

Lưu ý quan trọng: baseline metrics hiện đo khả năng học lại weak labels, không phải chất lượng phát hiện trầm cảm thật. Chỉ dùng baseline để kiểm tra pipeline, phát hiện lỗi dữ liệu và có mốc so sánh ban đầu trước khi train mô hình sâu như PhoBERT/viBERT.

## 13. Gold review và đánh giá trên nhãn thủ công

Sau khi review `data/review_samples.csv`, điền cột `final_label` bằng một trong các giá trị:

```text
depression
normal
uncertain
exclude
```

Nếu muốn tự chốt theo nhãn gợi ý, có thể điền:

- `suggested_label=depression` -> `final_label=depression`
- `suggested_label=normal` -> `final_label=normal`
- `suggested_label` rỗng -> `final_label=uncertain`

Sau đó chạy:

```bash
python -m yt_depression_crawler.pipelines.gold_pipeline
```

Pipeline này tạo:

```text
data/gold_review.csv
data/review_eval_report.json
data/review_eval_errors.csv
models/baseline_gold_metrics.json
data/baseline_gold_errors.csv
```

Ý nghĩa:

- `gold_review.csv`: chỉ lấy các dòng `final_label` là `depression` hoặc `normal`, map `normal=0`, `depression=1`.
- `review_eval_report.json`: đo mức khớp giữa weak label và nhãn review.
- `review_eval_errors.csv`: các lỗi của weak label so với gold review.
- `baseline_gold_metrics.json`: đánh giá baseline model trên gold review.
- `baseline_gold_errors.csv`: các lỗi baseline model trên gold review để phân tích false positive/false negative.

Dashboard có thêm các nút:

- **Gold Pipeline**: build gold set, evaluate weak labels và evaluate baseline on gold.
- **Build Gold**: chỉ tạo `gold_review.csv`.
- **Eval Weak**: chỉ đánh giá weak labels trên gold.
- **Eval Gold Baseline**: chỉ đánh giá baseline model trên gold.

Nếu `final_label` được tự điền đúng bằng `suggested_label`, weak-label accuracy có thể đạt 100% vì gold đang phản ánh chính gợi ý của hệ thống. Để đánh giá khách quan hơn, nên sửa thủ công các dòng sai trong `final_label` trước khi chạy `python -m yt_depression_crawler.pipelines.gold_pipeline`.

## 14. Train PhoBERT lần 1 và gán nhãn phần còn lại

Sau khi đã có `data/train.csv`, `data/val.csv`, `data/test.csv` từ tập high-confidence, train PhoBERT lần 1:

```bash
python -m yt_depression_crawler.modeling.phobert.phobert_train
```

Kết quả được lưu tại:

```text
models/phobert_first/
models/phobert_first/phobert_metrics.json
```

Sau đó dùng checkpoint PhoBERT để gán nhãn các comment còn lại, tức các dòng `uncertain` hoặc không phải `confidence=high` trong `data/auto_labeled_comments.csv`:

```bash
python -m yt_depression_crawler.modeling.phobert.phobert_predict
```

File đầu ra:

```text
data/phobert_remaining_predictions.csv
```

Các cột chính:

- `comment_text`: nội dung comment đã làm sạch.
- `source_weak_label`: nhãn keyword-scoring ban đầu.
- `phobert_label`: nhãn PhoBERT dự đoán, gồm `depression` hoặc `normal`.
- `probability`: xác suất của nhãn được chọn.
- `prob_normal`, `prob_depression`: xác suất từng lớp.

Để tách tiếp các mẫu tự tin cao và mẫu khó cần review active learning:

```bash
python -m yt_depression_crawler.modeling.phobert.phobert_postprocess
```

File đầu ra:

```text
data/phobert_confident_predictions.csv
data/phobert_active_learning_samples.csv
models/phobert_first/phobert_postprocess_report.json
```

Ý nghĩa:

- `phobert_confident_predictions.csv`: pseudo-label từ PhoBERT với `probability >= PHOBERT_PSEUDO_LABEL_PROB_THRESHOLD`, mặc định `0.90`. File này có thể dùng làm dữ liệu mở rộng cho vòng train sau, nhưng vẫn nên xem là nhãn bán tự động.
- `phobert_active_learning_samples.csv`: các mẫu khó như xác suất thấp, gần ranh giới, hoặc bất đồng giữa keyword scoring và PhoBERT. Đây là file nên review thủ công trước khi tạo `final_dataset.csv`.

Có thể chạy toàn bộ 3 bước bằng:

```bash
python -m yt_depression_crawler.pipelines.phobert_pipeline
```

Dashboard web có các nút:

- **PhoBERT Pipeline**: train, predict và postprocess.
- **Train PhoBERT**: chỉ train checkpoint.
- **Predict Remaining**: chỉ gán nhãn phần còn lại.
- **PhoBERT Postprocess**: chỉ tách pseudo-label confidence cao và active-learning samples từ file prediction hiện có.

Lưu ý: PhoBERT lần 1 được train từ weak labels confidence cao, nên prediction của PhoBERT là pseudo-label hỗ trợ nghiên cứu, chưa phải ground truth y tế. Tập `final_dataset.csv` chỉ nên tạo sau khi review các mẫu khó và thống nhất quy tắc gán nhãn.
