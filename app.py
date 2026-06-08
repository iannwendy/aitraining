"""Root entrypoint cho Flask dashboard.

Logic dashboard nằm trong package `yt_depression_crawler.web`.
Giữ file này để Docker/Gunicorn và thói quen chạy `python app.py` vẫn hoạt động.
"""

from yt_depression_crawler.web.app import app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
