import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.functions.pnu_geolocation_lookup import get_word
from config.default import BASE_DIR
from config.database import Database
import json

def make_land_info():
    print("### Make land_info table")
    db = Database()
    f = open(BASE_DIR + "/data/PnuCode.csv", "r", encoding="utf-8")
    lines = f.readlines()
    sido = []
    for line in lines:
        if line.split(",")[0] == "code":
            continue
        if not line.split(",")[0][0:2] in sido:
            sido.append(line.split(",")[0][0:2])
        
    print(sido)
    for s in sido:
        try:
            sql = f"""CREATE TABLE {s}_land_info (
                pnu VARCHAR(20) NOT NULL PRIMARY KEY,
                official_land_price FLOAT NOT NULL,
                predict_land_price FLOAT,
                land_classification VARCHAR(10) NOT NULL,
                land_zoning VARCHAR(20) NOT NULL,
                land_use_situation VARCHAR(20) NOT NULL,
                land_register VARCHAR(10) NOT NULL,
                land_area FLOAT NOT NULL,
                land_height VARCHAR(10) NOT NULL,
                land_form VARCHAR(10) NOT NULL,
                road_side VARCHAR(10) NOT NULL,
                land_uses TEXT,
                last_predicted_date DATE,
                land_feature_stdr_year INT NOT NULL
            )
            """
            db.execute(sql)
            db.commit()
        except:
            print(f"Exception: {s}_land_info table is already exist")
    db.close()

def make_region_coordinates():
    print("### Make region_coordinates table")
    db = Database()
    try:
        sql = """CREATE TABLE region_coordinates (
            pnu VARCHAR(10) NOT NULL PRIMARY KEY,
            type VARCHAR(12) NOT NULL,
            region VARCHAR(50) NOT NULL,
            lat DECIMAL(17,14) NOT NULL,
            lng DECIMAL(17,14) NOT NULL
        )
        """
        db.execute(sql)
        db.commit()
    except:
        print("Exception: region_coordinates table is already exist")

    print("##  Insert region_coordinates data")
    sql = "INSERT INTO region_coordinates (pnu, type, region, lat, lng) VALUES (%s, %s, %s, %s, %s)"
    f = open(BASE_DIR + "/data/PnuCode.csv", "r", encoding="utf-8")
    lines = f.readlines()
    count = 0
    try:
        for line in lines:
            count += 1
            print(f"\r#   {count:5d}/{len(lines):5d}", end="")
            if line.split(",")[1] in ["sido"]:
                continue
            if line.split(",")[4] == "" or line.split(",")[4] == "\n":
                if line.split(",")[3] == "":
                    if line.split(",")[2] == "":
                        db.commit()
                        lat, lng = get_word(line.split(",")[1])
                        db.execute(sql, (line.split(",")[0][0:2], "sido", line.split(",")[1], lat, lng))
                    else:
                        lat, lng = get_word(line.split(",")[1] + " " + line.split(",")[2])
                        db.execute(sql, (line.split(",")[0][0:5], "sigungu", line.split(",")[2], lat, lng))
                else:
                    lat, lng = get_word(line.split(",")[1] + " " + line.split(",")[2] + " " + line.split(",")[3])
                    db.execute(sql, (line.split(",")[0][0:8], "eupmyeondong", line.split(",")[3], lat, lng))
    except Exception as e:
        print(e)
    f.close()
    db.commit()
    db.close()

def make_geometry_data():
    print("### Make region_coordinates table")
    db = Database()
    try:
        sql = """CREATE TABLE geometry_data (
            pnu VARCHAR(10) NOT NULL PRIMARY KEY,
            centroid_lat DECIMAL(17,14) NOT NULL,
            centroid_lng DECIMAL(17,14) NOT NULL,
            multi_polygon LONGTEXT
        )
        """
        db.execute(sql)
        db.commit()
    except:
        print("Exception: region_coordinates table is already exist")

    print("##  Insert geometry data")
    sql = "INSERT INTO geometry_data (pnu, centroid_lat, centroid_lng, multi_polygon) VALUES (%s, %s, %s, %s)"
    for rt in ["emd", "sig", "sido"]:
        with open(BASE_DIR + "/data/" + rt + ".json", "r") as geo_file:
            data = json.load(geo_file)
        polygons = data["features"]
        count = 1
        for p in polygons:
            try:
                centroids = []
                total_area = 0
                
                for polygon in p["geometry"]["coordinates"]:
                    for coords in polygon:
                        x_sum = 0
                        y_sum = 0
                        n = len(coords)
                        
                        for coord in coords:
                            x_sum += coord[1]
                            y_sum += coord[0]
                        centroid = [y_sum / n, x_sum / n]
                        centroids.append(centroid)
                        total_area += 1  # 각 폴리곤의 영역을 1로 간주 (단순화)
                
                x_sum = sum([centroid[1] for centroid in centroids])
                y_sum = sum([centroid[0] for centroid in centroids])
                
                centroid = [y_sum / total_area, x_sum / total_area]
                
                if rt == "emd":
                    print(f"({count:4d}/{len(polygons):4d}) {p['properties']['EMD_CD']}")
                    db.execute(sql, (p["properties"]["EMD_CD"], centroid[1], centroid[0], json.dumps(p["geometry"]["coordinates"])))
                    db.commit()
                    count += 1
                elif rt == "sig":
                    print(f"({count:4d}/{len(polygon):4d}) {p['properties']['SIG_CD']}")
                    db.execute(sql, (p["properties"]["SIG_CD"], centroid[1], centroid[0], json.dumps(p["geometry"]["coordinates"])))
                    db.commit()
                    count += 1
                elif rt == "sido":
                    print(f"({count:4d}/{len(polygon):4d}) {p['properties']['CTPRVN_CD']}")
                    db.execute(sql, (p["properties"]["CTPRVN_CD"], centroid[1], centroid[0], json.dumps(p["geometry"]["coordinates"])))
                    db.commit()
                    count += 1
            except Exception as e:
                print(f"Error Occured! {e}")

def make_user_land_like_data():
    print("### Make user_land_like table")
    db = Database()
    try:
        sql = """CREATE TABLE user_land_like (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            pnu VARCHAR(20) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
        db.execute(sql)
        db.commit()
    except:
        print("Exception: user_land_like table is already exist")


if __name__ == "__main__":
    # make_land_info()
    make_region_coordinates()
    # make_geometry_data()
    # make_user_land_like_data()
