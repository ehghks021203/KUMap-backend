import requests
import xmltodict
import json

def _calc_date(year: int, month: int) -> tuple:
    if month == 1:
        return year - 1, 12
    else:
        return year, month - 1

class GetGeometryDataAPI():
    # 요청 파라미터 (변동되지 않음)
    service = "data"
    req = "GetFeature"
    page = 1
    size = 1000

    def __init__(self, key: str) -> None:
        self.key = key
    
    # 엔드포인트
    endpoint = "http://api.vworld.kr/req/data"
    def get_data(self, pnu):
        if len(pnu) == 19:
            data = "LP_PA_CBND_BUBUN"
            attrFilter = f"pnu:=:{pnu}"
        elif len(pnu) == 5:
            data = "LT_C_ADEMD_INFO"
            attrFilter = f"emd_cd:LIKE:{pnu}"
        elif len(pnu) == 2:
            data = "LT_C_ADSIGG_INFO"
            attrFilter = f"sig_cd:LIKE:{pnu}"
        
        url = f"{self.endpoint}?service={self.service}&request={self.req}&data={data}&key={self.key}&attrFilter={attrFilter}&page={self.page}&size={self.size}"
        response = json.loads(requests.get(url).text)
        if (response["response"]["status"] == "NOT_FOUND"):
            return None
        else:
            return response["response"]["result"]["featureCollection"]

class LandFeatureAPI():
    url = "https://api.vworld.kr/ned/data/getLandCharacteristics"
    def __init__(self, key: str) -> None:
        self.default_params = {
            "key": key,
            "format": "json",
            "numOfRows": "100",
            "pageNo": "1"
        }
    
    def get_data(self, pnu: str, year: int, assorted=False):
        params = {"pnu":pnu,"stdrYear":year}
        params.update(self.default_params)
        response = requests.get(self.url, params=params).json()
        if "landCharacteristicss" in response:
            if assorted:
                return response["landCharacteristicss"]["field"]
            else:
                return response["landCharacteristicss"]["field"][0]
        else:
            if year < 2015:
                return None
            else:
                return self.get_data(pnu, year-1, assorted)

class LandTradeAPI():
    url = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcLandTrade"
    def __init__(self, key: str) -> None:
        self.default_params = {
            "serviceKey": key,
            "numOfRows": "100",
            "pageNo": "1"
        }
    
    def get_data(self, pnu: str, year: int, month: int):
        params = {"LAWD_CD":pnu,"DEAL_YMD":f"{year:04d}{month:02d}"}
        params.update(self.default_params)
        response = xmltodict.parse(requests.get(self.url, params=params).text)
        if response["response"]["header"]["resultCode"] == "00":
            if response["response"]["body"]["totalCount"] == "0":
                return None
            else:
                return response["response"]["body"]["items"]["item"]
        
class LandUsePlanAPI():
    url = "https://api.vworld.kr/ned/data/getLandUseAttr"
    def __init__(self, key: str) -> None:
        self.default_params = {
            "key": key,
            "format": "json",
            "numOfRows": "100",
            "pageNo": "1"
        }
    
    def get_data(self, pnu: str, return2name=False):
        params = {"pnu":pnu}
        params.update(self.default_params)
        response = requests.get(self.url, params=params).json()
        print(response)
        if "landUses" in response:
            datas = response["landUses"]["field"]
            land_use_plan_list = []
            if not return2name:
                for d in datas:
                    land_use_plan_list.append("{}({})".format(d["prposAreaDstrcCode"], d["cnflcAt"]))
                land_use_plan_list = list(set(land_use_plan_list))
            else:
                for d in datas:
                    land_use_plan_list.append("{}({})".format(d["prposAreaDstrcCodeNm"], d["cnflcAtNm"]))
                land_use_plan_list = list(set(land_use_plan_list))
            land_use_plan_str = ""
            for l in land_use_plan_list:
                land_use_plan_str += l + "/"
            return land_use_plan_str[:-1]
        else:
            return None
    
class FluctuationRateOfLandPriceAPI():
    by_region_url = "https://api.vworld.kr/ned/data/getByRegion"
    by_large_region_url = "https://api.vworld.kr/ned/data/getLargeCLByRegion"
    def __init__(self, key: str) -> None:
        self.default_params = {
            "key": key,
            "format": "json",
            "numOfRows": "100",
            "pageNo": "1",
            "scopeDiv": "A"
        }
    
    def get_data_by_region(self, ld_code: str, year: int, month: int):
        params = {"reqLdCode":ld_code,"stdrYear":year, "stdrMt": f"{month:02d}"}
        params.update(self.default_params)
        response = requests.get(self.by_region_url, params=params).json()
        if "byRegions" in response:
            return response["byRegions"]["field"][0]
        else:
            if year < 2015:
                return None
            else:
                _year, _month = _calc_date(year, month)
                return self.get_data_by_region(ld_code, _year, _month)
    
    def get_data_by_large_region(self, ld_code: str, year: int, month: int):
        params = {"stdrYear":year, "stdrMt": f"{month:02d}"}
        params.update(self.default_params)
        response = requests.get(self.by_large_region_url, params=params).json()
        if "byRegions" in response:
            for data in response["byRegions"]["field"]:
                if data["ldCtprvnCode"] == ld_code[0:2]:
                    return data
        else:
            if year < 2015:
                return None
            else:
                _year, _month = _calc_date(year, month)
                return self.get_data_by_large_region(ld_code, _year, _month)
    
class ProducerPriceIndexAPI():
    url = "https://ecos.bok.or.kr/api/StatisticSearch"
    def __init__(self, key: str) -> None:
        self.url += f"/{key}/json/kr/1/100/404Y014/M"

    def get_data(self, year: int, month: int):
        response = requests.get(f"{self.url}/{year:04d}{month:02d}/{year:04d}{month:02d}/*AA/?/?/?").json()
        if "StatisticSearch" in response:
            return float(response["StatisticSearch"]["row"][0]["DATA_VALUE"])
        else:
            if year < 2015:
                return None
            else:
                _year, _month = _calc_date(year, month)
                return self.get_data(_year, _month)

class ConsumerPriceIndexAPI():
    url = "https://ecos.bok.or.kr/api/StatisticSearch"
    def __init__(self, key: str) -> None:
        self.url += f"/{key}/json/kr/1/100/901Y009/M"

    def get_data(self, year: int, month: int):
        response = requests.get(f"{self.url}/{year:04d}{month:02d}/{year:04d}{month:02d}/0/?/?/?").json()
        if "StatisticSearch" in response:
            return float(response["StatisticSearch"]["row"][0]["DATA_VALUE"])
        else:
            if year < 2015:
                return None
            else:
                _year, _month = _calc_date(year, month)
                return self.get_data(_year, _month)
        