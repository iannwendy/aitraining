"""Flask dashboard cho YouTube crawler."""

from __future__ import annotations

import logging

from flask import Flask, jsonify, render_template_string

from yt_depression_crawler.core.config import LOG_FILE, ensure_directories
from yt_depression_crawler.web.web_manager import CrawlManager

app = Flask(__name__)
manager = CrawlManager()


def setup_logging() -> None:
    ensure_directories()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


setup_logging()


@app.get("/")
def index():
    return render_template_string(DASHBOARD_HTML)


@app.get("/api/status")
def api_status():
    return jsonify(manager.status())


@app.post("/api/start")
def api_start():
    ok, message = manager.start()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409


@app.post("/api/stop")
def api_stop():
    ok, message = manager.stop()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/label/auto")
def api_label_auto():
    ok, message = manager.run_auto_label()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/label/train")
def api_label_train():
    ok, message = manager.build_initial_train()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/label/pipeline")
def api_label_pipeline():
    ok, message = manager.run_labeling_pipeline()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/ml/review")
def api_ml_review():
    ok, message = manager.create_review_set()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/ml/split")
def api_ml_split():
    ok, message = manager.create_train_splits()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/ml/baseline")
def api_ml_baseline():
    ok, message = manager.train_baseline()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/ml/pipeline")
def api_ml_pipeline():
    ok, message = manager.run_training_pipeline()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/gold/build")
def api_gold_build():
    ok, message = manager.build_gold_review()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/gold/eval-weak")
def api_gold_eval_weak():
    ok, message = manager.evaluate_weak_on_gold()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/gold/eval-baseline")
def api_gold_eval_baseline():
    ok, message = manager.evaluate_baseline_gold()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/gold/pipeline")
def api_gold_pipeline():
    ok, message = manager.run_gold_review_pipeline()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/phobert/train")
def api_phobert_train():
    ok, message = manager.train_phobert()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/phobert/predict")
def api_phobert_predict():
    ok, message = manager.predict_phobert_remaining()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/phobert/postprocess")
def api_phobert_postprocess():
    ok, message = manager.postprocess_phobert_predictions()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409

@app.post("/api/phobert/pipeline")
def api_phobert_pipeline():
    ok, message = manager.run_phobert_first_pipeline()
    return jsonify({"ok": ok, "message": message, "status": manager.status()}), 200 if ok else 409


DASHBOARD_HTML = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube Comment Crawler</title>
  <style>
    :root { color-scheme: light; --bg:#f6f7f9; --panel:#fff; --text:#17202a; --muted:#667085; --line:#d9dee7; --green:#147a4a; --red:#b42318; --blue:#175cd3; --amber:#b54708; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:var(--bg); color:var(--text); }
    header { padding:22px 28px; border-bottom:1px solid var(--line); background:var(--panel); display:flex; justify-content:space-between; gap:16px; align-items:center; }
    h1 { margin:0; font-size:22px; font-weight:700; letter-spacing:0; }
    main { padding:24px 28px 32px; max-width:1200px; margin:0 auto; }
    .actions { display:flex; gap:10px; flex-wrap:wrap; }
    button { border:1px solid var(--line); background:#fff; min-height:40px; padding:0 15px; border-radius:7px; font-size:14px; font-weight:650; cursor:pointer; }
    button:disabled { opacity:.55; cursor:not-allowed; }
    .start { background:var(--green); border-color:var(--green); color:#fff; }
    .stop { background:var(--red); border-color:var(--red); color:#fff; }
    .secondary { background:var(--blue); border-color:var(--blue); color:#fff; }
    .grid { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:14px; margin-bottom:18px; }
    .card { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; min-height:104px; }
    .label { color:var(--muted); font-size:13px; margin-bottom:10px; }
    .value { font-size:28px; font-weight:750; line-height:1.1; overflow-wrap:anywhere; }
    .small { font-size:14px; color:var(--muted); margin-top:8px; overflow-wrap:anywhere; }
    .wide { grid-column: span 2; }
    .progress { height:12px; background:#e8edf4; border-radius:999px; overflow:hidden; margin-top:12px; }
    .bar { height:100%; width:0%; background:var(--blue); transition:width .25s ease; }
    .status { display:inline-flex; align-items:center; min-height:30px; padding:0 10px; border-radius:999px; border:1px solid var(--line); background:#fff; font-size:13px; font-weight:700; }
    .status.running { color:var(--blue); border-color:#b2ccff; background:#eff4ff; }
    .status.completed { color:var(--green); border-color:#abefc6; background:#ecfdf3; }
    .status.stopping, .status.quota_exceeded { color:var(--amber); border-color:#fedf89; background:#fffaeb; }
    .status.error, .status.missing_api_key { color:var(--red); border-color:#fecdca; background:#fef3f2; }
    .section { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; margin-top:14px; }
    .section h2 { margin:0 0 12px; font-size:16px; }
    pre { margin:0; white-space:pre-wrap; word-break:break-word; max-height:360px; overflow:auto; font-size:12px; line-height:1.45; color:#344054; background:#f8fafc; border:1px solid var(--line); border-radius:7px; padding:12px; }
    @media (max-width: 900px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .wide { grid-column: span 2; } header { align-items:flex-start; flex-direction:column; } }
    @media (max-width: 560px) { main, header { padding-left:16px; padding-right:16px; } .grid { grid-template-columns: 1fr; } .wide { grid-column: span 1; } .value { font-size:24px; } }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>YouTube Depression Comment Crawler</h1>
      <div class="small">Dashboard theo dõi crawl comment công khai bằng YouTube Data API v3</div>
    </div>
    <div class="actions">
      <button id="startBtn" class="start" onclick="startCrawl()">Start</button>
      <button id="stopBtn" class="stop" onclick="stopCrawl()">Stop</button>
      <button id="labelPipelineBtn" class="secondary" onclick="runLabelPipeline()">Label Pipeline</button>
      <button id="autoLabelBtn" onclick="runAutoLabel()">Auto Label</button>
      <button id="buildTrainBtn" onclick="buildTrain()">Build Train</button>
      <button id="mlPipelineBtn" class="secondary" onclick="runMlPipeline()">ML Pipeline</button>
      <button id="reviewBtn" onclick="createReview()">Review Set</button>
      <button id="splitBtn" onclick="createSplits()">Split</button>
      <button id="baselineBtn" onclick="trainBaseline()">Baseline</button>
      <button id="goldPipelineBtn" class="secondary" onclick="runGoldPipeline()">Gold Pipeline</button>
      <button id="goldBuildBtn" onclick="buildGold()">Build Gold</button>
      <button id="goldWeakBtn" onclick="evalGoldWeak()">Eval Weak</button>
      <button id="goldBaselineBtn" onclick="evalGoldBaseline()">Eval Gold Baseline</button>
      <button id="phobertPipelineBtn" class="secondary" onclick="runPhoBertPipeline()">PhoBERT Pipeline</button>
      <button id="phobertTrainBtn" onclick="trainPhoBert()">Train PhoBERT</button>
      <button id="phobertPredictBtn" onclick="predictPhoBert()">Predict Remaining</button>
      <button id="phobertPostprocessBtn" onclick="postprocessPhoBert()">PhoBERT Postprocess</button>
    </div>
  </header>
  <main>
    <div class="grid">
      <div class="card">
        <div class="label">API state</div>
        <div id="apiState" class="status">loading</div>
        <div id="lastError" class="small"></div>
      </div>
      <div class="card">
        <div class="label">Raw comments</div>
        <div id="rawComments" class="value">0</div>
        <div id="target" class="small"></div>
      </div>
      <div class="card">
        <div class="label">Cleaned comments</div>
        <div id="cleanedComments" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">Auto-labeled</div>
        <div id="autoLabeledComments" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">Initial train</div>
        <div id="initialTrainRows" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">Review samples</div>
        <div id="reviewSamples" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">Processed videos</div>
        <div id="processedVideos" class="value">0</div>
      </div>
      <div class="card wide">
        <div class="label">Progress to target</div>
        <div id="progressText" class="value">0%</div>
        <div class="progress"><div id="progressBar" class="bar"></div></div>
      </div>
      <div class="card wide">
        <div class="label">Current work</div>
        <div id="currentKeyword" class="value">-</div>
        <div id="currentVideo" class="small">-</div>
      </div>
      <div class="card">
        <div class="label">Videos found this run</div>
        <div id="videosFound" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">Videos crawled this run</div>
        <div id="videosCrawled" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">Skipped this run</div>
        <div id="videosSkipped" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">New raw this run</div>
        <div id="newRaw" class="value">0</div>
      </div>
      <div class="card wide">
        <div class="label">Labeling state</div>
        <div id="labelingState" class="status">idle</div>
        <div id="labelingDetail" class="small">-</div>
      </div>
      <div class="card wide">
        <div class="label">Weak-label counts</div>
        <div id="labelCounts" class="value">-</div>
        <div id="trainCounts" class="small">-</div>
      </div>
      <div class="card wide">
        <div class="label">ML state</div>
        <div id="mlState" class="status">idle</div>
        <div id="mlDetail" class="small">-</div>
      </div>
      <div class="card wide">
        <div class="label">Train / Val / Test</div>
        <div id="splitCounts" class="value">-</div>
        <div id="splitDetail" class="small">-</div>
      </div>
      <div class="card wide">
        <div class="label">Baseline test metrics</div>
        <div id="baselineMetrics" class="value">-</div>
        <div id="baselineDetail" class="small">-</div>
      </div>
      <div class="card">
        <div class="label">Gold review</div>
        <div id="goldReviewRows" class="value">0</div>
      </div>
      <div class="card wide">
        <div class="label">Gold eval</div>
        <div id="goldMetrics" class="value">-</div>
        <div id="goldDetail" class="small">-</div>
      </div>
      <div class="card wide">
        <div class="label">PhoBERT state</div>
        <div id="phobertState" class="status">idle</div>
        <div id="phobertDetail" class="small">-</div>
      </div>
      <div class="card wide">
        <div class="label">PhoBERT metrics</div>
        <div id="phobertMetrics" class="value">-</div>
        <div id="phobertMetricsDetail" class="small">-</div>
      </div>
      <div class="card">
        <div class="label">PhoBERT predictions</div>
        <div id="phobertPredictions" class="value">0</div>
        <div id="phobertPredictionDetail" class="small">-</div>
      </div>
    </div>
    <div class="section">
      <h2>Log gần nhất</h2>
      <pre id="logTail"></pre>
    </div>
  </main>
  <script>
    const fmt = new Intl.NumberFormat('vi-VN');
    async function postJson(url) {
      const res = await fetch(url, {method: 'POST'});
      const data = await res.json();
      if (!res.ok) alert(data.message || 'Request failed');
      update(data.status || data);
    }
    function startCrawl() { postJson('/api/start'); }
    function stopCrawl() { postJson('/api/stop'); }
    function runAutoLabel() { postJson('/api/label/auto'); }
    function buildTrain() { postJson('/api/label/train'); }
    function runLabelPipeline() { postJson('/api/label/pipeline'); }
    function createReview() { postJson('/api/ml/review'); }
    function createSplits() { postJson('/api/ml/split'); }
    function trainBaseline() { postJson('/api/ml/baseline'); }
    function runMlPipeline() { postJson('/api/ml/pipeline'); }
    function buildGold() { postJson('/api/gold/build'); }
    function evalGoldWeak() { postJson('/api/gold/eval-weak'); }
    function evalGoldBaseline() { postJson('/api/gold/eval-baseline'); }
    function runGoldPipeline() { postJson('/api/gold/pipeline'); }
    function trainPhoBert() { postJson('/api/phobert/train'); }
    function predictPhoBert() { postJson('/api/phobert/predict'); }
    function postprocessPhoBert() { postJson('/api/phobert/postprocess'); }
    function runPhoBertPipeline() { postJson('/api/phobert/pipeline'); }
    async function refresh() {
      const res = await fetch('/api/status');
      update(await res.json());
    }
    function update(s) {
      const state = s.api_state || 'unknown';
      const running = Boolean(s.running);
      const labelingRunning = Boolean(s.labeling_running);
      const mlRunning = Boolean(s.ml_running);
      const phobertRunning = Boolean(s.phobert_running);
      document.getElementById('startBtn').disabled = running || labelingRunning || mlRunning || phobertRunning;
      document.getElementById('stopBtn').disabled = !running;
      const busy = running || labelingRunning || mlRunning || phobertRunning;
      document.getElementById('labelPipelineBtn').disabled = busy;
      document.getElementById('autoLabelBtn').disabled = busy;
      document.getElementById('buildTrainBtn').disabled = busy;
      document.getElementById('mlPipelineBtn').disabled = busy;
      document.getElementById('reviewBtn').disabled = busy;
      document.getElementById('splitBtn').disabled = busy;
      document.getElementById('baselineBtn').disabled = busy;
      document.getElementById('goldPipelineBtn').disabled = busy;
      document.getElementById('goldBuildBtn').disabled = busy;
      document.getElementById('goldWeakBtn').disabled = busy;
      document.getElementById('goldBaselineBtn').disabled = busy;
      document.getElementById('phobertPipelineBtn').disabled = busy;
      document.getElementById('phobertTrainBtn').disabled = busy;
      document.getElementById('phobertPredictBtn').disabled = busy;
      document.getElementById('phobertPostprocessBtn').disabled = busy;
      const api = document.getElementById('apiState');
      api.textContent = state;
      api.className = 'status ' + state;
      document.getElementById('lastError').textContent = s.last_error ? 'Last error: ' + s.last_error : '';
      document.getElementById('rawComments').textContent = fmt.format(s.raw_comments || 0);
      document.getElementById('cleanedComments').textContent = fmt.format(s.cleaned_comments || 0);
      document.getElementById('autoLabeledComments').textContent = fmt.format(s.auto_labeled_comments || 0);
      document.getElementById('initialTrainRows').textContent = fmt.format(s.initial_train_rows || 0);
      document.getElementById('reviewSamples').textContent = fmt.format(s.review_samples || 0);
      document.getElementById('goldReviewRows').textContent = fmt.format(s.gold_review_rows || 0);
      document.getElementById('phobertPredictions').textContent = fmt.format(s.phobert_prediction_rows || 0);
      document.getElementById('phobertPredictionDetail').textContent = `Confident ${fmt.format(s.phobert_confident_rows || 0)} / Active ${fmt.format(s.phobert_active_learning_rows || 0)}`;
      document.getElementById('processedVideos').textContent = fmt.format(s.processed_videos || 0);
      document.getElementById('target').textContent = s.target_raw_comments ? 'Target: ' + fmt.format(s.target_raw_comments) : 'No target';
      const pct = s.progress_percent == null ? 0 : s.progress_percent;
      document.getElementById('progressText').textContent = pct + '%';
      document.getElementById('progressBar').style.width = pct + '%';
      document.getElementById('currentKeyword').textContent = s.current_keyword || '-';
      document.getElementById('currentVideo').textContent = s.current_video_id ? `${s.current_video_id} - ${s.current_video_title || ''}` : '-';
      document.getElementById('videosFound').textContent = fmt.format(s.total_videos_found || 0);
      document.getElementById('videosCrawled').textContent = fmt.format(s.total_videos_crawled || 0);
      document.getElementById('videosSkipped').textContent = fmt.format(s.total_videos_skipped || 0);
      document.getElementById('newRaw').textContent = fmt.format(s.total_raw_comments_saved || 0);
      const labelState = document.getElementById('labelingState');
      labelState.textContent = s.labeling_state || 'idle';
      labelState.className = 'status ' + (s.labeling_state || 'idle');
      document.getElementById('labelingDetail').textContent = s.labeling_last_error ? 'Error: ' + s.labeling_last_error : (s.labeling_task || '-');
      const report = s.labeling_report || {};
      const auto = report.auto_labeling || {};
      const counts = auto.label_counts || {};
      document.getElementById('labelCounts').textContent = `D ${fmt.format(counts.depression_auto || 0)} / N ${fmt.format(counts.normal_auto || 0)} / U ${fmt.format(counts.uncertain || 0)}`;
      const train = report.initial_train || {};
      document.getElementById('trainCounts').textContent = `Train D ${fmt.format(train.selected_depression || 0)} / N ${fmt.format(train.selected_normal || 0)}`;
      const mlState = document.getElementById('mlState');
      mlState.textContent = s.ml_state || 'idle';
      mlState.className = 'status ' + (s.ml_state || 'idle');
      document.getElementById('mlDetail').textContent = s.ml_last_error ? 'Error: ' + s.ml_last_error : (s.ml_task || '-');
      document.getElementById('splitCounts').textContent = `${fmt.format(s.train_rows || 0)} / ${fmt.format(s.val_rows || 0)} / ${fmt.format(s.test_rows || 0)}`;
      const splits = report.splits || {};
      document.getElementById('splitDetail').textContent = splits.total_rows ? `Total trainable: ${fmt.format(splits.total_rows)}` : '-';
      const metrics = s.baseline_metrics || {};
      const test = metrics.test || {};
      if (test.f1_macro != null) {
        document.getElementById('baselineMetrics').textContent = `F1 ${test.f1_macro} / Acc ${test.accuracy}`;
        document.getElementById('baselineDetail').textContent = `Depression F1 ${test.f1_depression}; rows ${fmt.format(metrics.train_rows || 0)}/${fmt.format(metrics.val_rows || 0)}/${fmt.format(metrics.test_rows || 0)}`;
      } else {
        document.getElementById('baselineMetrics').textContent = '-';
        document.getElementById('baselineDetail').textContent = '-';
      }
      const goldMetrics = s.baseline_gold_metrics || {};
      if (goldMetrics.f1_macro != null) {
        document.getElementById('goldMetrics').textContent = `F1 ${goldMetrics.f1_macro} / Acc ${goldMetrics.accuracy}`;
        document.getElementById('goldDetail').textContent = `Depression F1 ${goldMetrics.f1_depression}; gold rows ${fmt.format(goldMetrics.gold_rows || 0)}`;
      } else if ((s.labeling_report || {}).gold_review) {
        const gold = s.labeling_report.gold_review;
        document.getElementById('goldMetrics').textContent = `Gold ${fmt.format(gold.gold_rows || 0)}`;
        document.getElementById('goldDetail').textContent = `Excluded ${fmt.format(gold.excluded_from_gold || 0)}`;
      } else {
        document.getElementById('goldMetrics').textContent = '-';
        document.getElementById('goldDetail').textContent = '-';
      }
      const phobertState = document.getElementById('phobertState');
      phobertState.textContent = s.phobert_state || 'idle';
      phobertState.className = 'status ' + (s.phobert_state || 'idle');
      document.getElementById('phobertDetail').textContent = s.phobert_last_error ? 'Error: ' + s.phobert_last_error : (s.phobert_task || '-');
      const phobertMetrics = s.phobert_metrics || {};
      const phobertTest = phobertMetrics.test || {};
      if (phobertTest.f1_macro != null) {
        document.getElementById('phobertMetrics').textContent = `F1 ${phobertTest.f1_macro} / Acc ${phobertTest.accuracy}`;
        const phobertGold = phobertMetrics.gold || {};
        const goldText = phobertGold.f1_macro != null ? `; Gold F1 ${phobertGold.f1_macro}` : '';
        document.getElementById('phobertMetricsDetail').textContent = `Depression F1 ${phobertTest.f1_depression}; epoch ${phobertMetrics.best_epoch || '-'}${goldText}`;
      } else {
        document.getElementById('phobertMetrics').textContent = '-';
        document.getElementById('phobertMetricsDetail').textContent = '-';
      }
      document.getElementById('logTail').textContent = (s.log_tail || []).join('');
    }
    refresh();
    setInterval(refresh, 3000);
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
