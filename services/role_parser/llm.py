import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Конфигурация 4-битной квантизации
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,                # загружать в 4 бита
    bnb_4bit_compute_dtype=torch.float16,  # вычисления в float16
    bnb_4bit_use_double_quant=True,   # дополнительное сжатие
)

_LLM_MODEL = None
_LLM_TOKENIZER = None


def load_llm():
    global _LLM_MODEL, _LLM_TOKENIZER

    if _LLM_MODEL is None:
        # Проверяем доступность GPU (для печати, модель загрузится сама)
        device_info = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device_info}")

        # Токенизатор (без изменений)
        _LLM_TOKENIZER = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

        # Модель с квантизацией и автоматическим распределением
        _LLM_MODEL = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-7B-Instruct",
            quantization_config=quantization_config,
            device_map="auto",          # auto распределит слои между GPU/CPU
        )
        _LLM_MODEL.eval()

        # Информация о размещении
        print(f"Model device: {_LLM_MODEL.device}")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        # Память после загрузки
        allocated = torch.cuda.memory_allocated() / 1024**3
        print(f"VRAM used: {allocated:.2f} GB")

    return _LLM_MODEL, _LLM_TOKENIZER


def generate_llm(messages, max_new_tokens=512):
    model, tokenizer = load_llm()

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.2
        )

    generated_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return response