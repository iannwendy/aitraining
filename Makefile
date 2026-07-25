PYTHON ?= .venv/bin/python
PYTHONPATH := $(CURDIR)
export PYTHONPATH

.PHONY: dataset augment translate-en-vi test classical-clean classical-augmented \
	classical-translated classical-augmented-translated \
	phobert-clean phobert-augmented bilstm-clean bilstm-augmented \
	phobert-translated phobert-augmented-translated \
	topic-clean topic-augmented dapt phobert-clean-export ensemble-tune \
	ensemble-evaluate aggregate

dataset:
	$(PYTHON) scripts/merge_round5_reviewed.py

augment:
	TQDM_DISABLE=1 $(PYTHON) scripts/data_augmentation.py --input data/labeled/final_train.csv --output data/augmented_v2/generated_depression_train.csv --depression-only --n-augment 3
	$(PYTHON) scripts/merge_augmented.py

translate-en-vi:
	$(PYTHON) scripts/build_translated_english_train.py

test:
	$(PYTHON) -m pytest -q

classical-clean:
	$(PYTHON) scripts/train_evaluate_classical.py --tag clean

classical-augmented:
	$(PYTHON) scripts/train_evaluate_classical.py --train-file data/augmented_v2/final_train_augmented.csv --tag augmented

classical-translated:
	$(PYTHON) scripts/train_evaluate_classical.py --train-file data/translated_en_vi/final_train_translated_en_vi.csv --tag translated --splits validation

classical-augmented-translated:
	$(PYTHON) scripts/train_evaluate_classical.py --train-file data/translated_en_vi/final_train_augmented_translated_en_vi.csv --tag augmented_translated --splits validation

phobert-clean:
	$(PYTHON) scripts/train_phobert_round5_multiseed.py --seeds 42 123 2024 --result-name phobert_results_clean.json --output-dir models/round5_predictions_clean

phobert-augmented:
	$(PYTHON) scripts/train_phobert_round5_multiseed.py --train-file data/augmented_v2/final_train_augmented.csv --seeds 42 123 2024 --result-name phobert_results_augmented.json --output-dir models/round5_predictions_augmented

phobert-translated:
	$(PYTHON) scripts/train_phobert_round5_multiseed.py --train-file data/translated_en_vi/final_train_translated_en_vi.csv --seeds 42 123 2024 --result-name phobert_results_translated.json --output-dir models/round5_predictions_translated --evaluation-splits validation

phobert-augmented-translated:
	$(PYTHON) scripts/train_phobert_round5_multiseed.py --train-file data/translated_en_vi/final_train_augmented_translated_en_vi.csv --seeds 42 123 2024 --result-name phobert_results_augmented_translated.json --output-dir models/round5_predictions_augmented_translated --evaluation-splits validation

phobert-clean-export:
	$(PYTHON) scripts/export_phobert_predictions.py --model-root models/round5_predictions_clean --tag clean --seeds 42 123 2024 --splits validation

bilstm-clean:
	$(PYTHON) scripts/run_bilstm_multiseed.py --seeds 42 123 2024 --variants random phobert --tag clean

bilstm-augmented:
	$(PYTHON) scripts/run_bilstm_multiseed.py --seeds 42 123 2024 --variants random phobert --train-file data/augmented_v2/final_train_augmented.csv --tag augmented

topic-clean:
	$(PYTHON) scripts/rerun_phobert_bertopic.py --train-file data/labeled/final_train.csv --phobert-dir models/round5_predictions_clean/seed_42/best_model --tag clean

topic-augmented:
	$(PYTHON) scripts/rerun_phobert_bertopic.py --train-file data/augmented_v2/final_train_augmented.csv --phobert-dir models/round5_predictions_augmented/seed_42/best_model --tag augmented

dapt:
	$(PYTHON) -m scripts.evaluate_domain_adapted_phobert --models models/phobert_base_local models/phobert_domain_adapted --seeds 42 123 2024 --output-dir results/reproducible_round5/dapt

ensemble-tune:
	$(PYTHON) scripts/select_validation_ensemble.py tune

ensemble-evaluate:
	$(PYTHON) scripts/select_validation_ensemble.py evaluate

aggregate:
	$(PYTHON) scripts/aggregate_reproducible_results.py
