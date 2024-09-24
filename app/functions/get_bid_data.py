import requests
import datetime
from bs4 import BeautifulSoup
from urllib import parse
import json
import pytz
from app.functions.convert_code import addr2code, code2addr_dict
from app.functions.pnu_geolocation_lookup import get_word

def _bid_case_init() -> dict:
    """bid list initialize
    """
    return {
        "case_cd": "",
        "case_nm": "",
        "obj_nm": "",
        "case_zoning": "",
        "appraisal_price": "",
        "min_sale_price": "",
        "bid_type": "",
        "bid_date": "",
        "court_in_charge": "",
        "court_detail": "",
        "case_reception": "",
        "bid_start_date": "",
        "div_request_deadline": "",
        "billable_amount": "",
        "date_list": [],
        "land_list": [],
    }

def _bid_land_init():
    """bid land list initialize
    """
    return {
        "case_cd": "",
        "obj_nm": "",
        "court_in_charge": "",
        "pnu": "",
        "addr": "",
        "detail": "",
    }


def get_bid_list_data(sido_cd:str, sigungu_cd=""):
    # Error: 법원경매 홈페이지 점검
    if 1 <= datetime.datetime.now(pytz.timezone('Asia/Seoul')).time().hour < 6:
        return None
    cookies = {
        'WMONID': '56UORLUn-SV',
        'JSESSIONID': 'OEGBjL5iVuF4JkrHRavlapSuHeJ8yeNua96SAkbg1n4b6rxdzyRj7bbOYslW4Fzo.amV1c19kb21haW4vYWlzMQ==',
        'daepyoSidoCd': '11',
        'daepyoSiguCd': '680',
        'mvmPlaceSidoCd': '',
        'mvmPlaceSiguCd': '',
        'rd1Cd': '',
        'rd2Cd': '',
        'realVowel': '35207_45207',
        'roadPlaceSidoCd': '',
        'roadPlaceSiguCd': '',
        'vowelSel': '35207_45207',
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8,ko-KR;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        # 'Cookie': 'WMONID=56UORLUn-SV; JSESSIONID=OEGBjL5iVuF4JkrHRavlapSuHeJ8yeNua96SAkbg1n4b6rxdzyRj7bbOYslW4Fzo.amV1c19kb21haW4vYWlzMQ==; daepyoSidoCd=11; daepyoSiguCd=680; mvmPlaceSidoCd=; mvmPlaceSiguCd=; rd1Cd=; rd2Cd=; realVowel=35207_45207; roadPlaceSidoCd=; roadPlaceSiguCd=; vowelSel=35207_45207',
        'Origin': 'https://www.courtauction.go.kr',
        'Referer': 'https://www.courtauction.go.kr/InitMulSrch.laf',
        'Sec-Fetch-Dest': 'frame',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    start_dt = datetime.datetime.now()
    end_dt = start_dt + datetime.timedelta(days=31)
    start_dt = start_dt.strftime('%Y.%m.%d')
    end_dt = end_dt.strftime('%Y.%m.%d')
    end_dt = "2024.07.13"

    data = f"bubwLocGubun=2&jiwonNm=%BC%AD%BF%EF%C1%DF%BE%D3%C1%F6%B9%E6%B9%FD%BF%F8&jpDeptCd=000000&daepyoSidoCd={sido_cd}&daepyoSiguCd={sigungu_cd}&daepyoDongCd=&rd1Cd=&rd2Cd=&realVowel=35207_45207&rd3Rd4Cd=&notifyRealRoad=on&saYear=2024&saSer=&ipchalGbncd=&termStartDt={start_dt}&termEndDt={end_dt}&lclsUtilCd=0000801&mclsUtilCd=&sclsUtilCd=&gamEvalAmtGuganMin=&gamEvalAmtGuganMax=&notifyMinMgakPrcMin=&notifyMinMgakPrcMax=&areaGuganMin=&areaGuganMax=&yuchalCntGuganMin=&yuchalCntGuganMax=&notifyMinMgakPrcRateMin=&notifyMinMgakPrcRateMax=&srchJogKindcd=&mvRealGbncd=00031R&srnID=PNO102001&_NAVI_CMD=&_NAVI_SRNID=&_SRCH_SRNID=PNO102001&_CUR_CMD=InitMulSrch.laf&_CUR_SRNID=PNO102001&_NEXT_CMD=RetrieveRealEstMulDetailList.laf&_NEXT_SRNID=PNO102002&_PRE_SRNID=&_LOGOUT_CHK=&_FORM_YN=Y"
    response = requests.post(
        'https://www.courtauction.go.kr/RetrieveRealEstMulDetailList.laf',
        cookies=cookies,
        headers=headers,
        data=data,
    )

    html = BeautifulSoup(str(response.text), 'html.parser')
    print(html)
    total_count = int(html.select("li.txtblue")[0].text.split(":")[1].lstrip(" ").rstrip("건]"))
    current_case_idx = 0
    bid_case_list = []
    for select_type in ["tr.Ltbl_list_lvl0", "tr.Ltbl_list_lvl1"]:
        current_case_idx += 1
        case_html = html.select(select_type)
        for c in case_html:
            is_only_land = True     # 경매 목록에 오로지 토지만 존재하는지 체크
            bid_case = _bid_case_init()
            bid_land_list = []
            case_obj = c.select("td")

            # 사건번호
            bid_case["case_cd"] = str(case_obj[0]).split(",")[1]
            # 물건번호
            bid_case["obj_nm"] = str(case_obj[0]).split(",")[2].rstrip('"/></td>')
            # 담당
            bid_case["court_in_charge"] = str(case_obj[0]).split(",")[0].lstrip('<td class="padding0"><input name="chk" type="checkbox" value="')
            # 토지 매물 목록 조회
            land_list = c.select("div.tbl_btm_line")
            for i in range(len(land_list)):
                if i == 0:
                    bid_land = _bid_land_init()
                    first_land = c.select("div.tbl_btm_noline")
                    first_land_str = first_land[0].text.replace("\t","").replace("\n","").replace("\r","")
                    first_land_str = ' '.join(first_land_str.split())
                    if first_land_str.split("[")[1][0:2] != "토지":
                        is_only_land = False
                        break
                    bid_land["case_cd"] = bid_case["case_cd"]
                    bid_land["obj_nm"] = bid_case["obj_nm"]
                    bid_land["court_in_charge"] = bid_case["court_in_charge"]
                    bid_land["addr"] = first_land_str.split("[")[0].rstrip(" ")
                    bid_land["pnu"] = addr2code(bid_land["addr"])
                    bid_land["detail"] = first_land_str.split("[")[1][3:].rstrip("]")
                    bid_land["area"] = float(bid_land["detail"].split(" ")[1].split("㎡")[0])
                    bid_land_list.append(bid_land)
                if i == len(land_list) - 2:
                    break
                bid_land = _bid_land_init()
                land_list_str = land_list[i].text.replace("\t","").replace("\n","").replace("\r","")
                land_list_str = " ".join(land_list_str.split())
                if land_list_str.split("[")[1][0:2] != "토지":
                    is_only_land = False
                    break;
                bid_land["case_cd"] = bid_case["case_cd"]
                bid_land["obj_nm"] = bid_case["obj_nm"]
                bid_land["court_in_charge"] = bid_case["court_in_charge"]
                bid_land["addr"] = land_list_str.split("[")[0].rstrip(" ")
                bid_land["pnu"] = addr2code(bid_land["addr"])
                bid_land["detail"] = land_list_str.split("[")[1][3:].rstrip("]")
                bid_land["area"] = float(bid_land["detail"].split(" ")[1].split("㎡")[0])
                bid_land_list.append(bid_land)
            if not is_only_land:
                continue

            # 경매 상세 내역 페이지
            bid_case = get_bid_case_data(bid_case["court_in_charge"], bid_case["case_cd"], bid_case["obj_nm"])
            # 토지 내역 리스트
            land_list = []
            for l in bid_land_list:
                land_list.append({'pnu':l['pnu'], 'addr':l['addr']})
            bid_case['land_list'] = json.dumps(land_list, ensure_ascii=False)
            bid_case_list.append(bid_case)

    return bid_case_list

def get_bid_land_list_data(sido_cd:str, sigungu_cd=""):
    # Error: 법원경매 홈페이지 점검
    if 1 <= datetime.datetime.now(pytz.timezone('Asia/Seoul')).time().hour < 6:
        return None
    cookies = {
        'WMONID': '56UORLUn-SV',
        'JSESSIONID': 'OEGBjL5iVuF4JkrHRavlapSuHeJ8yeNua96SAkbg1n4b6rxdzyRj7bbOYslW4Fzo.amV1c19kb21haW4vYWlzMQ==',
        'daepyoSidoCd': '11',
        'daepyoSiguCd': '680',
        'mvmPlaceSidoCd': '',
        'mvmPlaceSiguCd': '',
        'rd1Cd': '',
        'rd2Cd': '',
        'realVowel': '35207_45207',
        'roadPlaceSidoCd': '',
        'roadPlaceSiguCd': '',
        'vowelSel': '35207_45207',
    }
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8,ko-KR;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        # 'Cookie': 'WMONID=56UORLUn-SV; JSESSIONID=OEGBjL5iVuF4JkrHRavlapSuHeJ8yeNua96SAkbg1n4b6rxdzyRj7bbOYslW4Fzo.amV1c19kb21haW4vYWlzMQ==; daepyoSidoCd=11; daepyoSiguCd=680; mvmPlaceSidoCd=; mvmPlaceSiguCd=; rd1Cd=; rd2Cd=; realVowel=35207_45207; roadPlaceSidoCd=; roadPlaceSiguCd=; vowelSel=35207_45207',
        'Origin': 'https://www.courtauction.go.kr',
        'Referer': 'https://www.courtauction.go.kr/InitMulSrch.laf',
        'Sec-Fetch-Dest': 'frame',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    start_dt = datetime.datetime.now()
    end_dt = start_dt + datetime.timedelta(days=31)
    start_dt = start_dt.strftime('%Y.%m.%d')
    end_dt = end_dt.strftime('%Y.%m.%d')
    end_dt = "2024.07.13"

    data = f"bubwLocGubun=2&jiwonNm=%BC%AD%BF%EF%C1%DF%BE%D3%C1%F6%B9%E6%B9%FD%BF%F8&jpDeptCd=000000&daepyoSidoCd={sido_cd}&daepyoSiguCd={sigungu_cd}&daepyoDongCd=&rd1Cd=&rd2Cd=&realVowel=35207_45207&rd3Rd4Cd=&notifyRealRoad=on&saYear=2024&saSer=&ipchalGbncd=&termStartDt={start_dt}&termEndDt={end_dt}&lclsUtilCd=0000801&mclsUtilCd=&sclsUtilCd=&gamEvalAmtGuganMin=&gamEvalAmtGuganMax=&notifyMinMgakPrcMin=&notifyMinMgakPrcMax=&areaGuganMin=&areaGuganMax=&yuchalCntGuganMin=&yuchalCntGuganMax=&notifyMinMgakPrcRateMin=&notifyMinMgakPrcRateMax=&srchJogKindcd=&mvRealGbncd=00031R&srnID=PNO102001&_NAVI_CMD=&_NAVI_SRNID=&_SRCH_SRNID=PNO102001&_CUR_CMD=InitMulSrch.laf&_CUR_SRNID=PNO102001&_NEXT_CMD=RetrieveRealEstMulDetailList.laf&_NEXT_SRNID=PNO102002&_PRE_SRNID=&_LOGOUT_CHK=&_FORM_YN=Y"

    response = requests.post(
        'https://www.courtauction.go.kr/RetrieveRealEstMulDetailList.laf',
        cookies=cookies,
        headers=headers,
        data=data,
    )

    html = BeautifulSoup(str(response.text), 'html.parser')
    # print(html)
    total_count = int(html.select("li.txtblue")[0].text.split(":")[1].lstrip(" ").rstrip("건]"))
    current_case_idx = 0
    total_bid_land_list = []
    for select_type in ["tr.Ltbl_list_lvl0", "tr.Ltbl_list_lvl1"]:
        current_case_idx += 1
        case_html = html.select(select_type)
        for c in case_html:
            is_only_land = True     # 경매 목록에 오로지 토지만 존재하는지 체크
            bid_case = _bid_case_init()
            case_obj = c.select("td")
            bid_land_list = []
            # 사건번호
            bid_case["case_cd"] = str(case_obj[0]).split(",")[1]
            # 물건번호
            bid_case["obj_nm"] = str(case_obj[0]).split(",")[2].rstrip('"/></td>')
            # 담당
            bid_case["court_in_charge"] = str(case_obj[0]).split(",")[0].lstrip('<td class="padding0"><input name="chk" type="checkbox" value="')
            # 토지 매물 목록 조회
            land_list = c.select("div.tbl_btm_line")
            for i in range(len(land_list)):
                if i == 0:
                    bid_land = _bid_land_init()
                    first_land = c.select("div.tbl_btm_noline")
                    first_land_str = first_land[0].text.replace("\t","").replace("\n","").replace("\r","")
                    first_land_str = ' '.join(first_land_str.split())
                    if first_land_str.split("[")[1][0:2] != "토지":
                        is_only_land = False
                        break
                    pnu = addr2code(first_land_str.split("[")[0].rstrip(" "))
                    bid_land["case_cd"] = bid_case["case_cd"]
                    bid_land["obj_nm"] = bid_case["obj_nm"]
                    bid_land["court_in_charge"] = bid_case["court_in_charge"]
                    bid_land["addr"] = code2addr_dict(pnu)
                    bid_land["pnu"] = addr2code(bid_land["addr"]["address"])
                    bid_land["detail"] = first_land_str.split("[")[1][3:].rstrip("]")
                    bid_land["area"] = float(bid_land["detail"].split(" ")[1].split("㎡")[0])
                    bid_land_list.append(bid_land)
                if i == len(land_list) - 2:
                    break
                bid_land = _bid_land_init()
                land_list_str = land_list[i].text.replace("\t","").replace("\n","").replace("\r","")
                land_list_str = " ".join(land_list_str.split())
                if land_list_str.split("[")[1][0:2] != "토지":
                    is_only_land = False
                    break
                pnu = addr2code(land_list_str.split("[")[0].rstrip(" "))
                bid_land["case_cd"] = bid_case["case_cd"]
                bid_land["obj_nm"] = bid_case["obj_nm"]
                bid_land["court_in_charge"] = bid_case["court_in_charge"]
                bid_land["addr"] = code2addr_dict(pnu)
                bid_land["pnu"] = addr2code(bid_land["addr"]["address"])
                bid_land["detail"] = land_list_str.split("[")[1][3:].rstrip("]")
                bid_land["area"] = float(bid_land["detail"].split(" ")[1].split("㎡")[0])
                bid_land_list.append(bid_land)
            if not is_only_land:
                continue
            total_bid_land_list.extend(bid_land_list)
    return total_bid_land_list

def get_bid_case_data(court_in_charge: str, case_cd: str, obj_nm: str):
    # Error: 법원경매 홈페이지 점검
    if 1 <= datetime.datetime.now(pytz.timezone('Asia/Seoul')).time().hour < 6:
        return None
    cookies = {
        'WMONID': '56UORLUn-SV',
        'JSESSIONID': 'OEGBjL5iVuF4JkrHRavlapSuHeJ8yeNua96SAkbg1n4b6rxdzyRj7bbOYslW4Fzo.amV1c19kb21haW4vYWlzMQ==',
        'daepyoSidoCd': '11',
        'daepyoSiguCd': '680',
        'mvmPlaceSidoCd': '',
        'mvmPlaceSiguCd': '',
        'rd1Cd': '',
        'rd2Cd': '',
        'realVowel': '35207_45207',
        'roadPlaceSidoCd': '',
        'roadPlaceSiguCd': '',
        'vowelSel': '35207_45207',
    }
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8,ko-KR;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        # 'Cookie': 'WMONID=56UORLUn-SV; JSESSIONID=OEGBjL5iVuF4JkrHRavlapSuHeJ8yeNua96SAkbg1n4b6rxdzyRj7bbOYslW4Fzo.amV1c19kb21haW4vYWlzMQ==; daepyoSidoCd=11; daepyoSiguCd=680; mvmPlaceSidoCd=; mvmPlaceSiguCd=; rd1Cd=; rd2Cd=; realVowel=35207_45207; roadPlaceSidoCd=; roadPlaceSiguCd=; vowelSel=35207_45207',
        'Origin': 'https://www.courtauction.go.kr',
        'Referer': 'https://www.courtauction.go.kr/InitMulSrch.laf',
        'Sec-Fetch-Dest': 'frame',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    bid_case = _bid_case_init()
    # 사건번호
    bid_case["case_cd"] = case_cd
    # 물건번호
    bid_case["obj_nm"] = obj_nm
    # 담당
    bid_case["court_in_charge"] = court_in_charge

    # 경매 상세 내역 페이지
    detail_data = f"jiwonNm={parse.quote(court_in_charge, encoding='euc-kr')}&saNo={case_cd}&maemulSer={obj_nm}&mokmulSer=&_NAVI_CMD=InitMulSrch.laf&_NAVI_SRNID=PNO102001&_SRCH_SRNID=PNO102001&_CUR_CMD=RetrieveRealEstMulDetailList.laf&_CUR_SRNID=PNO102002&_NEXT_CMD=RetrieveRealEstCarHvyMachineMulDetailInfo.laf&_NEXT_SRNID=PNO102015&_PRE_SRNID=&_LOGOUT_CHK=&_FORM_YN=Y&_C_bubwLocGubun=1&_C_jiwonNm=%BC%AD%BF%EF%C1%DF%BE%D3%C1%F6%B9%E6%B9%FD%BF%F8&_C_jpDeptCd=000000&_C_daepyoSidoCd=&_C_daepyoSiguCd=&_C_daepyoDongCd=&_C_notifyLoc=on&_C_rd1Cd=&_C_rd2Cd=&_C_realVowel=35207_45207&_C_rd3Rd4Cd=&_C_notifyRealRoad=on&_C_saYear=2023&_C_saSer=&_C_ipchalGbncd=&_C_termStartDt=&_C_termEndDt=&_C_lclsUtilCd=&_C_mclsUtilCd=&_C_sclsUtilCd=&_C_gamEvalAmtGuganMin=&_C_gamEvalAmtGuganMax=&_C_notifyMinMgakPrcMin=&_C_notifyMinMgakPrcMax=&_C_areaGuganMin=&_C_areaGuganMax=&_C_yuchalCntGuganMin=&_C_yuchalCntGuganMax=&_C_notifyMinMgakPrcRateMin=&_C_notifyMinMgakPrcRateMax=&_C_srchJogKindcd=&_C_mvRealGbncd=00031R&_C_srnID=PNO102001"
    detail_response = requests.post(
        "https://www.courtauction.go.kr/RetrieveRealEstCarHvyMachineMulDetailInfo.laf",
        cookies=cookies,
        headers=headers,
        data=detail_data,
    )
    detail_html = BeautifulSoup(str(detail_response.text), "html.parser")
    case_detail = detail_html.select("table.Ltbl_dt")
    if case_detail == None:
        # 해당하는 사건 번호의 정보가 존재하지 않다는 것이기 때문에 패스
        return None

    # 물건기본정보의 사건번호 ... 담당 까지의 내용
    case_detail_elements = case_detail[0].select("tr td")
    for i in range(len(case_detail_elements)):
        # string 내에 있는 탭, 개행, 캐리지 리턴 제거
        case_detail_str = case_detail_elements[i].text.replace("\t","").replace("\n","").replace("\r","")
        if i == 0:          # 사건번호
            # non-breaking space 제거 및 사건번호만 표기해주기 위한 split 작업
            bid_case["case_nm"] = case_detail_str.replace(u"\xa0",u"").split("[")[0] 
        elif i == 2:        # 물건종류
            bid_case["land_zoning"] = case_detail_str
        elif i == 3:        # 감정평가액
            # 뒤에 있는 '원' 제거 및 쉼표 제거 후 Int 형변환
            bid_case["appraisal_price"] = int(case_detail_str.rstrip("원").replace(",",""))
        elif i == 4:        # 최저 매각 가격
            # 뒤에 있는 '원' 제거 및 쉼표 제거 후 Int 형변환
            bid_case["min_sale_price"] = int(case_detail_str.rstrip("원").replace(",",""))
        elif i == 5:        # 입찰방법
            bid_case["bid_type"] = case_detail_str
        elif i == 6:        # 매각기일
            bid_case["bid_date"] = case_detail_str
        elif i == (len(case_detail_elements) - 1):      # 담당 (맨 마지막 요소)
            # 공백 제거
            case_detail_str = case_detail_str.replace(" ", "")
            # '|'를 기준으로 담당 법원, 담당 팀 분류
            bid_case["court_in_charge"] = case_detail_str.split("|")[0]
            bid_case["court_detail"] = case_detail_str.split("|")[1]
            
    # 물건기본정보의 사건접수 ... 청구금액 까지의 내용
    case_detail_elements = case_detail[1].select("tr td")
    for i in range(len(case_detail_elements)):
        # string 내에 있는 탭, 개행, 캐리지 리턴 제거
        case_detail_str = case_detail_elements[i].text.replace("\t","").replace("\n","").replace("\r","")
        if i == 0:          # 사건접수
            bid_case["case_reception"] = case_detail_str
        elif i == 1:        # 경매개시일
            bid_case["bid_start_date"] = case_detail_str
        elif i == 2:        # 배당요구종기
            bid_case["div_request_deadline"] = case_detail_str.replace(" ", "")
        elif i == 3:        # 청구금액
            bid_case["billable_amount"] = case_detail_str.rstrip("원").replace(",", "")
            
    case_detail = detail_html.select("table.Ltbl_list")[0].select("tr")
    # 기일내역 리스트
    date_list = []
    for i in range(len(case_detail)):
        if i == 0:
            continue
        case_detail_elements = case_detail[i].select("td")
        date_dict = {}
        for j in range(len(case_detail_elements)):
            # string 내에 있는 탭, 개행, 캐리지 리턴 제거
            case_detail_str = case_detail_elements[j].text.replace("\t","").replace("\n","").replace("\r","")
            if j == 0:          # 기일
                date_dict["date"] = case_detail_str
            elif j == 1:        # 기일종류
                date_dict["type"] = case_detail_str
            elif j == 2:        # 기일장소
                date_dict["place"] = case_detail_str
            elif j == 3:        # 최저매각가격
                date_dict["min_sale_price"] = case_detail_str.rstrip("원").replace(",","")
            elif j == 4:        # 기일결과
                date_dict["result"] = case_detail_str.lstrip(" ")
        date_list.append(date_dict)
    bid_case["date_list"] = json.dumps(date_list, ensure_ascii=False)

    # 토지 목록 조회
    case_detail = detail_html.select("table.Ltbl_dt")[0].select("tr")
    land_list = []
    for i in range(4, len(case_detail) - 1):
        land = {}
        land["addr"] = case_detail[i].select("td")[0].text.replace("\t","").replace("\n","").replace("\r","").split(")")[1]
        land["addr"] = " ".join(land["addr"].split())
        land["pnu"] = addr2code(land["addr"])
        land["addr"] = code2addr_dict(land["pnu"])
        land["lat"], land["lng"] = get_word(land["addr"]["address"])
        land_list.append(land)
    bid_case["land_list"] = json.dumps(land_list, ensure_ascii=False)
    return bid_case


if __name__ == "__main__":
    #print(get_bid_land_list_data("11", "680"))
    get_bid_case_data("의정부지방법원", "20210130012080", "1")