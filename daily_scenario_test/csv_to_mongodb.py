import pandas as pd
from pymongo import MongoClient

# CSVファイルのパス
csv_file_path = "example_daily_test.csv"

# MongoDBの設定
mongo_uri = "mongodb://localhost:27017/"  # MongoDBのURI
db_name = "testDatabase"  # 使用するデータベース名
collection_name = "testResults"  # 使用するコレクション名

# CSVデータの読み込み
df = pd.read_csv(csv_file_path)

# MongoDBへの接続
client = MongoClient(mongo_uri)
db = client[db_name]
collection = db[collection_name]

# データの変換と挿入
for index, row in df.iterrows():
    # テスト項目のリストを作成
    test_items = []
    for col in df.columns:
        if "：" in col:  # テスト項目と判断
            item_name, item_type = col.split("：")
            # skip シナリオテスト総計
            if "シナリオテスト総計" in item_name:
                continue
            if item_name not in [item["name"] for item in test_items]:
                # 新しいテスト項目を追加
                test_items.append(
                    {"name": item_name, "OK": None, "NG": None, "Total": None}
                )
            # 最後に追加されたテスト項目を更新
            for item in test_items:
                if item["name"] == item_name:
                    item[item_type] = row[col]

    # ドキュメント形式でデータを挿入
    document = {
        "Date": row["Date"],
        "OK": row["シナリオテスト総計：OK"],
        "NG": row["シナリオテスト総計：NG"],
        "Total": row["シナリオテスト総計：シナリオ総数"],
        "Suite": test_items,
        "Success Rate (%)": row["Success Rate (%)"],
    }

    # MongoDBにデータ挿入
    collection.insert_one(document)

print("CSVデータがMongoDBにインポートされました。")
