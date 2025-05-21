from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class LLMService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = "Qwen/Qwen3-0.6B"
        self.initialize_lm()

    def initialize_lm(self):
        """Initialize the text generation pipeline."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype="auto",
                device_map="auto"
            )
        except Exception as e:
            print(f"Error initializing lm: {e}")

    def generate_text(self, prompt, max_length=1024, num_return_sequences=1, temperature=0.7):
        """Generate text using the pipeline.
        
        Args:
            prompt (str): The input prompt
            max_length (int): Maximum length of generated text
            num_return_sequences (int): Number of sequences to return
            temperature (float): Sampling temperature
            
        Returns:
            dict: Generated text or error message
        """
        if self.model is None:
            return {"error": "Text generation model not initialized"}
            
        try:
            messages = [{"role": "user", "content": prompt}]
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
    
            inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            generated_ids = self.model.generate(
                **inputs,
                max_length=max_length,
                num_return_sequences=num_return_sequences,
                temperature=temperature
            )
            output_ids = generated_ids[0][len(inputs["input_ids"][0]):].tolist()
            content = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip("\n")

            return {"generated_text": content}
        except Exception as e:
            return {"error": f"Text generation failed: {str(e)}"}

# Create a singleton instance
llm_service = LLMService() 