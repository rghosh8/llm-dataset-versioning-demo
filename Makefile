# ----------------------
#   Virtualenv & deps
# ----------------------

PYTHON := python3
VENV_DIR := venv

DATASET_NAME := demo-wikitext
BASE_VERSION_DIR := data/versions/$(DATASET_NAME)

.PHONY: venv
venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "Virtualenv created in $(VENV_DIR)"; \
	else \
		echo "Virtualenv already exists in $(VENV_DIR)"; \
	fi

.PHONY: install
install: venv
	@. $(VENV_DIR)/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

# ----------------------
#   Build dataset versions
# ----------------------

.PHONY: v1
v1:
	@. $(VENV_DIR)/bin/activate && \
	$(PYTHON) scripts/build_dataset.py --config configs/dataset-v1.0.yaml

.PHONY: v1.1
v1.1:
	@. $(VENV_DIR)/bin/activate && \
	$(PYTHON) scripts/build_dataset.py --config configs/dataset-v1.1.yaml

.PHONY: all
all: v1 v1.1

# ----------------------
#   Inspect versions
# ----------------------

.PHONY: inspect-v1
inspect-v1:
	@. $(VENV_DIR)/bin/activate && \
	$(PYTHON) scripts/inspect_version.py \
		--base_dir $(BASE_VERSION_DIR) \
		--version v1.0.0

.PHONY: inspect-v1.1
inspect-v1.1:
	@. $(VENV_DIR)/bin/activate && \
	$(PYTHON) scripts/inspect_version.py \
		--base_dir $(BASE_VERSION_DIR) \
		--version v1.1.0

# ----------------------
#   Cleanup
# ----------------------

.PHONY: clean-versions
clean-versions:
	@echo "Removing all dataset versions under $(BASE_VERSION_DIR)..."
	@rm -rf $(BASE_VERSION_DIR)

.PHONY: clean
clean: clean-versions

# ----------------------
#   OPTIONAL: Git tag / HF / DVC
#   (You must configure these yourself before using.)
# ----------------------

# Example: tag the code for v1.0.0
.PHONY: tag-v1.0.0
tag-v1.0.0:
	git tag -a data-$(DATASET_NAME)-v1.0.0 -m "Dataset $(DATASET_NAME) v1.0.0 built"
	git push origin data-$(DATASET_NAME)-v1.0.0

# Example: push v1.0.0 to HuggingFace Datasets (requires huggingface-cli login)
HF_DATASET_ID := your-username/$(DATASET_NAME)

.PHONY: hf-push-v1.0.0
hf-push-v1.0.0:
	huggingface-cli upload \
		data/versions/$(DATASET_NAME)/v1.0.0 \
		$(HF_DATASET_ID) \
		--repo-type dataset \
		--revision v1.0.0

# Example: DVC tracking (requires `dvc init` and remote setup)
.PHONY: dvc-add-v1.0.0
dvc-add-v1.0.0:
	dvc add data/versions/$(DATASET_NAME)/v1.0.0
	git add data/versions/$(DATASET_NAME)/v1.0.0.dvc
	git commit -m "Track $(DATASET_NAME) v1.0.0 with DVC"

.PHONY: dvc-push
dvc-push:
	dvc push
