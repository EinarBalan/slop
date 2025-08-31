import argparse
import os
import json
from dotenv import load_dotenv

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description='Run the Flask server with optional background LLM generation')
    parser.add_argument('--background', action='store_true', help='Enable background LLM generation')
    parser.add_argument('--model', type=str, default='local', help='Choose from local, gpt-5, gpt-image')
    parser.add_argument('--archive', action='store_true',
                        help='Serve AI posts from archive instead of generating new ones. '
                             'If enabled, the chosen --model/--experiment will not be honored for AI posts.')
    parser.add_argument('--source', type=str, choices=['base', 'base-humor'], default='base',
                        help='Choose generation prompt source ("base" or "base-humor")')
    parser.add_argument('--experiment', type=str, default='base',
                        help='Default experiment to use (e.g., base, summarize, subreddit, etc.)')
    return parser.parse_args()

# Parse arguments once when the module is imported
args = parse_args()

# Server configuration
BATCH_SIZE = 10

# Database configuration
# External database is required 
# Example: postgresql+psycopg://user:pass@host:5432/slop
DATABASE_URL = os.getenv("DATABASE_URL")

# Auth configuration
SECRET_KEY = os.getenv("SECRET_KEY", "yea-secret")
DEV_AUTH_NO_PASSWORD = os.getenv("DEV_AUTH_NO_PASSWORD", "true").lower() in ("1", "true", "yes")

# Generation configuration(
GENERATE_BATCH_SIZE = int(os.getenv("GENERATE_BATCH_SIZE", "5"))
AI_POSTS_QUEUE_SIZE = int(os.getenv("AI_POSTS_QUEUE_SIZE", "30"))  # Maximum number of AI posts to store
GENERATION_INTERVAL = float(os.getenv("GENERATION_INTERVAL", "2"))  # Seconds between generation attempts
AI_POSTS_RATIO = float(os.getenv("AI_POSTS_RATIO", "0.4"))    # Fraction of AI posts in the feed (0.0 - 1.0)

# Experiments
AVAILABLE_EXPERIMENTS = [
    'base',
    'summarize',
    'user-defined',
    'like-history-text',
    'slop',
    'finetuned',
    'subreddit',
]

# local LLM configuration
LOCAL_MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
DEFAULT_MAX_LENGTH = 1024
DEFAULT_NUM_RETURN_SEQUENCES = 1
DEFAULT_TEMPERATURE = 0.7

# Subreddit lists (kept here so generation does not depend on data scripts)
HUMOR_SUBREDDITS = [
    "Jokes", "3amjokes", "DadJokes", "CleanJokes", "Puns",
    "Oneliners", "AntiJokes", "BadJokes", "copypasta",
    "bookscirclejerk", "moviescirclejerk", "Gamingcirclejerk",
    "soccercirclejerk", "nbacirclejerk", "memes", "okbuddycinephile", 
    "okbuddyretard", "shitposting", "anarchychess", "whenthe",
    "sillyconfession", "dankchristianmemes", "shittymoviedetails", "funny",
    "TIFU", "Unexpected", "ComedyCemetery", "dankmemes",  "CrappyDesign", 
    "AnimalsBeingDerps", "wholesomememes", "me_irl", "gifs", "BlursedImages",
    "Blursedcomments", "comedyheaven", "cringepics", "cringe", "PeopleFuckingDying",
    "perfectlycutscreams", "raimimemes", "shid_and_camed", "wtfstockphotos", "youngpeopleyoutube", 
    "MoldyMemes", "nukedmemes", "tombstoning", "fatsquirrelhate", "engrish", "guitarcirclejerk", "vinuljerk", 
    "childrenfallingover", "ContagiousLaughter", "SipsTea", "wallstreetbets", "astrologymemes",
    "funnyanimals", "funnycats", "funnyvideos"
]

WHITELIST_SUBREDDITS = set([
    "ModernWarefareII", "teenagers", "relationship_advice", "NoStupidQuestions", "ModernWarefareII", "buildapc", "tipofmytongue", "pcmasterrace", "legaladvice", "shittyjobsforrobots", "AskDocs", "LoveIsBlindOnNetflix", "lovemanga", "BlazingDiscount", "BlazeDiscount", "Fantasy_Football", "Overwatch", "NoFilterNews", "AmItheAsshole", "ApplyingToCollege", "ADHD", "SteamDeck", "Vent", "personalfinance", "Warthunder", "HomeImprovement", "RimWorld", "EldenRing", "BreakUps", "GooglePixel", "brasil", "gaming", "newworldgame", "dadjokes", "ask", "Minecraft", "autism", "wow", "MechanicAdvice", "careerguidance", "OnePiece", "DestinyTheGame", "deadbydaylight", "sysadmin", "learnprogramming", "Teachers", "MarvelSnap", "TwoSentenceHorror", "PcBuild", "excel", "leagueoflegends", "Christianity", "antiwork", "VeteransBenefits", "pregnant", "2007scape", "csMajors", "learnpython", "FortNiteBR", "Cooking", "fo76", "BeyondTheFog", "Parenting", "skyrimmods", "cyberpunkgame", "UnsentLetters", "HeadphoneAdvice", "LegalAdviceUK", "airsoft", "adhdwomen", "beyondthebump", "dogs", "AskUK", "Crushes", "Wallstreeetsilver", "DnD", "ShadowBan", "every15min", "lonely", "apexlegends", "Drizzy", "Philippines", "modernwarefare2", "fut", "india", "hearthstone", "GothamKnights", "LSAT", "nba", "UKPersonalFinance", "GodofWar", "Bayonetta", "shrooms", "anime", "lawschooladmissions", "conspiracy", "Jokes", "CreditCards", "USCIS", "cats", "NBA2k", "borrow", "3dprinting", "Music", "OCD", "DreamlightValleuy", "KGBTR", "bipolar", "real_China_irl", "manga", "nursing", "NHLHUT", "Technoblade", "HomeNetworking", "Bannerlord", "socialskills", "travel", "walmart", "Destiny", "relationships", "Terraria", "HouseOfTheDragon", "MarvelStrikeForce", "Earnin", "TheFreshAndFit", "AutismInWomen", "skyrim", "DMAcademy", "NoMansSkyTheGame", "golf", "puppy101", "Warhammer40k", "Entrepreneur", "army", "Warframe", "lgbt", "SkincareAddiction", "selfimprovment", "funkopop", "copypasta", "avatartrading", "IVF", "Dreams", "CatAdvice", "UCSD", "GamingLaptops", "horror", "namenerds", "Aquariums", "feedthebeast", "Catholicism", "bloxfruits", "overwatch2", "cscareerquestions", "premed", "ffxiv", "FanFiction", "sales", "vce", "linuxquestions", "exmormon", "trees", "fantasyfootballadvice", "EDH", "Persona5", "venting", "RocketLeague", "toddlers", "dubai", "SGExams", "OverwatchUniversity", "playstation", "confessions", "wallstreetbets", "ireland", "movies", "duolingo", "cryptostreetbets", "runescape", "starbucks", "TwoXChromosomes", "covidlonghaulers", "askdentists", "Nepal", "CasualConersation", "socialanxiety", "mumbai", "fountainpens", "cocaine", "weddingplanning", "smallbusiness", "delhi", "Denmark", "dancingwiththestars", "residentevil", "VALORANT", "NewTubers", "CryptoCurrency", "elderscrollsonline", "WeightLossAdvice", "StardewVally", "doordash_drivers", "homeassistant", "harrypotter", "destiny2", "40kLore", "YoungRoyals", "leaves", "ucla", "StarWars", "splatoon", "germany", "Superstonk", "pokemongo", "GroundedGame", "totalwar", "jobs", "TheHandmaidsTale", "AmazonFC", "projectzomboid", "dating", "ExNoContact", "mac", "AusFinance", "simracing", "canthandlemoney", "MacOs", "ottawa", "homelab", "ClashRoyale", "h3h3productions", "mexico", "iphone", "islam", "EscapefromTarkov", "emetophobia", "gradadmissions", "pokemon", "Healthygamergg", "RandomThoughts", "USPS", "childfree", "China_irl", "gamedev", "tressless", "RealEstate", "UIUC", "OCPoetry", "wildrift", "college", "Accounting", "exjw", "foxholegame", "hvacadvice", "birthcontrol", "Fallout", "ios", "PSLF", "ukvisa", "youtube", "unrealengine", "AppleWatch", "mbti", "Roleplay", "bleach", "spirituality", "Stellaris", "dndnext", "worldbuilding", "LSD", "Mustardtopia", "starcitizen", "NewParents", "learnmath", "6thForm", "TheDragonPrince", "migraine", "Plumbing", "ARK", "classicwow", "DarkAndDarker", "UberEATS", "Divorce", "mountandblade", "Scholar", "Sephora", "poker", "newzealand", "Cornell", "doordash", "Testosterone", "hoi4", "Chucky", "uberdrivers", "Scams", "Diablo_2_Resurrected", "GilmoreGirls", "AirForce", "ITCareerQuestions", "blender", "gtaonline", "CallOfDutyMobile", "self", "footballmanagergames", "ontario", "thewalkingdead", "Yugioh101", "espresso", "bjj", "berkeley", "Hpfanfiction", "OnePiecePowerScaling", "tf2", "magicTCG", "melbourne", "dayz", "EnglishLearning", "progzonlymusic", "medical", "greece", "asoiaf", "osureport", "nvidia", "reddeadredemption", "Twitch", "MouseReview", "TowerOfFantasy", "Insurance", "IBO", "lexapro", "hometheater", "Epilepsy", "explainlikeimfive", "Nanny", "writing", "thinkpad", "WouldYouRather", "webdev", "Target", "crochet"
])

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = "gpt-5"

# Load prompts from JSON file
PROMPTS_FILE = os.path.join(os.path.dirname(__file__), 'prompts.json')
with open(PROMPTS_FILE, 'r') as f:
    PROMPTS = json.load(f)

# Export the args object and constants so they can be imported by other modules
__all__ = [
    'args', 
    'BATCH_SIZE', 
    'CSV_FILE',
    'DATABASE_URL',
    'SECRET_KEY',
    'DEV_AUTH_NO_PASSWORD',
    'GENERATE_BATCH_SIZE',
    'AI_POSTS_QUEUE_SIZE',
    'GENERATION_INTERVAL',
    'AI_POSTS_RATIO',
    'LOCAL_MODEL_NAME',
    'OPENAI_API_KEY',
    'OPENAI_MODEL_NAME',
    'DEFAULT_MAX_LENGTH',
    'DEFAULT_NUM_RETURN_SEQUENCES',
    'DEFAULT_TEMPERATURE',
    'PROMPTS',
    'PROMPTS_FILE',
    'AVAILABLE_EXPERIMENTS',
    'HUMOR_SUBREDDITS',
    'WHITELIST_SUBREDDITS'
] 