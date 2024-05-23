import xgboost as xgb
import pandas as pd
import app.functions.make_input_data as mid
from config import model
import time

def pred(pnu: str, year: int, month: int) -> int:
    loaded_model = xgb.XGBRegressor()
    loaded_model.load_model(model.MODEL_PATH)
    target_land = mid.make(pnu, f"{year:04d}{month:02d}")
    target_feature = {}
    for feature in loaded_model.feature_names_in_:
        if not feature in target_land.keys():
            if feature.split("_")[0] == "Sido":
                target_feature[feature] = feature.split("_")[1] == target_land["PNU"][0:2]
            elif feature.split("_")[0] == "LandUsePlans":
                target_feature[feature] = feature.split("_")[1] in target_land["LandUsePlans"].split("/")
            else:
                target_feature[feature] = feature.split("_")[1] in target_land[feature.split("_")[0]]
        else:
            target_feature[feature] = target_land[feature]

    target_x = pd.DataFrame.from_dict(data=[target_feature], orient="columns", dtype=float)
    target_predict = loaded_model.predict(target_x)
    return int(f"{target_predict[0]:.0f}")

if __name__ == "__main__":
    stt_time = time.time()
    target_pnu = "1147010100109370018"
    target_year = 2024
    target_month = 5
    pred_value = pred(target_pnu, target_year, target_month)
    end_time = time.time()
    print(f"Execution time: {end_time - stt_time:.2f} seconds")
    print(f"Predict value: {pred_value:,.0f}")