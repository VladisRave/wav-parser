import os
import time
import torch
import asyncio
from typing import List, Dict, Tuple, Optional
from openai import AsyncAzureOpenAI
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

LLM_MODE = os.getenv("LLM_MODE", "server")

# Azure config
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT", "gpt-4.1")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")         
AZURE_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")

# Цены за 1 миллион токенов
PRICE_INPUT = float(os.getenv("PRICE_INPUT", "102.10"))
PRICE_CACHED_INPUT = float(os.getenv("PRICE_CACHED_INPUT", "10.21"))
PRICE_OUTPUT = float(os.getenv("PRICE_OUTPUT", "816.76"))

class TokenStats:
    def __init__(self):
        self.non_cached_input = 0
        self.cached_input = 0
        self.output_tokens = 0
        self.calls = 0
    def add(self, non_cached: int, cached: int, output: int):
        self.non_cached_input += non_cached
        self.cached_input += cached
        self.output_tokens += output
        self.calls += 1
    def report(self):
        total_input = self.non_cached_input + self.cached_input
        cost = (self.non_cached_input * PRICE_INPUT +
                self.cached_input * PRICE_CACHED_INPUT +
                self.output_tokens * PRICE_OUTPUT) / 1_000_000
        return {
            "calls": self.calls,
            "non_cached_input_tokens": self.non_cached_input,
            "cached_input_tokens": self.cached_input,
            "total_input_tokens": total_input,
            "avg_input_tokens_per_call": round(total_input / self.calls, 1) if self.calls else 0,
            "avg_output_tokens_per_call": round(self.output_tokens / self.calls, 1) if self.calls else 0,
            "output_tokens": self.output_tokens,
            "total_tokens": total_input + self.output_tokens,
            "cost": round(cost, 2)
        }

token_stats = TokenStats()

azure_client = AsyncAzureOpenAI(
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
)

# Локальная модель
_LLM_MODEL = None
_LLM_TOKENIZER = None
quantization_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)

def load_llm():
    global _LLM_MODEL, _LLM_TOKENIZER
    if _LLM_MODEL is None:
        print("[LLM] Loading local Qwen2.5-7B...")
        _LLM_TOKENIZER = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
        _LLM_MODEL = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-7B-Instruct",
            quantization_config=quantization_config,
            device_map="auto",
        )
        _LLM_MODEL.eval()
        print("[LLM] Local model ready")
    return _LLM_MODEL, _LLM_TOKENIZER

def generate_local(messages: List[Dict], max_new_tokens: int = 128) -> Tuple[str, int, int, int]:
    model, tokenizer = load_llm()
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    input_tokens = inputs.input_ids.shape[1]
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    output_ids = generated_ids[0][inputs.input_ids.shape[1]:]
    output_tokens = len(output_ids)
    response = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
    return response, input_tokens, 0, output_tokens

async def generate_server(messages: List[Dict], max_tokens: int = 256, response_format: Optional[dict] = None) -> Tuple[str, int, int, int]:
    try:
        kwargs = {
            "model": AZURE_DEPLOYMENT,
            "messages": messages,
            "temperature": 0,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format
        response = await azure_client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content.strip()
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        cached = 0
        if hasattr(usage, 'prompt_tokens_details') and usage.prompt_tokens_details:
            cached = getattr(usage.prompt_tokens_details, 'cached_tokens', 0)
        non_cached = prompt_tokens - cached
        output_tokens = usage.completion_tokens
        return content, non_cached, cached, output_tokens
    except Exception as e:
        print(f"[LLM] Azure error: {e}")
        return "", 0, 0, 0

async def generate_llm(messages: List[Dict], max_new_tokens: int = 256, response_format: Optional[dict] = None) -> str:
    if LLM_MODE == "server":
        content, non_cached, cached, out = await generate_server(messages, max_tokens=max_new_tokens, response_format=response_format)
        token_stats.add(non_cached, cached, out)
        return content
    elif LLM_MODE == "local":
        loop = asyncio.get_event_loop()
        content, inp, cached, out = await loop.run_in_executor(None, lambda: generate_local(messages, max_new_tokens))
        token_stats.add(inp, cached, out)
        return content
    else:
        raise ValueError(f"Unknown LLM_MODE: {LLM_MODE}")