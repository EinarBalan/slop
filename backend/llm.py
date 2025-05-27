from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
import torch
from config import (
    MODEL_NAME,
    DEFAULT_MAX_LENGTH,
    DEFAULT_NUM_RETURN_SEQUENCES,
    DEFAULT_TEMPERATURE,
    BASE_PROMPT,
    SUMMARIZE_PROMPT
)

class LLMService:
    def __init__(self, experiment):
        self.pipe = None
        self.model = None
        self.tokenizer = None
        self.model_name = MODEL_NAME
        self.experiment = experiment
        self.initialize_lm()

    def initialize_lm(self):
        """Initialize the text generation pipeline."""
        
        if self.experiment == "base" or \
            self.experiment == "summarize" or \
            self.experiment == "user-defined":
            try:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    # llm_int8_enable_fp32_cpu_offload=True
                )
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map="auto",
                    quantization_config=quantization_config,
                    torch_dtype="auto"
                )

            except Exception as e:
                print(f"Error initializing lm: {e}")
        elif self.experiment == "finetuned":  #TODO
            pass
        elif self.experiment == "slop":  #TODO
            pass
        
    def exp_generate_text(self, max_length=DEFAULT_MAX_LENGTH, num_return_sequences=DEFAULT_NUM_RETURN_SEQUENCES, temperature=DEFAULT_TEMPERATURE):
        """Generate text using the pipeline.
        
        Args:
            max_length (int): Maximum length of generated text
            num_return_sequences (int): Number of sequences to return
            temperature (float): Sampling temperature
        """
        if self.experiment == "base":
            return self.generate_text(BASE_PROMPT, max_length, num_return_sequences, temperature)
        elif self.experiment == "summarize":
            return self.generate_text(SUMMARIZE_PROMPT, max_length, num_return_sequences, temperature)
        elif self.experiment == "finetuned":  #TODO
            return self.generate_text(BASE_PROMPT, max_length, num_return_sequences, temperature)
        elif self.experiment == "slop":  #TODO
            return self.generate_text(BASE_PROMPT, max_length, num_return_sequences, temperature)
        elif self.experiment == "user-defined":  #TODO
            return self.generate_text(BASE_PROMPT, max_length, num_return_sequences, temperature)

    def generate_text(self, prompt, max_length=DEFAULT_MAX_LENGTH, num_return_sequences=DEFAULT_NUM_RETURN_SEQUENCES, temperature=DEFAULT_TEMPERATURE):
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
                add_generation_prompt=True
            )
    
            inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            generated_ids = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature
            )
            
            # Extract only the assistant's response
            full_response = self.tokenizer.batch_decode(generated_ids)[0]
            # Find the last assistant response
            assistant_start = full_response.rfind("<|start_header_id|>assistant<|end_header_id|>")
            if assistant_start != -1:
                assistant_start += len("<|start_header_id|>assistant<|end_header_id|>")
                content = full_response[assistant_start:].strip()
                # Remove any trailing end tokens
                content = content.replace("<|eot_id|>", "").strip()
            else:
                content = full_response

            print(f"generated post: {content}")
            return {"generated_text": content}
        except Exception as e:
            return {"error": f"Text generation failed: {str(e)}"}

def get_llm_service(experiment):
    """Get an instance of the LLM service."""
    return LLMService(experiment) 