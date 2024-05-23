from config.default import *
import os

# API Keys
LAND_API_KEY = os.getenv("LAND_API_KEY", "default_api_key")
LAND_TRADE_API_KEY = os.getenv("LAND_TRADE_API_KEY", "default_api_key")
ECOS_API_KEY = os.getenv("ECOS_API_KEY", "default_api_key")
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY", "default_api_key")
VWORLD_API_KEY = os.getenv("VWORLD_API_KEY", "default_api_key")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "default_api_key")

def create_land_price_url(a, b, c, d, clat, clng):
    url = f"https://www.disco.re/home/hello/?a={a}&b={b}&c={c}&d={d}&clat={clat}&clng={clng}&mlv=3&mt=0&at=1&ct=1&st=1&h=1000000&i=1&j=1&k=2000&l=2022&m=0&n=99999999999&o=0&p=0&q=0&current=0&sale_first=false"
    return url
