# 🖥️ Hướng Dẫn Training PhoBERT trên Google Colab

## Mục Lục
1. [Tổng Quan](#tổng-quan)
2. [Cách 1: Sử Dụng Notebook Có Sẵn](#cách-1-sử-dụng-notebook-có-sẵn)
3. [Cách 2: Tạo Notebook Mới](#cách-2-tạo-notebook-mới)
4. [Upload Dữ Liệu Lên Colab](#upload-dữ-liệu-lên-colab)
5. [Chạy Training](#chạy-training)
6. [Download Model Về Máy](#download-model-về-máy)
7. [Sử Dụng Model Đã Train Trên Local](#sử-dụng-model-đã-train-trên-local)
8. [Hugging Face Hub (Khuyến Nghị)](#hugging-face-hub-khuyến-nghị)
9. [Xử Lý Sự Cố](#xử-lý-sự-cố)

---

## Tổng Quan

Colab notebook (`colab_training.ipynb`) đã được tạo sẵn với:
- ✅ PhoBERT training hoàn chỉnh
- ✅ GPU acceleration (T4, V100, A100)
- ✅ Auto-save lên Google Drive
- ✅ Inference test
- ✅ Hướng dẫn kết nối với local project

---

## Cách 1: Sử Dụng Notebook Có Sẵn

### Bước 1: Mở Notebook trên Colab

```bash
# Mở file trong repository
open colab_training.ipynb
```

Sau đó:
1. Click **Open in Colab** (nếu có button)
2. Hoặc copy file lên Google Drive → Open with → Google Colab

### Bước 2: Bật GPU

1. **Runtime** → **Change runtime type** → **Hardware accelerator** → **GPU**
2. Chọn T4 (miễn phí) hoặc V100/A100 (Colab Pro)

### Bước 3: Mount Google Drive

Colab notebook sẽ tự động mount Google Drive để lưu model.

---

## Cách 2: Tạo Notebook Mới

Nếu muốn tạo notebook từ đầu:

```python
# ============================================================
# STEP 1: SETUP
# ============================================================
from google.colab import drive
drive.mount('/content/drive')

!pip install transformers torch datasets scikit-learn pandas tqdm

import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")

# ============================================================
# STEP 2: COPY DATA TỪ DRIVE
# ============================================================
# Upload file lên Drive trước, sau đó copy vào Colab
# Thay YOUR_FOLDER bằng đường dẫn thực tế
!cp -r /content/drive/MyDrive/YOUR_DATA_FOLDER/*.csv /content/

# ============================================================
# STEP 3: TRAINING
# ============================================================
# (Sử dụng code từ section 3 trong notebook)
```

---

## Upload Dữ Liệu Lên Colab

### Cách 1: Upload Trực Tiếp

```python
from google.colab import files
uploaded = files.upload()
```

### Cách 2: Từ Google Drive

```python
# Mount Drive
from google.colab import drive
drive.mount('/content/drive')

# Copy file
!cp /content/drive/MyDrive/path/to/your/data.csv /content/
```

### Cách 3: Từ GitHub

```python
!git clone https://github.com/USERNAME/REPO.git
```

---

## Chạy Training

### Cấu Hình Khuyến Nghị

| Dataset Size | GPU | Batch Size | Epochs |
|-------------|-----|------------|--------|
| < 10,000 | T4 (Free) | 16 | 3-5 |
| 10,000 - 50,000 | T4 (Free) | 16-32 | 3-5 |
| 50,000 - 100,000 | V100 (Pro) | 32 | 5-10 |
| > 100,000 | A100 (Pro+) | 64 | 5-10 |

### Training Parameters

```python
MODEL_NAME = 'vinai/phobert-base'  # Pre-trained model
EPOCHS = 5
BATCH_SIZE = 16          # Tăng lên 32 nếu có GPU lớn hơn
MAX_LEN = 128
LEARNING_RATE = 2e-5
```

### Theo Dõi Training

- Progress bar sẽ hiển thị trong notebook
- Validation F1 được in sau mỗi epoch
- Best model được tự động lưu

---

## Download Model Về Máy

### Cách 1: Trực Tiếp Từ Colab

```python
# Trong notebook, chạy:
files.download('/content/drive/MyDrive/phobert_training/phobert_depression_model.zip')
```

### Cách 2: Từ Google Drive

1. Mở https://drive.google.com
2. Tìm thư mục `phobert_training/phobert_depression_model`
3. Download về máy
4. Copy vào `models/` trong project

### Cách 3: Zip Trước

```python
# Trong notebook:
!zip -r phobert_depression_model.zip /content/drive/MyDrive/phobert_training/phobert_depression_model/
files.download('/content/phobert_depression_model.zip')
```

---

## Sử Dụng Model Đã Train Trên Local

### 1. Copy Model Vào Project

```bash
# Giả sử model đã download về ~/Downloads/phobert_depression_model/
cp -r ~/Downloads/phobert_depression_model/* models/phobert_colab_trained/
```

### 2. Cập Nhật Code Để Load Model

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Load model đã train
MODEL_DIR = Path('models/phobert_colab_trained')

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, use_fast=False)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)

# Device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
model.eval()
```

### 3. Inference

```python
def predict(text):
    prepared = prepare_text(text)  # Hàm normalize từ phobert_utils.py
    inputs = tokenizer(prepared, return_tensors='pt', truncation=True, max_length=128)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
        pred = torch.argmax(outputs.logits, dim=-1).item()
    
    return 'depression' if pred == 1 else 'normal'
```

---

## Hugging Face Hub (Khuyến Nghị)

Cách này giúp dễ dàng share và load model từ bất kỳ đâu.

### Bước 1: Tạo Hugging Face Account

1. Truy cập https://huggingface.co/
2. Sign up (miễn phí)
3. Tạo Access Token: Settings → Access Tokens → Create new token
   - Chọn type: `Write`

### Bước 2: Upload Từ Colab

```python
!pip install huggingface_hub

from huggingface_hub import HfApi, login

# Login (sẽ yêu cầu nhập token)
login()

api = HfApi()

# Upload model
api.upload_folder(
    folder_path='/content/drive/MyDrive/phobert_training/phobert_depression_model',
    repo_id='YOUR_USERNAME/phobert-depression-v1',  # Thay bằng username của bạn
    repo_type='model',
)
```

### Bước 3: Load Model Từ Hugging Face

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = 'YOUR_USERNAME/phobert-depression-v1'  # Thay bằng model của bạn

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
```

---

## Xử Lý Sự Cố

### Lỗi "No module named 'xxx'"

```python
# Cài đặt thư viện thiếu
!pip install xxx
```

### Lỗi Out of Memory (OOM)

```python
# Giảm batch size
BATCH_SIZE = 8  # Thay vì 16 hoặc 32

# Hoặc clear cache
import torch
torch.cuda.empty_cache()
```

### Mất Kết Nối Runtime

1. **Colab Free**: Thường mất kết nối sau 90 phút không tương tác
   - **Giải pháp**: Thỉnh thoảng click vào notebook hoặc chạy một cell đơn giản

2. **Colab Pro**: Ít bị mất kết nối hơn
   - **Giải pháp**: Lưu checkpoint thường xuyên

### Lưu Checkpoint Thường Xuyên

Thêm vào training loop:

```python
# Sau mỗi epoch, lưu checkpoint
checkpoint_path = OUTPUT_DIR / f'checkpoint_epoch_{epoch}.pt'
torch.save({
    'epoch': epoch,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'val_f1': val_metrics['f1_macro'],
}, checkpoint_path)

# Upload lên Drive ngay lập tức
!cp -r /content/phobert_training /content/drive/MyDrive/
```

---

## So Sánh Các Dịch Vụ Cloud

| Dịch Vụ | GPU | Giá | Giới Hạn |
|---------|-----|-----|----------|
| **Google Colab (Free)** | T4 (shared) | Miễn phí | 90 phút session |
| **Google Colab Pro** | V100/A100 | $10/tháng | 24h session |
| **Kaggle** | T4/P100 | Miễn phí | 30h GPU/tuần |
| **Lambda Labs** | RTX 3090/A100 | $0.50-2.10/hr | Pay-as-you-go |
| **RunPod** | RTX 4090/A100 | $0.20-0.80/hr | Pay-as-you-go |

---

## Liên Hệ & Hỗ Trợ

Nếu gặp vấn đề:
1. Kiểm tra notebook output để xem error message
2. Restart runtime: Runtime → Restart runtime
3. Thử lại từ đầu với fresh session

---

*Generated: July 2026*
