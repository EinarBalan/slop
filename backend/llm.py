from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
import torch

class LLMService:
    def __init__(self):
        self.pipe = None
        self.model = None
        self.tokenizer = None
        self.model_name = "meta-llama/Llama-3.1-8B-Instruct"
        self.initialize_lm()

    # def initialize_lm(self):
    #     self.pipe = pipeline(
    #         "text-generation",
    #         model=self.model_name,
    #         device=0,
    #         max_new_tokens=512,  # This controls the maximum number of new tokens to generate
    #         temperature=0.8,     # Controls randomness in generation
    #         do_sample=True       # Enables sampling for more natural text
    #     )

    # def generate_text(self, prompt):
    #     messages = [{"role": "user", "content": prompt}]
    #     return self.pipe(messages)
    #     # return self.pipe(prompt)

    def initialize_lm(self):
        """Initialize the text generation pipeline."""
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

            print(self.model.get_memory_footprint())
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

            return {"generated_text": content}
        except Exception as e:
            return {"error": f"Text generation failed: {str(e)}"}

# Create a singleton instance
llm_service = LLMService() 