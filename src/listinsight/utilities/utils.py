import json

from qtpy import QtCore


def writeJson(json_path: str, data: dict) -> tuple[bool, str]:
    """Write JSON file"""
    jsonfile = QtCore.QFile(json_path)
    err = None

    if not jsonfile.open(QtCore.QIODeviceBase.OpenModeFlag.WriteOnly):
        err = f"Opening Error: {IOError(jsonfile.errorString())}"
        return False, err
    
    json_document = QtCore.QJsonDocument.fromVariant(data)

    if json_document.isNull():
        err = f"Failed to map JSON data structure"
        return False, err

    jsonfile.write(json_document.toJson(QtCore.QJsonDocument.JsonFormat.Indented))
    jsonfile.close()

    return True, err

def readJson(json_file: str) -> tuple[dict, str]:
        try:
            with open(json_file, mode='r', encoding='utf8') as file:
                return json.load(file), ""
        except json.JSONDecodeError:
            err = f"Warning: {json_file} is empty or contains invalid JSON."
            return {}, err
        except FileNotFoundError:
                err = f"Error: {json_file} not found."
                return {}, err

 