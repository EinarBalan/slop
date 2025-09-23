# Seamlessly aligning LLMs with Online user Prefrences

Motivated by the observation that humor is personal, this project aims to create a scalable method for aligning an LLM as closely as possible with user preferences. 

To me it seems that there are two critical aspects of this:
1. Scalability e.g. it doesn't make sense to just fine tune a bunch of models [(although this has been shown to work)](https://arxiv.org/pdf/2502.20356v1) as this is extremely expensive 
2. Seamless preference collection e.g. we don't want to have to poll users as this requires them to go out of their way to fill out a form (which is not easy) and also probably doesn't paint the best picture of their actual user preferences

With these constraints in mind, it seems clear that the best way to go about this is by taking advantage of an existing product like TikTok, Reddit, Instagram, Twitter, etc. that serves content according to user preferences. This allows us to seamlessly collect user preferences in order to inform our LLM towards producing personalized generation. To address scalability, I'm hoping to try out soft prompting techniques. Inspired by UserLLM from DeepMind, it's possible to encode a user's preferences into a user embedding which is then given to an LLM at inference time in order to (hopefully) produce more relevant generation. 

# Build and Run

The docker file does not work yet and I may not actually get it to work at all

```
/backend % conda env create --file env.yml
/backend % conda activate slop 
/backend % python server.py --background --model gpt-5 --experiment base

/backend % cd ../frontend
/frontend % npm install
/frontend % npm run dev
```

Once the docker file works:

```
docker build -t slop:conda /home/ubuntu/slop-utah/slop
```
```
docker run --gpus all -it -p 3000:3000 slop:conda
# Inside container:
conda run -n slop python /app/backend/server.py
```

things I wanted to do but ran out of time for:
- testing on actual social media environemnt in the app I made
- testing w image gen
- finetuned LLM judge
- vector similarity of generated posts (more variety is better)
- investigating social implications
- prompt: what are some topics you like to discuss
- relationship between number of training samples and number of topics able to be captured and represented