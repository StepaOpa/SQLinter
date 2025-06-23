from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
from pathlib import Path
from typing import Union, Optional


class SQLinterModel:
    def __init__(self) -> None:
        current_dir: Path = Path(__file__).parent
        self.model_path: Union[str, Path] = current_dir.parent / "model"
        self.device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer: AutoTokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model: AutoModelForSeq2SeqLM = AutoModelForSeq2SeqLM.from_pretrained(self.model_path).to(self.device)

    def predict(self, input_text: str, max_length: int = 200) -> str:
        inputs: dict = self.tokenizer(input_text, return_tensors="pt").to(self.device)
        outputs: torch.Tensor = self.model.generate(
            inputs["input_ids"],
            max_new_tokens=max_length,
            pad_token_id=self.tokenizer.pad_token_id,
            num_beams=5,
            early_stopping=True
        )
        # Декодируем результат
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # print("Исправленный SQL:", result)  # убираем отладочный вывод
        
        return result

if __name__ == "__main__":
    current_dir: Path = Path(__file__).parent
    model_path: Path = current_dir.parent / "model"
    model: SQLinterModel = SQLinterModel(model_path)
    
    while True:
        user_input: str = input("Введите SQL запрос (или 'exit' для выхода): ")
        if user_input.lower() == 'exit':
            break
            
        result: str = model.predict(user_input)
        print("Исправленный SQL:", result)