import sys
import time
from concurrent.futures import ThreadPoolExecutor
from config import api
import app.functions.get_place_data as gpd
from app.functions.api import (
    LandFeatureAPI,
    LandUsePlanAPI,
    FluctuationRateOfLandPriceAPI,
    ProducerPriceIndexAPI,
    ConsumerPriceIndexAPI
)

def make(pnu: str, date: str):
    start_time = time.time()  # 전체 실행 시작 시간
    land = {
        "PNU": pnu,
        "Year": int(date[0:4]),
        "Month": int(date[4:6])
    }

    # 병렬로 실행할 함수들을 정의
    def fetch_land_feature_data():
        lf_api = LandFeatureAPI(api.LAND_API_KEY)
        result = lf_api.get_data(land["PNU"], land["Year"])
        if result is None:
            sys.exit("Failed to fetch land characteristic data from the API.")
        return result

    def fetch_fluctuation_rate_data():
        frolp_api = FluctuationRateOfLandPriceAPI(api.LAND_API_KEY)
        region_data = frolp_api.get_data_by_region(land["PNU"][0:10], int(land["Year"]), int(land["Month"]))
        large_region_data = frolp_api.get_data_by_large_region(land["PNU"][0:10], int(land["Year"]), int(land["Month"]))
        return region_data, large_region_data

    def fetch_price_index_data():
        ppi_api = ProducerPriceIndexAPI(api.ECOS_API_KEY)
        ppi_result = ppi_api.get_data(int(land["Year"]), int(land["Month"]))
        if ppi_result is None:
            sys.exit("Failed to fetch producer price index data from the API.")
        
        cpi_api = ConsumerPriceIndexAPI(api.ECOS_API_KEY)
        cpi_result = cpi_api.get_data(int(land["Year"]), int(land["Month"]))
        if cpi_result is None:
            sys.exit("Failed to fetch customer price index data from the API.")
        
        return ppi_result, cpi_result

    def fetch_place_data():
        future_rd = executor.submit(gpd.get_nearest_place_distance, addr)
        future_rd_500 = executor.submit(gpd.get_place_count_in_radius, addr, 500)
        future_rd_1000 = executor.submit(gpd.get_place_count_in_radius, addr, 1000)
        future_rd_3000 = executor.submit(gpd.get_place_count_in_radius, addr, 3000)

        rd = future_rd.result()
        rd_500 = future_rd_500.result()
        rd_1000 = future_rd_1000.result()
        rd_3000 = future_rd_3000.result()

        if rd is None or rd_500 is None or rd_1000 is None or rd_3000 is None:
            sys.exit("Failed to fetch place data from the API.")

        return rd, rd_500, rd_1000, rd_3000

    def fetch_land_use_plan_data():
        lup_api = LandUsePlanAPI(api.LAND_API_KEY)
        result = lup_api.get_data(land["PNU"])
        if result is None:
            sys.exit("Failed to fetch land use plans data from the API.")
        return result

    # ThreadPoolExecutor를 사용하여 병렬로 API 호출
    with ThreadPoolExecutor() as executor:
        # 병렬 실행
        future_feature = executor.submit(fetch_land_feature_data)
        future_fluctuation = executor.submit(fetch_fluctuation_rate_data)
        future_price_index = executor.submit(fetch_price_index_data)
        future_land_use_plan = executor.submit(fetch_land_use_plan_data)

        # Land feature 데이터 처리
        feature_start = time.time()
        result = future_feature.result()
        addr = result["ldCodeNm"] + " "
        addr += result["regstrSeCodeNm"] if result["regstrSeCodeNm"] == "산" else ""
        addr += str(int(str(land["PNU"])[11:15])) + "-" + str(int(str(land["PNU"])[15:19]))
        land["PblntfPclnd"] = result["pblntfPclnd"]
        land["RegstrSe"] = "Re" + result["regstrSeCode"]
        land["Lndcgr"] = "Lc" + result["lndcgrCode"]
        land["LndpclAr"] = result["lndpclAr"]
        land["PrposArea1"] = "A1" + result["prposArea1"]
        land["PrposArea2"] = "A2" + result["prposArea2"]
        land["LadUseSittn"] = "Us" + result["ladUseSittn"]
        land["TpgrphHg"] = "Hg" + result["tpgrphHgCode"]
        land["TpgrphFrm"] = "Fm" + result["tpgrphFrmCode"]
        land["RoadSide"] = "Rs" + result["roadSideCode"]
        feature_end = time.time()
        print(f"Land feature data fetched in {feature_end - feature_start:.2f} seconds")

        # Fluctuation rate 데이터 처리
        fluctuation_start = time.time()
        region_data, large_region_data = future_fluctuation.result()
        land["PclndIndex"] = region_data["pclndIndex"]
        land["PclndChgRt"] = region_data["pclndChgRt"]
        land["AcmtlPclndChgRt"] = region_data["acmtlPclndChgRt"]
        land["LargeClPclndIndex"] = large_region_data["pclndIndex"]
        land["LargeClPclndChgRt"] = large_region_data["pclndChgRt"]
        land["LargeClAcmtlPclndChgRt"] = large_region_data["acmtlPclndChgRt"]
        fluctuation_end = time.time()
        print(f"Fluctuation rate data fetched in {fluctuation_end - fluctuation_start:.2f} seconds")

        # Price index 데이터 처리
        price_index_start = time.time()
        ppi_result, cpi_result = future_price_index.result()
        land["PPI"] = ppi_result
        land["CPI"] = cpi_result
        price_index_end = time.time()
        print(f"Price index data fetched in {price_index_end - price_index_start:.2f} seconds")

        # Place data를 병렬로 가져오기
        place_data_start = time.time()
        rd, rd_500, rd_1000, rd_3000 = fetch_place_data()  # `addr`가 필요한 이유로 이 부분은 호출 후에 따로 병렬화
        place_data_end = time.time()
        print(f"Place data fetched in {place_data_end - place_data_start:.2f} seconds")

        for category in gpd.Category.list():
            land[category] = rd[category]
            land[category + "_500m"] = rd_500[category]
            land[category + "_1000m"] = rd_1000[category]
            land[category + "_3000m"] = rd_3000[category]

        # Land use plan 데이터 처리
        land_use_plan_start = time.time()
        land["LandUsePlans"] = future_land_use_plan.result()
        land_use_plan_end = time.time()
        print(f"Land use plans data fetched in {land_use_plan_end - land_use_plan_start:.2f} seconds")

    end_time = time.time()  # 전체 실행 종료 시간
    print(f"Total execution time: {end_time - start_time:.2f} seconds")

    return land

if __name__ == "__main__":
    target_pnu = "1147010100109370018"
    target_date = "202312"
    target_land = make(target_pnu, target_date)
    print(target_land)
