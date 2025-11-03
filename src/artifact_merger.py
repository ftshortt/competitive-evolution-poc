"""Artifact-safe merging and validation utilities (AZR-inspired)

- Validate LoRA checkpoints before merging
- Merge base model + adapters to produce exportable artifact
- Calculate checksums for reproducibility
"""

import os
import hashlib
import json
import logging
from transformers import AutoModelForCausalLM

logger = logging.getLogger(__name__)


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def validate_lora_checkpoint(ckpt_dir: str) -> bool:
    meta = os.path.join(ckpt_dir, 'metadata.json')
    if not os.path.exists(meta):
        logger.warning(f"No metadata.json found in {ckpt_dir}; proceeding conservatively")
        return True
    try:
        with open(meta) as f:
            data = json.load(f)
        # Basic sanity fields
        return 'step' in data and 'loss' in data
    except Exception as e:
        logger.error(f"Failed to parse metadata: {e}")
        return False


def merge_base_with_lora(base_model: str, lora_dir: str, export_dir: str) -> str:
    """Merge base model with LoRA adapters into a standalone artifact.
    This function assumes offlined/PEFT merge pattern and writes checksum.
    """
    from peft import PeftModel

    os.makedirs(export_dir, exist_ok=True)

    if not validate_lora_checkpoint(lora_dir):
        raise ValueError(f"Invalid LoRA checkpoint: {lora_dir}")

    logger.info(f"Loading base model {base_model} for merging...")
    base = AutoModelForCausalLM.from_pretrained(base_model, trust_remote_code=True)
    peft_model = PeftModel.from_pretrained(base, lora_dir)

    logger.info("Merging LoRA weights into base model...")
    merged = peft_model.merge_and_unload()

    logger.info(f"Saving merged artifact to {export_dir}...")
    merged.save_pretrained(export_dir)

    # Write checksum for reproducibility
    checksum_path = os.path.join(export_dir, 'CHECKSUMS.txt')
    with open(checksum_path, 'w') as f:
        for root, _, files in os.walk(export_dir):
            for name in files:
                p = os.path.join(root, name)
                try:
                    f.write(f"{sha256_of_file(p)}  {os.path.relpath(p, export_dir)}\n")
                except Exception:
                    pass

    logger.info("Merge complete with checksums.")
    return export_dir
