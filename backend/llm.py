from openai import OpenAI
import os
from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL_NAME,
    LOCAL_MODEL_NAME,
    DEFAULT_MAX_LENGTH,
    DEFAULT_NUM_RETURN_SEQUENCES,
    DEFAULT_TEMPERATURE,
    PROMPTS
)
from config import args

class LLMService:
    def __init__(self, model, experiment):
        self.pipe = None
        self.model_type = model
        self.local_model = None
        self.api_client = None
        self.tokenizer = None
        self.local_model_name = LOCAL_MODEL_NAME
        self.experiment = experiment
        self.initialize_lm()

    def initialize_lm(self):
        """Initialize the text generation pipeline."""
        if self.model_type == "local":
            self.initialize_local_lm()
        elif self.model_type == "gpt-5" or self.model_type == "gpt-image":
            self.initialize_openai()
        else:
            raise ValueError(f"Invalid model type: {self.model_type}")
       
    def initialize_local_lm(self):
        """Initialize the local LLM."""
        # Lazy import heavy deps only if local model is requested
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch  # noqa: F401
        except Exception as e:
            print(f"Local LLM dependencies not available: {e}")
            self.local_model = None
            self.tokenizer = None
            return
        if self.experiment == "base" or \
            self.experiment == "summarize" or \
            self.experiment == "user-defined" or \
            self.experiment == "like-history-text": #TODO
            try:
                # quantization_config = BitsAndBytesConfig(
                #     load_in_4bit=True,
                #     # llm_int8_enable_fp32_cpu_offload=True
                # )
                self.tokenizer = AutoTokenizer.from_pretrained(self.local_model_name)
                self.local_model = AutoModelForCausalLM.from_pretrained(
                    self.local_model_name,
                    device_map="auto",
                    # quantization_config=quantization_config,
                    torch_dtype="auto"
                )

            except Exception as e:
                print(f"Error initializing lm: {e}")
        elif self.experiment == "finetuned":  #TODO
            pass
        elif self.experiment == "slop":  #TODO
            pass


    def initialize_openai(self):
        """Initialize the OpenAI API."""
        self.api_client = OpenAI(api_key=OPENAI_API_KEY)

    def exp_generate_text(self, max_length=DEFAULT_MAX_LENGTH, num_return_sequences=DEFAULT_NUM_RETURN_SEQUENCES, temperature=DEFAULT_TEMPERATURE):
        """Generate text using the pipeline.
        
        Args:
            max_length (int): Maximum length of generated text
            num_return_sequences (int): Number of sequences to return
            temperature (float): Sampling temperature
        """
        if self.experiment == "base":
            return self.generate_text(PROMPTS["base"], max_length, num_return_sequences, temperature)
        elif self.experiment == "summarize":
            return self.generate_text(PROMPTS["base-summarize"] + PROMPTS["summary"]["generated_text"], max_length, num_return_sequences, temperature)
        elif self.experiment == "finetuned":  #TODO
            return self.generate_text(PROMPTS["base"], max_length, num_return_sequences, temperature)
        elif self.experiment == "slop":  #TODO
            return self.generate_text(PROMPTS["base"], max_length, num_return_sequences, temperature)
        elif self.experiment == "user-defined":  #TODO
            return self.generate_text(PROMPTS["user-defined"], max_length, num_return_sequences, temperature)
        elif self.experiment == "like-history-text": #TODO
            return self.generate_text(PROMPTS["base"], max_length, num_return_sequences, temperature)

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
        if self.model_type == "local":
            return self.generate_text_local(prompt, max_length, num_return_sequences, temperature)
        elif self.model_type == "gpt-5":
            return self.generate_text_api(prompt, max_length, num_return_sequences, temperature)
        elif self.model_type == "gpt-image":
            return self.generate_image_api(prompt, max_length, num_return_sequences, temperature)
        else:
            raise ValueError(f"Invalid model type: {self.model_type}")
        
    def generate_text_local(self, prompt, max_length=DEFAULT_MAX_LENGTH, num_return_sequences=DEFAULT_NUM_RETURN_SEQUENCES, temperature=DEFAULT_TEMPERATURE):
        """Generate text using the local model."""
        if self.local_model is None:
            return {"error": "Text generation model not initialized"}
            
        try:
            messages = [{"role": "user", "content": prompt}]
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True
            )
    
            inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ).to(self.local_model.device)
            
            outputs = self.local_model.generate(    
                **inputs,
                max_length=max_length,
                temperature=temperature
            )
            
            prompt_length = inputs["input_ids"].size(-1)
            generated_ids = outputs[0, prompt_length:].tolist()
            content = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            print(f"generated: {content}")
            return {"generated_text": content}
        except Exception as e:
            return {"error": f"Text generation failed: {str(e)}"}
    
    def generate_text_api(self, prompt, max_length=DEFAULT_MAX_LENGTH, num_return_sequences=DEFAULT_NUM_RETURN_SEQUENCES, temperature=DEFAULT_TEMPERATURE):
        """Generate text using the OpenAI API."""
        try:
            response = self.api_client.responses.create(
                model=OPENAI_MODEL_NAME,
                input=prompt,
                # temperature=temperature,
                # The Responses API uses max_output_tokens
                # max_output_tokens=max_length,
            )

            # Prefer the helper property when available
            text = getattr(response, "output_text", None)
            if not text:
                # Fallback to structured parsing
                try:
                    text = response.output[0].content[0].text
                except Exception:
                    text = str(response)

            print(f"generated post: {text}") #TODO: remove
            return {"generated_text": text}
        except Exception as e:
            return {"error": f"OpenAI generation failed: {str(e)}"}
        
    def generate_image_api(self, prompt, max_length=DEFAULT_MAX_LENGTH, num_return_sequences=DEFAULT_NUM_RETURN_SEQUENCES, temperature=DEFAULT_TEMPERATURE):
        """Generate image using the OpenAI API."""
        raise NotImplementedError("Image generation is not implemented yet")
        
        
        
        

def get_llm_service(model,experiment):
    """Get an instance of the LLM service."""
    return LLMService(model,experiment) 
