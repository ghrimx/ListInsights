import avro.schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter

schema = avro.schema.parse(open("C:/Users/debru/Documents/GitHub/ListInsights/tag.avsc", "rb").read())

writer = DataFileWriter(open("tags.avro", "wb"), DatumWriter(), schema)
writer.append({"tagname":"OverReporting", "values":["BE1234", "BE4567", "BE6789"]})
writer.append({"tagname":"UnderReporting", "values":["BE1234", "BE4567", "BE6789"]})
writer.close()

reader = DataFileReader(open("tags.avro", "rb"), DatumReader())
for user in reader:
    print(user)
reader.close()