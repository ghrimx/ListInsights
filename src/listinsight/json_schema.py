json_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["datasets", "project_files", "project_name", "project_rootpath"],
  "properties": {
    "datasets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["metadata", "filters"],
        "properties": {
          "metadata": {
            "type": "object",
            "required": ["dataset_id", "dataset_name", "parquet", "primary_key_index", "primary_key_name"],
            "properties": {
              "dataset_id": { "type": "string" },
              "dataset_name": { "type": "string" },
              "parquet": { "type": "string" },
              "primary_key_index": { "type": "integer" },
              "primary_key_name": { "type": "string" }
            }
          },
          "filters": {
            "type": "array",
            "items": {}
          }
        }
      }
    },
    "project_files": {
      "type": "object",
      "required": ["shortlist", "tagged"],
      "properties": {
        "shortlist": { "type": "string" },
        "tagged": { "type": "string" }
      }
    },
    "project_name": { "type": "string" },
    "project_rootpath": { "type": "string" }
  }
}
