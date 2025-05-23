from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
import torch

# Base prompt for post generation
base_prompt = """
Please generate a post for the subreddit r/ucla.
Your post should be relatively short and preferably humorous. It can be about anything. Do not output any other text than the title and post. Make sure to stick to the format exactly.
Example outputs:

title: Cooked
self_text: Can't wait for this shit ass quarter to end. My jealousy for semester students is unmatched and cannot be measured in a quantifiable manner right now.

title: don't take people's things 😭
self_text: i can't believe i even have to say this omg. whoever took my water bottle please give it back it's purple with lots of stickers

title: Dinner in Westwood
self_text: My daughter has 2 day freshman orientation in July. Looking for recommendations for dinner on a Friday night we will be staying in Westwood that night. We will prefer not to drive. Thank you. We like all types of food. Just want her to get familiar with what's close to campus.
"""

# Summarize prompt for user interest analysis
summarize_prompt = """
The following is a summary of the current user's interests based on posts they have liked in the past: 'Based on the posts the user has liked, it appears that their interests include:

* Complaints about UCLA's academic quarter system and the stress associated with it
* Concern for personal property (specifically water bottles)
* Food and dining options near the UCLA campus
* Parental or family-related concerns (as evidenced by liking a post about freshman orientation)

The user seems to be a student at UCLA, possibly an undergraduate, who is frustrated with the academic demands of
the quarter system and is looking for ways to navigate the campus community. They also appear to be concerned with
maintaining a sense of normalcy in their life despite the challenges of university life.'

Here is a new post that the user has liked:

title: Dinner in Westwood
self_text: My daughter has 2 day freshman orientation in July. Looking for recommendations for dinner on a Friday night we will be staying in Westwood that night. We will prefer not to drive. Thank you. We like all types of food. Just want her to get familiar with what's close to campus.

Based on the previous summary and this new post, please generate a new summary of the user's interests.
"""

# TODO: add class parameter to specify which experiment to run
class LLMService:
    def __init__(self, experiment):
        self.pipe = None
        self.model = None
        self.tokenizer = None
        self.model_name = "meta-llama/Llama-3.1-8B-Instruct"
        self.experiment = experiment
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
        
    def exp_generate_text(self, max_length=1024, num_return_sequences=1, temperature=0.7):
        """Generate text using the pipeline.
        
        Args:
            prompt (str): The input prompt
            max_length (int): Maximum length of generated text
            num_return_sequences (int): Number of sequences to return
            temperature (float): Sampling temperature
        """
        if self.experiment == "base":
            return self.generate_text(base_prompt, max_length, num_return_sequences, temperature)
        elif self.experiment == "summarize": #TODO
            return self.generate_text(summarize_prompt, max_length, num_return_sequences, temperature)
        elif self.experiment == "finetuned":  #TODO
            return self.generate_text(base_prompt, max_length, num_return_sequences, temperature)
        elif self.experiment == "slop":  #TODO
            return self.generate_text(base_prompt, max_length, num_return_sequences, temperature)
        elif self.experiment == "user-defined":  #TODO
            return self.generate_text(base_prompt, max_length, num_return_sequences, temperature)

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

            print(f"generated post: {content}")
            return {"generated_text": content}
        except Exception as e:
            return {"error": f"Text generation failed: {str(e)}"}

def get_llm_service(experiment):
    """Get an instance of the LLM service."""
    return LLMService(experiment) 