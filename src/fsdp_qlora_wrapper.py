"""FSDP+QLoRA Compatible Wrapper for Agent Model Fine-tuning

Adapted from Absolute-Zero-Reasoner's best practices for robust distributed training.
Implements the "Freeze, Inject, and Wrap" sequence to bypass FSDP+QLoRA incompatibility.

Supported models: DeepSeek OCR, DeepSeek R1, Qwen Coder
"""

import os
import torch
import torch.distributed as dist
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import ShardingStrategy, MixedPrecision
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import logging

logger = logging.getLogger(__name__)


class FSDPQLoRAWrapper:
    """Robust FSDP+QLoRA wrapper following AZR's proven patterns."""
    
    def __init__(
        self,
        model_name: str,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: list = None,
        use_4bit: bool = True,
        checkpoint_dir: str = "./checkpoints"
    ):
        self.model_name = model_name
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.target_modules = target_modules or ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        self.use_4bit = use_4bit
        self.checkpoint_dir = checkpoint_dir
        
        # Ensure checkpoint directory exists
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
    def load_model_with_quantization(self):
        """Load model with 4-bit quantization for memory efficiency."""
        if self.use_4bit:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
        else:
            bnb_config = None
            
        logger.info(f"Loading base model: {self.model_name}")
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16
        )
        
        return model
    
    def apply_freeze_inject_wrap(self, model):
        """Apply AZR's 'Freeze, Inject, and Wrap' sequence for FSDP+QLoRA.
        
        This is the critical pattern that ensures compatibility:
        1. FREEZE: Freeze base model parameters
        2. INJECT: Add LoRA adapters
        3. WRAP: Apply FSDP sharding
        """
        # Step 1: FREEZE - Prepare model for k-bit training (freezes base params)
        logger.info("Step 1: Freezing base model parameters...")
        model = prepare_model_for_kbit_training(model)
        
        # Step 2: INJECT - Add LoRA adapters
        logger.info("Step 2: Injecting LoRA adapters...")
        lora_config = LoraConfig(
            r=self.lora_r,
            lora_alpha=self.lora_alpha,
            target_modules=self.target_modules,
            lora_dropout=self.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM"
        )
        model = get_peft_model(model, lora_config)
        
        # Enable gradient checkpointing for memory efficiency
        model.enable_input_require_grads()
        
        logger.info(f"LoRA trainable parameters: {model.print_trainable_parameters()}")
        
        # Step 3: WRAP - Apply FSDP sharding
        logger.info("Step 3: Wrapping with FSDP...")
        mixed_precision_policy = MixedPrecision(
            param_dtype=torch.bfloat16,
            reduce_dtype=torch.bfloat16,
            buffer_dtype=torch.bfloat16
        )
        
        model = FSDP(
            model,
            sharding_strategy=ShardingStrategy.FULL_SHARD,
            mixed_precision=mixed_precision_policy,
            use_orig_params=True,
            limit_all_gathers=True
        )
        
        logger.info("FSDP+QLoRA wrapper successfully applied!")
        return model
    
    def setup_distributed(self):
        """Initialize distributed training environment."""
        if not dist.is_initialized():
            dist.init_process_group(backend="nccl")
        
        local_rank = int(os.environ.get("LOCAL_RANK", 0))
        torch.cuda.set_device(local_rank)
        
        return local_rank
    
    def save_checkpoint(self, model, step: int, metadata: dict = None):
        """Save checkpoint with validation metadata following AZR patterns.
        
        Implements frequent checkpointing (every 2 steps) as recommended by AZR.
        """
        checkpoint_path = os.path.join(self.checkpoint_dir, f"checkpoint-{step}")
        os.makedirs(checkpoint_path, exist_ok=True)
        
        # Save LoRA adapters only (not full model)
        model.module.save_pretrained(checkpoint_path)
        
        # Save metadata for validation
        if metadata:
            metadata_path = os.path.join(checkpoint_path, "metadata.json")
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        logger.info(f"Checkpoint saved at step {step}: {checkpoint_path}")
        return checkpoint_path
    
    def load_checkpoint(self, checkpoint_path: str, model):
        """Load checkpoint from path."""
        logger.info(f"Loading checkpoint from: {checkpoint_path}")
        model.module.load_adapter(checkpoint_path)
        return model
    
    def create_agent_model(self):
        """Complete setup: load model, apply wrappers, return ready-to-train model."""
        # Setup distributed if needed
        local_rank = self.setup_distributed()
        
        # Load quantized model
        model = self.load_model_with_quantization()
        
        # Apply Freeze-Inject-Wrap sequence
        model = self.apply_freeze_inject_wrap(model)
        
        return model, local_rank


def create_ocr_agent(checkpoint_dir="./checkpoints/ocr"):
    """Create FSDP+QLoRA wrapped DeepSeek OCR agent."""
    wrapper = FSDPQLoRAWrapper(
        model_name="deepseek-ai/deepseek-ocr",
        checkpoint_dir=checkpoint_dir
    )
    return wrapper.create_agent_model()


def create_r1_agent(checkpoint_dir="./checkpoints/r1"):
    """Create FSDP+QLoRA wrapped DeepSeek R1 agent."""
    wrapper = FSDPQLoRAWrapper(
        model_name="deepseek-ai/DeepSeek-R1",
        checkpoint_dir=checkpoint_dir
    )
    return wrapper.create_agent_model()


def create_qwen_agent(checkpoint_dir="./checkpoints/qwen"):
    """Create FSDP+QLoRA wrapped Qwen Coder agent."""
    wrapper = FSDPQLoRAWrapper(
        model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
        checkpoint_dir=checkpoint_dir
    )
    return wrapper.create_agent_model()
