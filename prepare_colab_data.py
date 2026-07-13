"""
Prepare data for Google Colab training.

Chạy script này trước khi upload lên Colab:
    python prepare_colab_data.py

Script sẽ:
1. Copy các file data cần thiết vào thư mục colab_data/
2. Nén thành file zip để upload lên Google Drive
3. Tạo file hướng dẫn setup trên Colab
"""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[0]
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "colab_data"


def main():
    print("=" * 60)
    print("PREPARE DATA FOR GOOGLE COLAB")
    print("=" * 60)

    # Tạo thư mục output
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Các file data cần thiết cho training
    required_files = [
        ("data/final_train.csv", "final_train.csv"),
        ("data/final_val.csv", "final_val.csv"),
        ("data/final_test.csv", "final_test.csv"),
        ("data_unified/cross_domain_test.csv", "cross_domain_test.csv"),
    ]

    print("\n1. Copying data files...")
    copied = []
    for src_name, dst_name in required_files:
        src = PROJECT_DIR / src_name
        dst = OUTPUT_DIR / dst_name

        if src.exists():
            shutil.copy2(src, dst)
            size_kb = dst.stat().st_size / 1024
            print(f"   ✓ {dst_name} ({size_kb:.1f} KB)")
            copied.append(dst_name)
        else:
            print(f"   ✗ Missing: {src_name}")

    if not copied:
        print("\nLỗi: Không có file data nào được copy!")
        print("Vui lòng đảm bảo các file data tồn tại.")
        return

    # Copy model config (nếu muốn tiếp tục train từ model đã có)
    print("\n2. Copying model configs...")
    model_configs = [
        ("models/phobert_second/config.json", "phobert_config.json"),
        ("yt_depression_crawler/core/config.py", "config.py"),
    ]

    for src_name, dst_name in model_configs:
        src = PROJECT_DIR / src_name
        dst = OUTPUT_DIR / dst_name

        if src.exists():
            if src.is_dir():
                shutil.copytree(src, OUTPUT_DIR / src_name.split("/")[-1])
            else:
                shutil.copy2(src, dst)
            print(f"   ✓ {dst_name}")
        else:
            print(f"   - Skipped: {src_name} (not found)")

    # Tạo file metadata
    print("\n3. Creating metadata...")
    metadata = {
        "created_at": datetime.now().isoformat(),
        "files": copied,
        "project": "YouTube Depression Detection",
        "model": "vinai/phobert-base",
        "notes": [
            "final_train.csv: Training data",
            "final_val.csv: Validation data",
            "final_test.csv: In-domain test data",
            "cross_domain_test.csv: Cross-domain test data",
        ],
    }

    metadata_file = OUTPUT_DIR / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    print(f"   ✓ metadata.json")

    # Tạo file zip để upload lên Google Drive
    print("\n4. Creating zip archive...")
    zip_name = f"colab_data_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
    zip_path = PROJECT_DIR / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in OUTPUT_DIR.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(OUTPUT_DIR)
                zf.write(file, arcname)

    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"   ✓ {zip_path} ({zip_size_mb:.2f} MB)")

    # Tạo file hướng dẫn Colab
    print("\n5. Creating Colab instructions...")
    instructions = """# 📋 Hướng Dẫn Upload Lên Google Colab

## Bước 1: Upload File ZIP Lên Google Drive

1. Truy cập https://drive.google.com
2. Tạo thư mục mới, ví dụ: `phobert_training`
3. Upload file `{ZIP_NAME}` vào thư mục đó

## Bước 2: Mở Google Colab

1. Truy cập https://colab.research.google.com
2. Tạo notebook mới hoặc mở `colab_training.ipynb`

## Bước 3: Mount Google Drive Trong Colab

```python
from google.colab import drive
drive.mount('/content/drive')

# Giải nén data
!unzip /content/drive/MyDrive/phobert_training/{ZIP_NAME} -d /content/
```

## Bước 4: Verify Data

```python
import os
data_files = os.listdir('/content/colab_data/')
print("Data files:", data_files)
```

## Bước 5: Chạy Training

Mở notebook `colab_training.ipynb` và chạy các cells.
Đảm bảo:
- Runtime > Change runtime type > GPU
- Sửa `DATA_DIR` trong notebook thành `/content/colab_data/`

---

## Tổng Kết

- **File ZIP**: `{ZIP_NAME}`
- **Thư mục Google Drive**: `phobert_training/`
- **Thư mục trong Colab**: `/content/colab_data/`
- **Colab Notebook**: `colab_training.ipynb`
""".format(ZIP_NAME=zip_name)

    instructions_file = OUTPUT_DIR / "UPLOAD_INSTRUCTIONS.md"
    instructions_file.write_text(instructions)
    print(f"   ✓ UPLOAD_INSTRUCTIONS.md")

    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print(f"""
Tiếp theo:

1. Upload '{zip_name}' lên Google Drive
   - Tạo thư mục: phobert_training
   - Upload file vào thư mục đó

2. Mở 'colab_training.ipynb' trên Google Colab

3. Mount Drive và chạy notebook:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   !unzip /content/drive/MyDrive/phobert_training/{zip_name} -d /content/
   ```

4. Trong notebook, sửa đường dẫn:
   - DATA_DIR = '/content/colab_data/'

5. Chạy training với GPU!
   - Runtime > Change runtime type > GPU
""")

    return {
        "zip_file": str(zip_path),
        "data_dir": str(OUTPUT_DIR),
        "instructions": str(instructions_file),
    }


if __name__ == "__main__":
    main()
