from configs.path_config import TEXT_PATH, IMAGE_PATH

SCHALE_URL = "https://lonqie.github.io/SchaleDB/"
MIRROR_SCHALE_URL = "http://schale.lgc2333.top/"
BAWIKI_DB_URL = "https://bawiki.lgc2333.top/"
RES_PATH = IMAGE_PATH / "BAWiki"
DATA_PATH = TEXT_PATH / "BAWiki"

if not DATA_PATH.exists():
    DATA_PATH.mkdir(parents=True)
