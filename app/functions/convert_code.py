import csv
from config.default import BASE_DIR
from app.utils.types import MapZoomLevel

PLACE_CODE = {
    "MT1":"대형마트", 
    "CS2":"편의점", 
    "PS3":"어린이집 및 유치원", 
    "SC4":"학교", 
    "AC5":"학원", 
    "PK6":"주차장", 
    "OL7":"주유소 및 충전소", 
    "SW8":"지하철역", 
    "BK9":"은행",
    "CT1":"문화시설",
    "AG2":"중개업소",
    "PO3":"공공기관",
    "AT4":"관광명소",
    "AD5":"숙박",
    "FD6":"음식점",
    "CE7":"카페",
    "HP8":"병원",
    "PM9":"약국"
}

def code2regstr(code: str):
    with open(BASE_DIR + "/data/RegstrSeCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))
    for d in csv_mapping:
        if d["code"] == code:
            return d["kr-name"]

def code2lndcgr(code: str):
    with open(BASE_DIR + "/data/LandCgrCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))
    for d in csv_mapping:
        if d["code"] == code:
            return d["kr-name"]

def code2zoning(code: str):
    with open(BASE_DIR + "/data/LandZoningCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))
    for d in csv_mapping:
        if d["code"] == code:
            return d["kr-name"]

def code2landcategory(code: str):
    with open(BASE_DIR + "/data/LandCategoryCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))
    for d in csv_mapping:
        if d["code"] == code:
            return d["kr-name"]
        
def code2tpgrphfrm(code: str):
    with open(BASE_DIR + "/data/TpgrphFrmCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))
    for d in csv_mapping:
        if d["code"] == code:
            return d["kr-name"]

def code2tpgrphhg(code: str):
    with open(BASE_DIR + "/data/TpgrphHgCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))
    for d in csv_mapping:
        if d["code"] == code:
            return d["kr-name"]

def code2roadside(code: str):
    with open(BASE_DIR + "/data/RoadSideCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))
    for d in csv_mapping:
        if d["code"] == code:
            return d["kr-name"]

def code2placename(code: str):
    with open(BASE_DIR + "/data/PlaceCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))
    for d in csv_mapping:
        if d["code"] == code:
            return d["kr-name"]
        
def code2useplan(code: str):
    with open(BASE_DIR +"/data/LandUsePlanCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))
    for d in csv_mapping:
        if d["code"] == code[0:6]:
            if code[7] == "1":
                return d["kr-name"] + "<포함>"
            if code[7] == "2":
                return d["kr-name"] + "<저촉>"
            if code[7] == "3":
                return d["kr-name"] + "<접함>"

def code2addr(code:str, scale=0):
    """

        Params:
            code `str`:
                토지 코드 (2자리: 시도, 5자리: 시도 시군구, 8자리: 시도 시군구 읍면동, 19자리: 전체 주소)
            scale `int` (default=0):
                주소 단위 (0: 전체, 1: 시도, 2: 시군구, 3: 읍면동)
    """
    with open(BASE_DIR + "/data/PnuCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))

    if scale == 0:
        if len(code) == 2:
            for d in csv_mapping:
                if d["code"][0:2] == code:
                    return f"{d['sido']}"
        elif len(code) == 5:
            for d in csv_mapping:
                if d["code"][0:5] == code:
                    return f"{d['sido']} {d['sigungu']}"
        elif len(code) == 8:
            for d in csv_mapping:
                if d["code"][0:8] == code:
                    return f"{d['sido']} {d['sigungu']} {d['eupmyeondong']}"
        elif len(code) == 19:
            for d in csv_mapping:
                if d["code"] == code[0:10]:
                    if code[10] == "1":
                        m = ""
                    else:
                        m = "산"
                    main_n = int(code[11:15])
                    sub_n = int(code[15:19])
                    n = f"{main_n}-{sub_n}" if sub_n != 0 else f"{main_n}"
                    if d["donglee"] != "":
                        return f"{d['sido']} {d['sigungu']} {d['eupmyeondong']} {d['donglee']} {m}{n}"
                    else:
                        return f"{d['sido']} {d['sigungu']} {d['eupmyeondong']} {m}{n}"
    else:
        for d in csv_mapping:
            if d["code"] == code[0:10]:
                sido = d["sido"]
                sigungu = d["sigungu"]
                eupmyeondong = d["eupmyeondong"]
                if scale in MapZoomLevel.LOW:
                    return sido
                elif scale in MapZoomLevel.MEDIUM:
                    return sigungu
                else:
                    return eupmyeondong
    return None

def code2addr_dict(code:str):
    """

        Params:
            code `str`:
                토지 코드 (2자리: 시도, 5자리: 시도 시군구, 8자리: 시도 시군구 읍면동, 19자리: 전체 주소)
            scale `int` (default=0):
                주소 단위 (0: 전체, 1: 시도, 2: 시군구, 3: 읍면동)
    """
    with open(BASE_DIR + "/data/PnuCode.csv") as data:
        csv_mapping = list(csv.DictReader(data))

    addr_dict = {}

    if len(code) == 5:
        for d in csv_mapping:
            if d["code"][0:5] == code:
                addr_dict["sido"] = d["sido"]
                addr_dict["sigungu"] = d["sigungu"]
                addr_dict["address"] = f"{d['sido']} {d['sigungu']}"
                break
    elif len(code) == 19:
        for d in csv_mapping:
            if d["code"] == code[0:10]:
                if code[10] == "1":
                    m = ""
                else:
                    m = "산"
                main_n = int(code[11:15])
                sub_n = int(code[15:19])
                n = f"{main_n}-{sub_n}" if sub_n != 0 else f"{main_n}"
                if d["donglee"] != "":
                    addr_dict["sido"] = d["sido"]
                    addr_dict["sigungu"] = d["sigungu"]
                    addr_dict["eupmyeondong"] = d["eupmyeondong"]
                    addr_dict["donglee"] = d["donglee"]
                    addr_dict["detail"] = f"{m}{n}"
                    addr_dict["address"] = f"{d['sido']} {d['sigungu']} {d['eupmyeondong']} {d['donglee']} {m}{n}"
                else:
                    addr_dict["sido"] = d["sido"]
                    addr_dict["sigungu"] = d["sigungu"]
                    addr_dict["eupmyeondong"] = d["eupmyeondong"]
                    addr_dict["detail"] = f"{m}{n}"
                    addr_dict["address"] = f"{d['sido']} {d['sigungu']} {d['eupmyeondong']} {m}{n}"
    return addr_dict

def addr2code(addr:str):
    '''주소를 PNU 코드로 변경해주는 코드.

        Args:
            addr `str`: 토지의 지번 주소
        
        Returns:
            `str`: 19자리 PNU 코드
    '''
    # 주소를 법정동코드로 변환하기 위한 pnu_code.csv 파일
    with open(BASE_DIR +"/data/PnuCode.csv", "r") as pnu_f:
        pnu_reader = pnu_f.readlines()
    pnuDict = {}
    for i in range(len(pnu_reader)):
        if i != 0:
            pnu_split = pnu_reader[i].split(',')
            for i in range(len(pnu_split)):
                if i == 0:
                    addr_str = ''
                    continue
                addr_str += pnu_split[i] + ' '
            addr_str = addr_str.replace('\n ', '')
            addr_str = addr_str.rstrip(' ')
            pnuDict[addr_str] = pnu_split[0]
    addr_split = addr.split(' ')    # 공백을 기준으로 주소 분류
    addr_main = ''                  # 시/도, 시/군/구, 읍/면/동
    addr_sub_code = ''              # 지번
    for j in range(len(addr_split)):
        if j == len(addr_split) - 1:
            if addr_split[j][0] == '산':        # 필지가 산일 경우
                addr_split[j] = addr_split[j].lstrip('산')
                addr_sub_code += '2'
            elif addr_split[j][0] != '산':      # 필지가 일반일 경우
                addr_sub_code += '1'
            if len(addr_split[j].split('-')) == 2:  # 만일 부번이 있을 경우
                addr_sub_code += addr_split[j].split('-')[0].zfill(4)
                addr_sub_code += addr_split[j].split('-')[1].zfill(4)
            else:                                   # 부번이 없을 경우(본번만 있을 경우)
                addr_sub_code += addr_split[j].split('-')[0].zfill(4)
                addr_sub_code += '0000'
            break;
        else:
            addr_main += str(addr_split[j]) + ' '
    addr_main = addr_main.rstrip(' ')
    pnu = pnuDict[addr_main] + addr_sub_code
    return pnu