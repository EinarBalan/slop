# Seamlessly aligning LLMs with Online user Prefrences

Motivated by the observation that humor is personal, this project aims to create a scalable method for aligning an LLM as closely as possible with user preferences. 

To me it seems that there are two critical aspects of this:
1. Scalability e.g. it doesn't make sense to just fine tune a bunch of models [(although this has been shown to work)](https://arxiv.org/pdf/2502.20356v1) as this is extremely expensive 
2. Seamless preference collection e.g. we don't want to have to poll users as this requires them to go out of their way to fill out a form (which is not easy) and also probably doesn't paint the best picture of their actual user preferences

With these constraints in mind, it seems clear that the best way to go about this is by taking advantage of an existing product like TikTok, Reddit, Instagram, Twitter, etc. that serves content according to user preferences. This allows us to seamlessly collect user preferences in order to inform our LLM towards producing personalized generation. To address scalability, I'm hoping to try out soft prompting techniques. Inspired by UserLLM from DeepMind, it's possible to encode a user's preferences into a user embedding which is then given to an LLM at inference time in order to (hopefully) produce more relevant generation. 

I also hope to create a unified recommendation and contextualization system. dot product user embedding and post embeddings to find most relevant. encoding through sentence t5 

Experiments
- comparing generation like rate for different alignment methods
- comparing generation dislike rate for different alignment methods
- comparing generation AI detected rate for different alignment methods
- comparing judgement alignment e.g. funny or not funny between human and LLM
- comparing different model sizes (though all of them will have to be relatively small)
- trying summarization technique on image diffusion models
    - use summarization technique to generate textual description which is then fed into diffusion model

need to randomly interperse these different methods in the same session for a blind comparison

Alignment methods todo: add detail for each:
- slop
    - allows use of a single frozen model for all users
    - a few options:
        - use sentence t5 (or other embedding model) to encode all post data in database, and add these to the user embedding whenever it is liked. user embedding consists of multiple topic embedding directions. if there is a topic that is close to the post already, average with this and update that topic. otherwise add new topic embedding (e.g. the new post emebedding) 
            - how close should the post be to a topic to take average?
            - can also easily use topic embeddings to retrieve more relevant posts for recommendation engine
        - don't consolidate multiple topics, just encode all posts and add these to prompt
- supervised finetuning (as a potential ceiling)
    - need a separate finetune for each user
    - finetune on hand selected good examples that represent my preferences (what I like) and explanations for why 
    - can try without explanations as well for more direct comparison
- LLM summarization 
    - still benefits from both advantages as slop soft prompting
    - can also be applied to larger models
    - whenever a user likes a post, use an off the shelf LLM (probably via API) to update a summary of the user's preferences
    - this summary is then supplied to the local model at inference
    - using this method with larger models? image models?
- no alignment (as a floor)
    - the prompt really matters, we can try a few different options

models attempted:
- https://huggingface.co/Qwen/Qwen3-0.6B
    - runs fine, generation quality questionable
    - 5-6 GB VRAM
- https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
    - does not run (could try quantized version)
    - tried 4bit quantized (its alright, very quick and generation quality is decent for speed)
- https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct **
    - much much better quality but quite slow
    - nearly 10 GB VRAM (full), 31 GB RAM
    - supported by unsloth
- https://huggingface.co/meta-llama/Llama-3.2-1B
    - no instruction tuning = bad
- https://huggingface.co/google/gemma-2b-it
    - very quick, quality better than qwen but slightly questionable (might be better with better prompting)
    - also nearly 10 GB VRAM, but doesn't seem to hit as hard as llama 3.2 3B-Instruct
- https://huggingface.co/unsloth/gemma-3-1b-it
    - quick, bad generation quality (at least without any intervention)
    - keeps generating variations of the same thing for ucla prompt
- https://huggingface.co/google/gemma-3-4b-it
    - failed
- https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
    - very quick, stays to format, but very generic 


models to try:
- qwen 2.5 3b
- mistral
- phi4-mini 4b
- quantizations of above that didn't work (need to figure that out)


unsloth models
https://huggingface.co/unsloth?sort_models=likes#models