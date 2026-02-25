# CLAUDE.md — DeepSeek-V3 Repository Guide

This file provides AI assistants with a comprehensive map of the codebase, development workflows, and conventions for the DeepSeek-V3 repository.

---

## Repository Overview

DeepSeek-V3 is a **671B parameter Mixture-of-Experts (MoE) large language model** with 37B activated parameters per token. This repository contains:

1. A **reference inference implementation** (`inference/`) in PyTorch + Triton
2. **Model checkpoint tools** for converting and sharding weights
3. A **demo web application** for Vietnamese room/hostel management (`demo/`)
4. **Documentation** in English (`README.md`, `README_WEIGHTS.md`) and Vietnamese (`APP_QUAN_LY_PHONG_TRO.md`)

The inference code is the authoritative implementation; actual training code is not included. The repository is primarily used for deployment and as a reference architecture.

---

## Directory Structure

```
DeepSeek-V3/
├── inference/                  # Core Python inference implementation
│   ├── model.py                # Transformer architecture (MLA, MoE, etc.)
│   ├── generate.py             # Text generation + CLI entry point
│   ├── convert.py              # HuggingFace → sharded safetensors converter
│   ├── fp8_cast_bf16.py        # FP8 → BF16 weight format converter
│   ├── kernel.py               # Triton GPU kernels (quantization, FP8 GEMM)
│   ├── requirements.txt        # Pinned Python dependencies
│   └── configs/
│       ├── config_16B.json     # 16B model configuration
│       ├── config_236B.json    # 236B model configuration (DeepSeek-V2 size)
│       └── config_671B.json    # Full 671B production model configuration
├── scripts/
│   └── run_quan_ly_phong_tro_demo.sh  # Starts HTTP server for demo UI
├── demo/
│   └── quan-ly-phong-tro-ui.html      # Single-file Vietnamese room management UI
├── figures/                    # PNG images referenced in README.md
├── .github/
│   ├── workflows/stale.yml     # Auto-close stale GitHub issues
│   └── ISSUE_TEMPLATE/         # Bug report + feature request templates
├── README.md                   # Main documentation with benchmarks and deployment guides
├── README_WEIGHTS.md           # FP8 weight format and MTP module documentation
├── APP_QUAN_LY_PHONG_TRO.md   # Vietnamese app spec (unrelated to the LLM)
├── LICENSE-CODE                # MIT License (code)
└── LICENSE-MODEL               # DeepSeek Model Agreement (model weights)
```

---

## Core Architecture (`inference/model.py`)

The model is a standard decoder-only transformer with two major innovations: **Multi-Head Latent Attention (MLA)** and **DeepSeekMoE**.

### Key Classes

| Class | Purpose |
|-------|---------|
| `ModelArgs` | Dataclass of all model hyperparameters; read from JSON config |
| `Transformer` | Top-level model: embedding → 61 `Block` layers → RMSNorm → head |
| `Block` | One transformer layer: `MLA` attention + (`MLP` or `MoE`) FFN |
| `MLA` | Multi-Head Latent Attention — uses LoRA on Q/KV to compress KV cache |
| `MoE` | Mixture-of-Experts module with a `Gate` routing to `Expert` layers |
| `Gate` | Top-K expert selection with optional sigmoid/softmax scoring |
| `Expert` | Single expert MLP: w1/w2/w3 with SiLU gating |
| `MLP` | Dense feed-forward block for early non-MoE layers |
| `Linear` | Custom linear layer supporting BF16 and FP8 (e4m3fn) weight dtypes |
| `ColumnParallelLinear` | Splits output features across `world_size` GPUs |
| `RowParallelLinear` | Splits input features across `world_size` GPUs; all-reduces output |
| `ParallelEmbedding` | Vocabulary-parallel embedding; all-reduces activations |
| `RMSNorm` | Root Mean Square Layer Normalization |

### Architecture Detail (671B)

- **Layers**: 61 total — first 3 are dense (`MLP`), layers 3–60 use `MoE`
- **Experts**: 256 routed + 1 shared expert per MoE layer; 8 experts activated per token
- **Attention**: MLA with `q_lora_rank=1536`, `kv_lora_rank=512`; two KV cache modes:
  - `"absorb"` (default, production): stores compressed `kv_cache` + `pe_cache`
  - `"naive"`: stores full expanded `k_cache` + `v_cache`
- **Positional encoding**: YaRN-extended RoPE (supports up to 128K context)
- **Precision**: Native FP8 (`torch.float8_e4m3fn`), with BF16 fallback via `gemm_impl`

### Global State in `model.py`

Three module-level globals are set at `Transformer.__init__` time:

```python
world_size = 1   # set from dist.get_world_size()
rank = 0         # set from dist.get_rank()
gemm_impl = "bf16"  # or "fp8" — controls Linear.forward dispatch
attn_impl = "absorb"  # or "naive" — controls MLA cache layout
block_size = 128    # FP8 quantization block size (do not change)
```

---

## Triton Kernels (`inference/kernel.py`)

Three GPU operations implemented in Triton:

| Function | Description |
|----------|-------------|
| `act_quant(x, block_size=128)` | Quantize activation tensor to FP8 e4m3fn; returns `(y, scale)` |
| `weight_dequant(x, s, block_size=128)` | Dequantize FP8 weight matrix using 128×128 block scale factors |
| `fp8_gemm(a, a_s, b, b_s)` | FP8 matrix multiply with per-block scaling; autotuned via `@triton.autotune` |

These are called inside `model.linear()` depending on `gemm_impl`.

---

## Checkpoint and Weight Tools

### `inference/convert.py` — HuggingFace → Distributed Format

Converts HuggingFace `.safetensors` checkpoints to sharded files suitable for multi-GPU inference. Handles:
- **Tensor parallelism**: splits weight tensors along the column (`dim=0`) or row (`dim=1`) dimension
- **Expert sharding**: distributes expert weights across ranks
- Remaps HuggingFace parameter names to the internal `model.py` names

```bash
cd inference
python convert.py \
  --hf-ckpt-path /path/to/DeepSeek-V3-HF \
  --save-path /path/to/DeepSeek-V3-Demo \
  --n-experts 256 \
  --model-parallel 16   # must divide n-experts evenly
```

Output: `model{i}-mp{mp}.safetensors` for i in 0..mp-1, plus tokenizer files.

### `inference/fp8_cast_bf16.py` — FP8 → BF16 Conversion

The released weights are in FP8 format. For hardware that does not support FP8, convert to BF16:

```bash
cd inference
python fp8_cast_bf16.py \
  --input-fp8-hf-path  /path/to/fp8_weights \
  --output-bf16-hf-path /path/to/bf16_weights
```

Reads `model.safetensors.index.json`, processes each shard, removes `_scale_inv` tensors, and writes a new index file.

---

## Running Inference (`inference/generate.py`)

### Interactive Chat (multi-node example)

```bash
torchrun \
  --nnodes 2 --nproc-per-node 8 \
  --node-rank $RANK --master-addr $ADDR \
  generate.py \
  --ckpt-path /path/to/DeepSeek-V3-Demo \
  --config configs/config_671B.json \
  --interactive \
  --temperature 0.7 \
  --max-new-tokens 200
```

Special interactive commands: `/exit` to quit, `/clear` to reset conversation history.

### Batch Inference

```bash
torchrun ... generate.py \
  --ckpt-path /path/to/model \
  --config configs/config_671B.json \
  --input-file prompts.txt \
  --max-new-tokens 512
```

### Single-GPU / Development

```bash
cd inference
python generate.py \
  --ckpt-path /path/to/model \
  --config configs/config_16B.json \
  --interactive
```

---

## Model Configurations

### Config Parameters Reference

| Parameter | 16B | 236B | 671B | Description |
|-----------|-----|------|------|-------------|
| `vocab_size` | 102400 | 102400 | 129280 | Vocabulary size |
| `dim` | 2048 | 5120 | 7168 | Hidden dimension |
| `n_layers` | 27 | 61 | 61 | Transformer block count |
| `n_dense_layers` | 1 | 1 | 3 | Non-MoE prefix layers |
| `n_heads` | 16 | 128 | 128 | Attention heads |
| `n_routed_experts` | 64 | 160 | 256 | Total routed experts |
| `n_activated_experts` | 6 | 6 | 8 | Experts per token |
| `q_lora_rank` | 0 | 1536 | 1536 | 0 = no LoRA on Q |
| `kv_lora_rank` | 512 | 512 | 512 | KV compression rank |
| `dtype` | (bf16 default) | — | `"fp8"` | Weight dtype |

---

## Dependencies and Environment

**Pinned versions** (from `inference/requirements.txt`):

```
torch==2.4.1
triton==3.0.0
transformers==4.46.3
safetensors==0.4.5
```

**System requirements**:
- Linux, Python 3.10+ (macOS/Windows not officially supported)
- CUDA-capable NVIDIA GPU (required for Triton kernels and FP8)
- AMD GPUs: supported via SGLang only
- Huawei Ascend NPUs: supported via MindIE framework

**Install**:
```bash
cd inference
pip install -r requirements.txt
```

---

## Demo Web Application

An unrelated bonus demo lives in `demo/quan-ly-phong-tro-ui.html`: a Vietnamese hostel/room management UI. It is a self-contained single-file HTML app using `localStorage` for persistence — no backend required.

**Run locally**:
```bash
./scripts/run_quan_ly_phong_tro_demo.sh          # default port 4173
./scripts/run_quan_ly_phong_tro_demo.sh 8080     # custom port
# Open: http://127.0.0.1:4173/demo/quan-ly-phong-tro-ui.html
```

The script simply calls `python3 -m http.server` from the repo root.

---

## Key Conventions and Patterns

### Naming Conventions

- **Python**: Standard snake_case throughout; dataclasses with type hints on `ModelArgs`
- **Configs**: kebab-case CLI arguments (`--ckpt-path`, `--hf-ckpt-path`)
- **Weight naming**: HuggingFace names use `self_attn`/`mlp`; internal names use `attn`/`ffn`. The mapping is in `convert.py:mapping`

### Distributed Inference Pattern

All parallel layers check the module-level `world_size` and `rank` globals set during `Transformer.__init__`. A single-process run (`world_size=1`) is also valid and skips all `dist.*` calls.

### FP8 Dispatch Pattern

`model.linear()` (the free function, not the class) handles dtype dispatch:
1. `weight.element_size() > 1` → standard `F.linear` (BF16)
2. `gemm_impl == "bf16"` → dequantize weight, then `F.linear`
3. else → quantize activation, then `fp8_gemm` kernel

### KV Cache Layout

Two modes exist in `MLA`:
- **`absorb`** (default): stores `kv_cache` (compressed, shape `[B, T, kv_lora_rank]`) and `pe_cache` (shape `[B, T, qk_rope_head_dim]`). Lower memory, requires einsum-based attention.
- **`naive`**: stores full `k_cache` and `v_cache`. Higher memory, simpler code.

### Adding New Model Sizes

1. Add a new `configs/config_Xb.json` following the existing schema
2. Ensure `n_experts % model_parallel == 0` in the convert step
3. No code changes required — `ModelArgs(**json.load(f))` handles everything

---

## Third-Party Inference Frameworks

The repository README documents several recommended production-grade inference options:

| Framework | Modes | Notes |
|-----------|-------|-------|
| **SGLang** ≥ v0.4.1 | BF16, FP8 | NVIDIA + AMD; recommended for throughput |
| **LMDeploy** | BF16, FP8 | Online serving + pipeline mode |
| **TensorRT-LLM** | BF16, INT4/INT8 | NVIDIA only; FP8 in progress |
| **vLLM** ≥ v0.6.6 | BF16, FP8 | Pipeline parallelism; NVIDIA + AMD |
| **LightLLM** ≥ v1.0.1 | BF16, FP8 | PD-disaggregation support |

---

## CI/CD

- **`.github/workflows/stale.yml`**: Marks issues stale after 30 days; closes them after 14 more days. Exempts `pinned` and `security` labels. Only runs on `deepseek-ai/DeepSeek-V3` — does not run on forks.
- No automated test suite or linter workflow is configured.

---

## Licenses

- **Code** (`LICENSE-CODE`): MIT — free for any use
- **Model weights** (`LICENSE-MODEL`): DeepSeek Model Agreement — commercial use permitted; see file for restrictions on redistribution and fine-tuning
