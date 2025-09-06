pip install dotenv sqlalchemy psycopg[binary]

python ./data/sampleposts.py -n 750 --table posts --out ./data/posts.json
python ./data/sampleposts.py -n 750 --table humorposts --out ./data/humorposts.json