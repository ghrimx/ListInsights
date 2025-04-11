from pathlib import Path

metadata_list = [
        {
            "dataset_id": "16",
            "dataset_name": "SAMPLE",
            "parquet": "C:/Users/debru/Documents/DEMO/ListInsight/parquets/SAMPLE.parquet",
            "primary_key_index": -1,
            "primary_key_name": ""
        },
        {
            "dataset_id": "17",
            "dataset_name": "SAMPLE",
            "parquet": "C:/Users/debru/Documents/DEMO/ListInsight/parquets/SAMPLE.parquet",
            "primary_key_index": 0,
            "primary_key_name": "CASE_ID"
        }
    ]

update = {
            "dataset_id": "16",
            "dataset_name": "SAMPLE",
            "parquet": "C:/Users/debru/Documents/DEMO/ListInsight/parquets/SAMPLE.parquet",
            "primary_key_index": 0,
            "primary_key_name": "CASE_ID"
        }

add = {
            "dataset_id": "19",
            "dataset_name": "SAMPLE",
            "parquet": "C:/Users/debru/Documents/DEMO/ListInsight/parquets/SAMPLE.parquet",
            "primary_key_index": 0,
            "primary_key_name": "CASE_ID"
        }

def test_loop():
    metadata_dict: dict
    for i in range(len(metadata_list)):
        metadata_dict = metadata_list[i]
        # dataset_id = metadata_dict.get("dataset_id")
        if metadata_dict.get("dataset_id") == "19":
            metadata_list[i] = update
            break
    else:
        metadata_list.append(add)

    print(metadata_list)
    assert len(metadata_list) > 0

def test_path():
    p = Path(None)
    print(f"Path={p}\nexist?:{p.exists()}")