import os
import time
import torch
from typing import List, Dict

from openai import AzureOpenAI
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


# CONFIG
LLM_MODE = os.getenv("LLM_MODE", "local")  # local-Qwen-2.5 | server-GPT-5

AZURE_DEPLOYMENT = "gpt-5"
AZURE_ENDPOINT = "https://YOUR-ENDPOINT.openai.azure.com/"
AZURE_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_API_VERSION = "2024-02-15-preview"

_LLM_MODEL = None
_LLM_TOKENIZER = None

# LOCAL MODEL CONFIG
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# AZURE CLIENT
azure_client = AzureOpenAI(
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
)


def load_llm():
    """
    Загружает локальную LLM (Qwen) один раз (singleton).

    Returns:
        tuple: (model, tokenizer)
    """
    global _LLM_MODEL, _LLM_TOKENIZER

    if _LLM_MODEL is None:
        device_info = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[LLM] Using device: {device_info}")

        _LLM_TOKENIZER = AutoTokenizer.from_pretrained(
            "Qwen/Qwen2.5-7B-Instruct"
        )

        _LLM_MODEL = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-7B-Instruct",
            quantization_config=quantization_config,
            device_map="auto",
        )

        _LLM_MODEL.eval()

        print(f"[LLM] Model loaded: Qwen2.5-7B-Instruct")
        if torch.cuda.is_available():
            print(f"[LLM] GPU: {torch.cuda.get_device_name(0)}")
            mem = torch.cuda.memory_allocated() / 1024**3
            print(f"[LLM] VRAM used: {mem:.2f} GB")

    return _LLM_MODEL, _LLM_TOKENIZER


def generate_local(messages: List[Dict], max_new_tokens: int = 128) -> str:
    """
    Генерация ответа через локальную модель (Qwen).

    Args:
        messages: список сообщений в формате OpenAI chat
        max_new_tokens: максимальная длина ответа

    Returns:
        str: ответ модели
    """
    model, tokenizer = load_llm()

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )

    generated_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids in zip(
            model_inputs.input_ids, generated_ids
        )
    ]

    return tokenizer.batch_decode(
        generated_ids, skip_special_tokens=True
    )[0].strip()


def generate_server(messages: List[Dict], max_tokens: int = 256, retries: int = 2) -> str:
    """
    Генерация ответа через Azure OpenAI (GPT-5).

    Args:
        messages: список сообщений
        max_tokens: максимум токенов
        retries: количество повторных попыток

    Returns:
        str: ответ модели
    """
    for attempt in range(retries):
        try:
            response = azure_client.chat.completions.create(
                model=AZURE_DEPLOYMENT,
                messages=messages,
                temperature=0,
                top_p=1,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content

            if content:
                return content.strip()

        except Exception as e:
            print(f"[LLM] Azure error (attempt {attempt+1}): {e}")
            time.sleep(1)

    return ""


def generate_llm(messages: List[Dict], max_new_tokens: int = 256) -> str:
    """
    Унифицированный интерфейс генерации.

    Автоматически выбирает:
    - server -> GPT
    - local -> Qwen

    Args:
        messages: список сообщений
        max_new_tokens: длина ответа

    Returns:
        str: ответ модели
    """
    if LLM_MODE == "server":
        return generate_server(messages, max_tokens=max_new_tokens)

    elif LLM_MODE == "local":
        return generate_local(messages, max_new_tokens=max_new_tokens)

    else:
        raise ValueError(f"Unknown LLM_MODE: {LLM_MODE}")