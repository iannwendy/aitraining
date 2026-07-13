"""
Colab Helper Script - Download PhoBERT model từ Google Drive về local.

Usage:
    python colab_helper.py download --model-id YOUR_USERNAME/phobert-depression-v1
    python colab_helper.py download --drive-path /content/drive/MyDrive/phobert_training/
    python colab_helper.py upload-local --local-path ./models/my_model --repo-id YOUR_USERNAME/phobert-depression-v1
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

# Thêm project root vào path
PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))


def download_from_huggingface(model_id: str, output_dir: str):
    """Download model từ Hugging Face Hub."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Cài đặt huggingface_hub...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
        from huggingface_hub import snapshot_download

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {model_id}...")
    local_dir = snapshot_download(repo_id=model_id, repo_type="model")

    # Copy files
    local_path = Path(local_dir)
    for item in local_path.iterdir():
        dest = output_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    print(f"Model saved to: {output_path}")
    return output_path


def download_from_gdrive(drive_path: str, output_dir: str):
    """Download model từ Google Drive (cần gdown)."""
    import subprocess

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading from: {drive_path}")

    # Try using gdown
    try:
        subprocess.run(["pip", "install", "gdown"], check=True)
        subprocess.run(["gdown", "--folder", drive_path, "-O", str(output_path)], check=True)
    except subprocess.CalledProcessError:
        print("gdown failed, trying direct copy...")
        # Alternative: mount Drive vào Colab, chạy notebook để copy
        print(f"""
Vui lòng làm theo cách sau:
1. Mở notebook trên Colab
2. Thêm cell sau và chạy:

from google.colab import drive
drive.mount('/content/drive')

import shutil
import os
os.makedirs('{output_dir}', exist_ok=True)
shutil.copytree('{drive_path}', '{output_dir}/phobert_model', dirs_exist_ok=True)
files.download('{output_dir}/phobert_model.zip')
        """)

    print(f"Model saved to: {output_path}")
    return output_path


def upload_to_huggingface(local_path: str, repo_id: str, commit_message: str = "Upload PhoBERT model"):
    """Upload model local lên Hugging Face Hub."""
    try:
        from huggingface_hub import HfApi, login
    except ImportError:
        print("Cài đặt huggingface_hub...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
        from huggingface_hub import HfApi, login

    # Login
    print("Logging in to Hugging Face...")
    login()

    api = HfApi()

    print(f"Uploading {local_path} to {repo_id}...")
    api.upload_folder(
        folder_path=local_path,
        repo_id=repo_id,
        repo_type="model",
        commit_message=commit_message,
    )

    print(f"""
Upload thành công!
Model của bạn tại: https://huggingface.co/{repo_id}

Để sử dụng:
    tokenizer = AutoTokenizer.from_pretrained('{repo_id}')
    model = AutoModelForSequenceClassification.from_pretrained('{repo_id}')
""")


def import_to_project(model_path: str, target_name: str = "phobert_colab"):
    """Import model đã download vào project structure."""
    source = Path(model_path)
    target_dir = PROJECT_ROOT / "models" / target_name

    if not source.exists():
        print(f"Lỗi: Không tìm thấy model tại {source}")
        print("Vui lòng download model trước.")
        return None

    # Check required files
    required = ["config.json", "tokenizer.json"]
    tokenizer_files = ["vocab.json", "merges.txt"]  # PhoBERT specific

    has_tokenizer = any((source / f).exists() for f in tokenizer_files)
    has_model = (source / "model.safetensors").exists() or (source / "pytorch_model.bin").exists()

    if not has_model:
        print(f"Cảnh báo: Không tìm thấy model weights trong {source}")

    # Copy
    print(f"Copying model to: {target_dir}")
    if target_dir.exists():
        print(f"  (Overwriting existing {target_name})")
        shutil.rmtree(target_dir)

    shutil.copytree(source, target_dir)

    # Update results registry
    registry_file = PROJECT_ROOT / "models" / "results_registry.json"
    registry = {}
    if registry_file.exists():
        try:
            registry = json.loads(registry_file.read_text())
        except json.JSONDecodeError:
            registry = {}

    registry[target_name] = {
        "path": str(target_dir),
        "source": "google_colab",
        "model_id": source.name,
    }

    registry_file.write_text(json.dumps(registry, indent=2))

    print(f"""
Model đã import thành công!

Sử dụng trong code:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_dir = 'models/{target_name}'
    tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
""")


def create_inference_script(model_name: str):
    """Tạo script inference cho model đã train."""
    script_content = f'''"""Inference script cho model: {model_name}"""

from __future__ import annotations

import torch
from pathlib import Path
from transformers import AutoModelForSequenceClassification, AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "models" / "{model_name}"

# Load model
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), use_fast=False)
model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()


def normalize_text(text: str) -> str:
    """Normalize text tiếng Việt."""
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = " ".join(text.split())
    return text


def predict(text: str) -> dict:
    """Predict depression cho một text.

    Args:
        text: Text tiếng Việt cần phân loại

    Returns:
        Dict với prediction và confidence
    """
    prepared = normalize_text(text)
    inputs = tokenizer(
        prepared,
        return_tensors="pt",
        truncation=True,
        max_length=128,
    )
    inputs = {{k: v.to(device) for k, v in inputs.items()}}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        pred = torch.argmax(probs, dim=-1).item()
        confidence = probs[0][pred].item()

    return {{
        "prediction": "depression" if pred == 1 else "normal",
        "label": pred,
        "confidence": confidence,
        "probabilities": {{
            "normal": probs[0][0].item(),
            "depression": probs[0][1].item(),
        }},
    }}


if __name__ == "__main__":
    import sys

    test_texts = [
        "Tôi cảm thấy rất vui hôm nay!",
        "Cuộc sống này thật vô nghĩa...",
        "Không biết làm gì, chán quá.",
    ]

    if len(sys.argv) > 1:
        # Test từ command line
        text = " ".join(sys.argv[1:])
        result = predict(text)
        print(f"Text: {{text}}")
        print(f"Prediction: {{result['prediction']}}")
        print(f"Confidence: {{result['confidence']:.2%}}")
    else:
        # Test với sample texts
        print("Testing model: {model_name}")
        print("=" * 50)
        for text in test_texts:
            result = predict(text)
            print(f"\\nText: {{text}}")
            print(f"  Prediction: {{result['prediction']}}")
            print(f"  Confidence: {{result['confidence']:.2%}}")
'''

    script_path = PROJECT_ROOT / "scripts" / f"inference_{model_name}.py"
    script_path.write_text(script_content)
    print(f"Inference script created: {script_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Colab Helper - Kết nối model từ Google Colab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:

  # Download từ Hugging Face
  python colab_helper.py download-hf --model-id username/phobert-depression-v1

  # Download từ Google Drive path
  python colab_helper.py download-gdrive --drive-path /content/drive/MyDrive/phobert/

  # Upload model local lên Hugging Face
  python colab_helper.py upload-hf --local-path ./models/my_model --repo-id username/my-model

  # Import model vào project
  python colab_helper.py import-model --model-path ./downloaded_model

  # Tạo inference script
  python colab_helper.py create-inference --model-name phobert_colab
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Download from HuggingFace
    dl_hf = subparsers.add_parser("download-hf", help="Download model từ Hugging Face")
    dl_hf.add_argument("--model-id", required=True, help="Model ID trên Hugging Face (VD: username/model-name)")
    dl_hf.add_argument("--output", default="models/phobert_colab", help="Output directory")

    # Download from Google Drive
    dl_gd = subparsers.add_parser("download-gdrive", help="Download model từ Google Drive")
    dl_gd.add_argument("--drive-path", required=True, help="Đường dẫn trên Google Drive")
    dl_gd.add_argument("--output", default="models/phobert_colab", help="Output directory")

    # Upload to HuggingFace
    up_hf = subparsers.add_parser("upload-hf", help="Upload model lên Hugging Face")
    up_hf.add_argument("--local-path", required=True, help="Đường dẫn model local")
    up_hf.add_argument("--repo-id", required=True, help="Repository ID (VD: username/model-name)")

    # Import to project
    imp = subparsers.add_parser("import-model", help="Import model vào project")
    imp.add_argument("--model-path", required=True, help="Đường dẫn model đã download")
    imp.add_argument("--name", default="phobert_colab", help="Tên model trong project")

    # Create inference script
    inf = subparsers.add_parser("create-inference", help="Tạo inference script")
    inf.add_argument("--model-name", required=True, help="Tên model")

    args = parser.parse_args()

    if args.command == "download-hf":
        download_from_huggingface(args.model_id, args.output)
    elif args.command == "download-gdrive":
        download_from_gdrive(args.drive_path, args.output)
    elif args.command == "upload-hf":
        upload_to_huggingface(args.local_path, args.repo_id)
    elif args.command == "import-model":
        import_to_project(args.model_path, args.name)
    elif args.command == "create-inference":
        create_inference_script(args.model_name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
