pip install dotenv sqlalchemy psycopg[binary]

export DATABASE_URL="postgresql+psycopg://slop:slop@127.0.0.1:65433/slop?connect_timeout=3&sslmode=disable" 

python ./data/sampleposts.py -n 750 --table posts --out ./data/posts.json
python ./data/sampleposts.py -n 750 --table humorposts --out ./data/humorposts.json