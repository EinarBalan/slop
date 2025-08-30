import csv
import sys
import os
from pathlib import Path
# Increase CSV field size limit to handle very large self_text fields
try:
    csv.field_size_limit(sys.maxsize)
except Exception:
    # Fallback for platforms where sys.maxsize overflows the C long
    csv.field_size_limit(2147483647)

# Banned keywords to filter out
BANNED_KEYWORDS = ["sex", "selfharm", "thread", "meta", "[deleted]", "[removed]"]

BANNED_TAGS = ["[deleted]", "[removed]", "Megapost"]

WHITELIST_SUBREDDITS = set(["ModernWarefareII", "teenagers", "relationship_advice", "NoStupidQuestions", "ModernWarefareII", "buildapc", "tipofmytongue", "pcmasterrace", "legaladvice", "shittyjobsforrobots", "AskDocs", "LoveIsBlindOnNetflix", "lovemanga", "BlazingDiscount", "BlazeDiscount", "Fantasy_Football", "Overwatch", "NoFilterNews", "AmItheAsshole", "ApplyingToCollege", "ADHD", "SteamDeck", "Vent", "personalfinance", "Warthunder", "HomeImprovement", "RimWorld", "EldenRing", "BreakUps", "GooglePixel", "brasil", "gaming", "newworldgame", "dadjokes", "ask", "Minecraft", "autism", "wow", "MechanicAdvice", "careerguidance", "OnePiece", "DestinyTheGame", "deadbydaylight", "sysadmin", "learnprogramming", "Teachers", "MarvelSnap", "TwoSentenceHorror", "PcBuild", "excel", "leagueoflegends", "Christianity", "antiwork", "VeteransBenefits", "pregnant", "2007scape", "csMajors", "learnpython", "FortNiteBR", "Cooking", "fo76", "BeyondTheFog", "Parenting", "skyrimmods", "cyberpunkgame", "UnsentLetters", "HeadphoneAdvice", "LegalAdviceUK", "airsoft", "adhdwomen", "beyondthebump", "dogs", "AskUK", "Crushes", "Wallstreeetsilver", "DnD", "ShadowBan", "every15min", "lonely", "apexlegends", "Drizzy", "Philippines", "modernwarefare2", "fut", "india", "hearthstone", "GothamKnights", "LSAT", "nba", "UKPersonalFinance", "GodofWar", "Bayonetta", "shrooms", "anime", "lawschooladmissions", "conspiracy", "Jokes", "CreditCards", "USCIS", "cats", "NBA2k", "borrow", "3dprinting", "Music", "OCD", "DreamlightValleuy", "KGBTR", "bipolar", "real_China_irl", "manga", "nursing", "NHLHUT", "Technoblade", "HomeNetworking", "Bannerlord", "socialskills", "travel", "walmart", "Destiny", "relationships", "Terraria", "HouseOfTheDragon", "MarvelStrikeForce", "Earnin", "TheFreshAndFit", "AutismInWomen", "skyrim", "DMAcademy", "NoMansSkyTheGame", "golf", "puppy101", "Warhammer40k", "Entrepreneur", "army", "Warframe", "lgbt", "SkincareAddiction", "selfimprovment", "funkopop", "copypasta", "avatartrading", "IVF", "Dreams", "CatAdvice", "UCSD", "GamingLaptops", "horror", "namenerds", "Aquariums", "feedthebeast", "Catholicism", "bloxfruits", "overwatch2", "cscareerquestions", "premed", "ffxiv", "FanFiction", "sales", "vce", "linuxquestions", "exmormon", "trees", "fantasyfootballadvice", "EDH", "Persona5", "venting", "RocketLeague", "toddlers", "dubai", "SGExams", "OverwatchUniversity", "playstation", "confessions", "wallstreetbets", "ireland", "movies", "duolingo", "cryptostreetbets", "runescape", "starbucks", "TwoXChromosomes", "covidlonghaulers", "askdentists", "Nepal", "CasualConersation", "socialanxiety", "mumbai", "fountainpens", "cocaine", "weddingplanning", "smallbusiness", "delhi", "Denmark", "dancingwiththestars", "residentevil", "VALORANT", "NewTubers", "CryptoCurrency", "elderscrollsonline", "WeightLossAdvice", "StardewVally", "doordash_drivers", "homeassistant", "harrypotter", "destiny2", "40kLore", "YoungRoyals", "leaves", "ucla", "StarWars", "splatoon", "germany", "Superstonk", "pokemongo", "GroundedGame", "totalwar", "jobs", "TheHandmaidsTale", "AmazonFC", "projectzomboid", "dating", "ExNoContact", "mac", "AusFinance", "simracing", "canthandlemoney", "MacOs", "ottawa", "homelab", "ClashRoyale", "h3h3productions", "mexico", "iphone", "islam", "EscapefromTarkov", "emetophobia", "gradadmissions", "pokemon", "Healthygamergg", "RandomThoughts", "USPS", "childfree", "China_irl", "gamedev", "tressless", "RealEstate", "UIUC", "OCPoetry", "wildrift", "college", "Accounting", "exjw", "foxholegame", "hvacadvice", "birthcontrol", "Fallout", "ios", "PSLF", "ukvisa", "youtube", "unrealengine", "AppleWatch", "mbti", "Roleplay", "bleach", "spirituality", "Stellaris", "dndnext", "worldbuilding", "LSD", "Mustardtopia", "starcitizen", "NewParents", "learnmath", "6thForm", "TheDragonPrince", "migraine", "Plumbing", "ARK", "classicwow", "DarkAndDarker", "UberEATS", "Divorce", "mountandblade", "Scholar", "Sephora", "poker", "newzealand", "Cornell", "doordash", "Testosterone", "hoi4", "Chucky", "uberdrivers", "Scams", "Diablo_2_Resurrected", "GilmoreGirls", "AirForce", "ITCareerQuestions", "blender", "gtaonline", "CallOfDutyMobile", "self", "footballmanagergames", "ontario", "thewalkingdead", "Yugioh101", "espresso", "bjj", "berkeley", "Hpfanfiction", "OnePiecePowerScaling", "tf2", "magicTCG", "melbourne", "dayz", "EnglishLearning", "progzonlymusic", "medical", "greece", "asoiaf", "osureport", "nvidia", "reddeadredemption", "Twitch", "MouseReview", "TowerOfFantasy", "Insurance", "IBO", "lexapro", "hometheater", "Epilepsy", "explainlikeimfive", "Nanny", "writing", "thinkpad", "WouldYouRather", "webdev", "Target", "crochet"])

def is_valid_post(post):
    if post.get('subreddit') not in WHITELIST_SUBREDDITS:
        return False
    
    # Check if post has required fields and isn't deleted/removed/NSFW
    if not (post.get('self_text') and 
            post['self_text'].strip() != '' and 
            post.get('over_18') != 'true'):
        return False
    
    # Check for banned keywords in all text fields
    for value in post.values():
        if isinstance(value, str):
            text = value.lower()
            if any(keyword in text for keyword in BANNED_KEYWORDS):
                return False
    
    return True

def process_csv_files():
    archive_dir = Path('data/archive')
    output_file = './data/posts.csv'
    
    # Get all CSV files in the archive directory
    csv_files = sorted(archive_dir.glob('*.csv'))
    
    if not csv_files:
        print("No CSV files found in archive directory")
        return
    
    # Get fieldnames from first file
    with open(csv_files[0], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
    
    # Process all files
    total_posts = 0
    filtered_posts = 0
    
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for csv_file in csv_files[:1]: #! limit to 1 file 
            print(f"Processing {csv_file.name}...")
            
            with open(csv_file, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                
                for post in reader:
                    total_posts += 1
                    if is_valid_post(post):
                        writer.writerow(post)
                        filtered_posts += 1
                    
                    # Print progress every 100,000 posts
                    if total_posts % 100000 == 0:
                        print(f"Processed {total_posts:,} posts, kept {filtered_posts:,} posts")
    
    print(f"\nProcessing complete!")
    print(f"Total posts processed: {total_posts:,}")
    print(f"Posts kept after filtering: {filtered_posts:,}")
    print(f"Posts filtered out: {total_posts - filtered_posts:,}")
    print(f"Output saved to: {output_file}")

if __name__ == '__main__':
    process_csv_files() 