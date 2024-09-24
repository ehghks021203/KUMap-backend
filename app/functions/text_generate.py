from app import db
from app.models.land import LandInfo
import app.functions.convert_code as cc
import app.functions.make_input_data as mid
from app.functions.api import LandFeatureAPI, LandTradeAPI
import xgboost as xgb
from app.functions.predict import pred
from config import model, api, default
import google.generativeai as genai
from datetime import datetime
import pytz
import os

def generate(target_pnu, predict_price):
    loaded_model = xgb.XGBRegressor()
    loaded_model.load_model(model.MODEL_PATH)

    genai.configure(api_key=api.GOOGLE_API_KEY)
    llm_model = genai.GenerativeModel('gemini-1.5-flash')

    land_info = LandInfo[target_pnu[0:2]].query.filter_by(pnu=target_pnu).first()
    if not land_info:
        return None
    target_year = datetime.now(pytz.timezone("Asia/Seoul")).year
    target_month = datetime.now(pytz.timezone("Asia/Seoul")).month
    target_x, target_predict = pred(target_pnu, target_year, target_month, return_all=True)

    land_info_str = "예측 평가액: ￦{:,d} ({:,d}원/㎡)\n\n".format(int(predict_price * float(target_x.iloc[0]["LndpclAr"])), int(predict_price))
    print(land_info_str)
    land_use_plan_str = ""
    place_info_str = "== 주변 상권 정보 ==\n"
    for k, v in target_x.iloc[0].items():
        if v == 0.0:
            continue
        if k[0:3] in cc.PLACE_CODE.keys():
            place_kr = cc.PLACE_CODE[k[0:3]]
            if len(k.split("_")) == 2:
                place_info_str += "{} 이내에 있는 {}의 수: {:,d}개\n".format(k.split("_")[1], place_kr, int(v))
            else:
                if v == 20000:
                    continue
                place_info_str += "{} 최소 거리: {:,d}m\n".format(place_kr, int(v))
        elif len(k.split("_")) == 2:
            if k.split("_")[0] == "LdCode":
                jibun = cc.code2addr(k.split("_")[1])
                land_info_str += f"지번주소: {jibun}\n"
            if k.split("_")[0] == "RegstrSe":
                re = cc.code2regstr(k.split("_")[1][2:3])
                land_info_str += f"필지: {re}\n"
            if k.split("_")[0] == "Lndcgr":
                lc = cc.code2lndcgr(k.split("_")[1][2:4])
                land_info_str += f"지목: {lc}\n"
            if k.split("_")[0] == "PrposArea1":
                a1 = cc.code2zoning(k.split("_")[1][2:4])
                land_info_str += f"용도지역: {a1}\n"
            if k.split("_")[0] == "LadUseSittn":
                us = cc.code2landcategory(k.split("_")[1][2:5])
                land_info_str += f"이용상황: {us}\n"
            if k.split("_")[0] == "TpgrphHg":
                th = cc.code2tpgrphhg(k.split("_")[1][2:4])
                land_info_str += f"토지지세: {th}\n"
            if k.split("_")[0] == "TpgrphFrm":
                tf = cc.code2tpgrphfrm(k.split("_")[1][2:4])
                land_info_str += f"토지형상: {tf}\n"
            if k.split("_")[0] == "TpgrphHg":
                rs = cc.code2roadside(k.split("_")[1][2:4])
                land_info_str += f"도로접면: {rs}\n"
            if k.split("_")[0] == "LandUsePlans":
                # print(k)
                if cc.code2useplan(k.split("_")[1]):
                    land_use_plan_str += cc.code2useplan(k.split("_")[1]) + ", "
        # print(f"- {k}: {v}")

    land_info_str += "토지면적: {:,}㎡\n".format(target_x.iloc[0]["LndpclAr"])
    land_info_str += "기준년도: {}년\n".format(target_x.iloc[0]["Year"])
    land_info_str += "기준월: {}월\n".format(target_x.iloc[0]["Month"])
    land_info_str += "개별공시지가: {:,d}원/㎡당\n".format(int(target_x.iloc[0]["PblntfPclnd"]))
    land_info_str += "지가지수: {}\n".format(target_x.iloc[0]["PclndIndex"])
    land_info_str += "지가변동률: {}%\n".format(target_x.iloc[0]["PclndChgRt"])
    land_info_str += "누계지가변동률: {}%\n".format(target_x.iloc[0]["AcmtlPclndChgRt"])
    land_info_str += "권역별지가지수: {}\n".format(target_x.iloc[0]["LargeClPclndIndex"])
    land_info_str += "권역별지가변동률: {}%\n".format(target_x.iloc[0]["LargeClPclndChgRt"])
    land_info_str += "권역별누계지가변동률: {}%\n".format(target_x.iloc[0]["LargeClAcmtlPclndChgRt"])
    land_info_str += "생산자물가지수: {}\n".format(target_x.iloc[0]["PPI"])
    land_info_str += "소비자물가지수: {}\n".format(target_x.iloc[0]["CPI"])

    land_info_str += f"이용계획: {land_use_plan_str[:-2]}"

    info_str = land_info_str + "\n\n" + place_info_str

    tree_text = ""
    tree_dump = loaded_model.get_booster().get_dump()
    for i, tree in enumerate(tree_dump):
        tree_text += f"Tree {i}:\n{tree}"

    lt_api = LandTradeAPI(api.LAND_TRADE_API_KEY)
    target_year = int(target_x.iloc[0]["Year"])
    target_month = int(target_x.iloc[0]["Month"])

    # Compare land data
    compare_land_trade = {}

    while True:
        result = lt_api.get_data(target_pnu[:5], target_year, target_month)
        if result == None:
            target_month -= 1
            if target_month == 0:
                target_month = 12
                target_year -= 1
            if target_year == 2000:
                break
            continue
        
        for r in result:
            if isinstance(r, dict):
                if r["지목"] == lc:
                    if r.get("용도지역") != None:
                        if r["용도지역"] == a1:
                            compare_land_trade = r
                            break
        if compare_land_trade != {}:
            break
        target_month -= 1
        if target_month == 0:
            target_month = 12
            target_year -= 1
        if target_year == 2013:
            break

    if compare_land_trade != {}:
        compare_pnu = cc.addr2code(f"{cc.code2addr(compare_land_trade['지역코드'])} {compare_land_trade['법정동']} {compare_land_trade['지번']}")
        lf_api = LandFeatureAPI(api.LAND_API_KEY)
        result = lf_api.get_data(compare_pnu[0:10], int(compare_land_trade["년"]), assorted=True)
        compare_land = None
        for r in result:
            if r["prposArea1Nm"] == compare_land_trade["용도지역"] and r["lndcgrCodeNm"] == compare_land_trade["지목"]:
                compare_land = r
                break
        if compare_land != None:
            compare_pnu = compare_land["pnu"]
            compare_date = compare_land_trade["년"] + compare_land_trade["월"].zfill(2)
            print("비교하고자 하는 토지 주소:", cc.code2addr(compare_pnu))
            print("기준년도:", compare_date)
            compare_land_feature = mid.make(compare_pnu, compare_date)

            compare_info_str = "토지 매매가: {:,f}원/㎡당\n\n".format(float(float(compare_land_trade["거래금액"].replace(",",""))*10000 / float(compare_land_trade['거래면적'].replace(',',''))))
            land_use_plan_str = ", ".join(
                [cc.code2useplan(item) for item in compare_land_feature["LandUsePlans"].split("/") if cc.code2useplan(item) is not None]
            )
            place_info_str = "== 주변 상권 정보 ==\n"
            for k, v in compare_land_feature.items():
                if k[0:3] in cc.PLACE_CODE.keys():
                    place_kr = cc.PLACE_CODE[k[0:3]]
                    if len(k.split("_")) == 2:
                        place_info_str += "{} 이내에 있는 {}의 수: {:,d}개\n".format(k.split("_")[1], place_kr, int(v))
                    else:
                        if v == 20000:
                            continue
                        place_info_str += "{} 최소 거리: {:,d}m\n".format(place_kr, int(v))
                        
            compare_info_str = f"""
            비교 토지 주소: {cc.code2addr(compare_land_trade['지역코드'])} {compare_land_trade['법정동']} {compare_land_trade['지번']}

            비교 토지의 거래가: ￦{int(float(compare_land_trade['거래금액'].replace(',',''))*10000):,d} ({int(float(compare_land_trade['거래금액'].replace(',',''))*10000 / float(compare_land_trade['거래면적'].replace(',',''))):,d}원/㎡)
            토지 매매 면적: 전체 면적 {float(compare_land_feature['LndpclAr']):,f}㎡ 중 {float(compare_land_trade['거래면적'].replace(',','')):,f}㎡

            필지: {cc.code2regstr(compare_land_feature['RegstrSe'][2:3])}
            지목: {cc.code2lndcgr(compare_land_feature['Lndcgr'][2:4])}
            용도지역: {cc.code2zoning(compare_land_feature['PrposArea1'][2:4])}
            이용상황: {cc.code2landcategory(compare_land_feature['LadUseSittn'][2:5])}
            토지지세: {cc.code2tpgrphhg(compare_land_feature['TpgrphHg'][2:4])}
            도로접면: {cc.code2roadside(compare_land_feature['RoadSide'][2:4])}
            토지형상: {cc.code2tpgrphfrm(compare_land_feature['TpgrphFrm'][2:4])}
            토지면적: {float(compare_land_feature['LndpclAr']):,}㎡
            기준년도: {compare_land_feature['Year']}년
            기준월: {compare_land_feature['Month']}월
            개별공시지가: {int(compare_land_feature['PblntfPclnd']):,}원/㎡당
            지가지수: {compare_land_feature['PclndIndex']}
            지가변동률: {compare_land_feature['PclndChgRt']}%
            누계지가변동률: {compare_land_feature['AcmtlPclndChgRt']}%
            권역별지가지수: {compare_land_feature['LargeClPclndIndex']}
            권역별지가변동률: {compare_land_feature['LargeClPclndChgRt']}%
            권역별누계지가변동률: {compare_land_feature['LargeClAcmtlPclndChgRt']}%
            생산자물가지수: {compare_land_feature['PPI']}
            소비자물가지수: {compare_land_feature['CPI']}
            이용계획: {land_use_plan_str}
                
            {place_info_str}
            """
        else:
            compare_info_str = "비교군 없음"
    else:
        compare_info_str = "비교군 없음"

    with open(os.path.join(default.BASE_DIR, "data", "prompt", "prompt.txt"), "r", encoding="utf-8") as file:
        prompt_template = file.read()
    prompt = prompt_template.format(
        land_address=cc.code2addr(target_pnu),
        info_str=info_str,
        tree_text=tree_text,
        compare_info_str=compare_info_str
    )
    llm_response = llm_model.generate_content(
        contents=prompt,
        request_options={"timeout": 1000}
    )
    return llm_response.text





def _generate(target_pnu, predict_price):
    loaded_model = xgb.XGBRegressor()
    loaded_model.load_model(model.MODEL_PATH)

    genai.configure(api_key=api.GOOGLE_API_KEY)
    llm_model = genai.GenerativeModel('gemini-1.5-flash')

    land_info = LandInfo[target_pnu[0:2]].query.filter_by(pnu=target_pnu).first()
    if not land_info:
        return None
    target_year = datetime.now(pytz.timezone("Asia/Seoul")).year
    target_month = datetime.now(pytz.timezone("Asia/Seoul")).month
    target_x, target_predict = pred(target_pnu, target_year, target_month, return_all=True)

    land_info_str = "예측 평가액: ￦{:,d} ({:,d}원/㎡)\n\n".format(int(predict_price * float(target_x.iloc[0]["LndpclAr"])), int(predict_price))
    print(land_info_str)
    land_use_plan_str = ""
    place_info_str = "== 주변 상권 정보 ==\n"
    for k, v in target_x.iloc[0].items():
        if v == 0.0:
            continue
        if k[0:3] in cc.PLACE_CODE.keys():
            place_kr = cc.PLACE_CODE[k[0:3]]
            if len(k.split("_")) == 2:
                place_info_str += "{} 이내에 있는 {}의 수: {:,d}개\n".format(k.split("_")[1], place_kr, int(v))
            else:
                if v == 20000:
                    continue
                place_info_str += "{} 최소 거리: {:,d}m\n".format(place_kr, int(v))
        elif len(k.split("_")) == 2:
            if k.split("_")[0] == "LdCode":
                jibun = cc.code2addr(k.split("_")[1])
                land_info_str += f"지번주소: {jibun}\n"
            if k.split("_")[0] == "RegstrSe":
                re = cc.code2regstr(k.split("_")[1][2:3])
                land_info_str += f"필지: {re}\n"
            if k.split("_")[0] == "Lndcgr":
                lc = cc.code2lndcgr(k.split("_")[1][2:4])
                land_info_str += f"지목: {lc}\n"
            if k.split("_")[0] == "PrposArea1":
                a1 = cc.code2zoning(k.split("_")[1][2:4])
                land_info_str += f"용도지역: {a1}\n"
            if k.split("_")[0] == "LadUseSittn":
                us = cc.code2landcategory(k.split("_")[1][2:5])
                land_info_str += f"이용상황: {us}\n"
            if k.split("_")[0] == "TpgrphHg":
                th = cc.code2tpgrphhg(k.split("_")[1][2:4])
                land_info_str += f"토지지세: {th}\n"
            if k.split("_")[0] == "TpgrphFrm":
                tf = cc.code2tpgrphfrm(k.split("_")[1][2:4])
                land_info_str += f"토지형상: {tf}\n"
            if k.split("_")[0] == "TpgrphHg":
                rs = cc.code2roadside(k.split("_")[1][2:4])
                land_info_str += f"도로접면: {rs}\n"
            if k.split("_")[0] == "LandUsePlans":
                # print(k)
                if cc.code2useplan(k.split("_")[1]):
                    land_use_plan_str += cc.code2useplan(k.split("_")[1]) + ", "
        # print(f"- {k}: {v}")

    land_info_str += "토지면적: {:,}㎡\n".format(target_x.iloc[0]["LndpclAr"])
    land_info_str += "기준년도: {}년\n".format(target_x.iloc[0]["Year"])
    land_info_str += "기준월: {}월\n".format(target_x.iloc[0]["Month"])
    land_info_str += "개별공시지가: {:,d}원/㎡당\n".format(int(target_x.iloc[0]["PblntfPclnd"]))
    land_info_str += "지가지수: {}\n".format(target_x.iloc[0]["PclndIndex"])
    land_info_str += "지가변동률: {}%\n".format(target_x.iloc[0]["PclndChgRt"])
    land_info_str += "누계지가변동률: {}%\n".format(target_x.iloc[0]["AcmtlPclndChgRt"])
    land_info_str += "권역별지가지수: {}\n".format(target_x.iloc[0]["LargeClPclndIndex"])
    land_info_str += "권역별지가변동률: {}%\n".format(target_x.iloc[0]["LargeClPclndChgRt"])
    land_info_str += "권역별누계지가변동률: {}%\n".format(target_x.iloc[0]["LargeClAcmtlPclndChgRt"])
    land_info_str += "생산자물가지수: {}\n".format(target_x.iloc[0]["PPI"])
    land_info_str += "소비자물가지수: {}\n".format(target_x.iloc[0]["CPI"])

    land_info_str += f"이용계획: {land_use_plan_str[:-2]}"

    info_str = land_info_str + "\n\n" + place_info_str

    tree_text = ""
    tree_dump = loaded_model.get_booster().get_dump()
    for i, tree in enumerate(tree_dump):
        tree_text += f"Tree {i}:\n{tree}"

    lt_api = LandTradeAPI(api.LAND_TRADE_API_KEY)
    target_year = int(target_x.iloc[0]["Year"])
    target_month = int(target_x.iloc[0]["Month"])

    # Compare land data
    compare_land_trade = {}

    while True:
        result = lt_api.get_data(target_pnu[:5], target_year, target_month)
        if result == None:
            target_month -= 1
            if target_month == 0:
                target_month = 12
                target_year -= 1
            if target_year == 2000:
                break
            continue
        
        for r in result:
            if isinstance(r, dict):
                if r["지목"] == lc:
                    if r.get("용도지역") != None:
                        if r["용도지역"] == a1:
                            compare_land_trade = r
                            break
        if compare_land_trade != {}:
            break
        target_month -= 1
        if target_month == 0:
            target_month = 12
            target_year -= 1
        if target_year == 2013:
            break

    if compare_land_trade != {}:
        compare_pnu = cc.addr2code(f"{cc.code2addr(compare_land_trade['지역코드'])} {compare_land_trade['법정동']} {compare_land_trade['지번']}")
        lf_api = LandFeatureAPI(api.LAND_API_KEY)
        result = lf_api.get_data(compare_pnu[0:10], int(compare_land_trade["년"]), assorted=True)
        compare_land = None
        for r in result:
            if r["prposArea1Nm"] == compare_land_trade["용도지역"] and r["lndcgrCodeNm"] == compare_land_trade["지목"]:
                compare_land = r
                break
        if compare_land != None:
            compare_pnu = compare_land["pnu"]
            compare_date = compare_land_trade["년"] + compare_land_trade["월"].zfill(2)
            print("비교하고자 하는 토지 주소:", cc.code2addr(compare_pnu))
            print("기준년도:", compare_date)
            compare_land_feature = mid.make(compare_pnu, compare_date)

            compare_info_str = "토지 매매가: {:,f}원/㎡당\n\n".format(float(float(compare_land_trade["거래금액"].replace(",",""))*10000 / float(compare_land_trade['거래면적'].replace(',',''))))
            land_use_plan_str = ", ".join(
                [cc.code2useplan(item) for item in compare_land_feature["LandUsePlans"].split("/") if cc.code2useplan(item) is not None]
            )
            place_info_str = "== 주변 상권 정보 ==\n"
            for k, v in compare_land_feature.items():
                if k[0:3] in cc.PLACE_CODE.keys():
                    place_kr = cc.PLACE_CODE[k[0:3]]
                    if len(k.split("_")) == 2:
                        place_info_str += "{} 이내에 있는 {}의 수: {:,d}개\n".format(k.split("_")[1], place_kr, int(v))
                    else:
                        if v == 20000:
                            continue
                        place_info_str += "{} 최소 거리: {:,d}m\n".format(place_kr, int(v))
                        
            compare_info_str = f"""
            비교 토지 주소: {cc.code2addr(compare_land_trade['지역코드'])} {compare_land_trade['법정동']} {compare_land_trade['지번']}

            비교 토지의 거래가: ￦{int(float(compare_land_trade['거래금액'].replace(',',''))*10000):,d} ({int(float(compare_land_trade['거래금액'].replace(',',''))*10000 / float(compare_land_trade['거래면적'].replace(',',''))):,d}원/㎡)
            
            필지: {cc.code2regstr(compare_land_feature['RegstrSe'][2:3])}
            지목: {cc.code2lndcgr(compare_land_feature['Lndcgr'][2:4])}
            용도지역: {cc.code2zoning(compare_land_feature['PrposArea1'][2:4])}
            이용상황: {cc.code2landcategory(compare_land_feature['LadUseSittn'][2:5])}
            토지지세: {cc.code2tpgrphhg(compare_land_feature['TpgrphHg'][2:4])}
            도로접면: {cc.code2roadside(compare_land_feature['RoadSide'][2:4])}
            토지형상: {cc.code2tpgrphfrm(compare_land_feature['TpgrphFrm'][2:4])}
            토지면적: {float(compare_land_feature['LndpclAr']):,}㎡
            기준년도: {compare_land_feature['Year']}년
            기준월: {compare_land_feature['Month']}월
            개별공시지가: {int(compare_land_feature['PblntfPclnd']):,}원/㎡당
            지가지수: {compare_land_feature['PclndIndex']}
            지가변동률: {compare_land_feature['PclndChgRt']}%
            누계지가변동률: {compare_land_feature['AcmtlPclndChgRt']}%
            권역별지가지수: {compare_land_feature['LargeClPclndIndex']}
            권역별지가변동률: {compare_land_feature['LargeClPclndChgRt']}%
            권역별누계지가변동률: {compare_land_feature['LargeClAcmtlPclndChgRt']}%
            생산자물가지수: {compare_land_feature['PPI']}
            소비자물가지수: {compare_land_feature['CPI']}
            이용계획: {land_use_plan_str}
                
            {place_info_str}
            """
        else:
            compare_info_str = "비교군 없음"
    else:
        compare_info_str = "비교군 없음"

    sys_msg_str = f"""
    너는 이제부터 토지의 가치를 평가하는 감정평가사야. 토지의 가치를 평가해서 일반 사용자들이 읽을 감정평가서를 작성해야돼.
    토지의 가격이 어떻게 산출되었는지 주어진 정보를 바탕으로 논리적으로 설명하고 가치를 평가해야돼.
    가격이 199,726.327313원 처럼 소수점을 포함한다면 199,726원 같이 소수점을 버리고 작성해줘.
    모든 설명이 끝나고 마지막에는 제곱미터당 가격과 토지면적과 곱한 가격을 모두 말해줘야돼.

    가치를 평가할 토지 주소: {cc.code2addr(target_pnu)}
        
    == 가치를 평가할 토지 정보 ==
    {info_str}
        
    아래 결정트리에 의거해서 논리적으로 왜 가격을 그렇게 예측했는지 설명해줘.
    설명할 때 영문변수명은 언급하지 말고, 사용자가 이해하기 힘들 수 있는 어려운 단어는 제외해줘. (예를 들면 결정트리)
        
    == 결정트리 ==
    {tree_text}
        
    또한, 아래 비교군 토지 정보 중 주변에 비슷한 토지의 최근 매매 내역을 기반으로 가격 가치 판단에 대한 근거를 제시해줘.
        
    == 비교군 토지 정보 ==
    {compare_info_str}
        
    비교군과의 비교 분석을 통한 가치 평가를 중점으로 진행하고, 여기서 나오는 근거들은 결정트리에 근거하여 답변해줘.
    그리고 '제공해주신 데이터는~' 이러한 방식으로 말하지 말고, 너가 직접 수집한 정보를 통해 가치 판단한다는 느낌으로 말해줘.
    넌 전문가야. 그냥 담백하게 ~ 토지에 대한 가격은 얼마로 산정되었습니다. 이에 대한 근거는 다음과 같습니다. 이런식으로 시작하는것도 나쁘지 않을 것 같아.
    만약 비교군 토지 정보가 없다면, 위 과정은 생략해.
        
    모든 근거는 결정트리에 근거하여 논리적으로 답변해줘.
    아래 양식에 맞추어 작성해줘. <> 안에 적혀있는 내용은 너가 이해하기 쉽게 주석을 달아놓은거니까 작성할때 포함하지마.
        
    == 양식 ==
    ## **토지 가격 평가 설명**

    * 평가 토지: 경기도 광명시 광명동 산79-2
    * 면적:
    * 지목: 
    * 이용상황:
    * 용도지역:
    * 도로조건:
    * 형상지세:
    * 평가액: ￦736,179,000 (76,901원/㎡ x 9,573㎡)
        
    경기도 광명시 광명동 산79-2 토지에 대한 가격은 736,179,000원<예측가와 토지 면적을 곱한 가격>으로 산정되었습니다. 이에 대한 근거는 다음과 같습니다. 

    **토지 특성 분석:**
    <
    토지 특성에 관해 분석하면 돼.
    1. 위치 및 주위환경
    2. 교통상황
    3. 형태 및 이용상황
    4. 인접 도로상태
    5. 토지이용계획사항
    6. 기타 참고사항

    번호 순서대로 분석해서 작성하고 없는 정보는 '해당사항 없습니다.'라고 작성해줘.
    >

    **입지 분석:** 
    <
    주변 입지를 분석하면 돼.
    1. 주거환경
    2. 상권
    3. 교통환경
    4. 개발가능성

    번호 순서대로 분석해서 작성하고 없는 정보는 '해당사항 없습니다.'라고 작성해줘.
    >

    **비교 사례 분석:**
    인근지역에 있는 표준지 중에서 대상토지와 용도지역ㆍ이용상황ㆍ주변환경 등이 같거나 가장 비슷한 경기도 광명시 광명동 산1**를 비교지로 선정하였습니다.
    비교지에 대한 자세한 정보는 다음과 같습니다.
    * 비교 토지: 경기도 광명시 광명동 산1**
    * 면적: 33㎡
    * 지목: 
    * 이용상황: 
    * 용도지역:
    * 도로조건:
    * 형상지세:
    * 공시지가: 12,712,727원/㎡

    대상 토지와 비교지에 대한 비교는 다음과 같습니다.

    <
    1. 가로조건
    2. 접근조건
    3. 환경조건
    4. 획지조건
    5. 행정적조건
    6. 기타조건

    * 

    번호 순서대로 분석해서 작성하고 없는 정보는 '해당사항 없습니다.'라고 작성해줘.
    대상 토지와 비교지의 조건들이 유사하다면 '대체로 유사함'이라고 작성해주고 다르다면 '대상 토지가 가로의 폭 등에서 열세함'형태로 알려줘.
    마지막 *에는 토지 비교 내용을 요약해서 알려주고 비교지의 가격과 비교하여 대상 토지 가격의 산출 근거를 명확하게 제시해줘.
    >

    **결론:**

    위와 같은 분석 결과를 바탕으로  경기도 광명시 광명동 산79-2 토지 가격은  76,901원/㎡당으로 평가되었습니다. 이는 면적으로 환산하면 736,179,000원입니다. 
    <결론은 면적당 가격을 먼저 말해주고, 면적과 예측가를 곱한 전체 토지 가격을 말해주면 돼.>
        
    """

    llm_response = llm_model.generate_content(
        contents=sys_msg_str,
        request_options={"timeout": 1000}
    )
    return llm_response.text