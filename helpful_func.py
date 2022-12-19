import json
from pprint import pprint


def json_restructured(json_file, model):

    with open(json_file, "r", encoding="utf-8") as json_f:
        data = json.load(json_f)

        result_list = []

        for dict_element in data:
            fields_item = dict(dict_element)
            del fields_item["id"]
            result_list.append(
                {
                    "model": model,
                    "pk": dict_element["id"],
                    "fields": fields_item
                }
            )

        return result_list


def data_to_json_file(json_file, json_newfile, model):
    with open(json_newfile, "w", encoding="utf-8") as json_f_new:
        data = json_restructured(json_file, model)
        json_f_new.write(json.dumps(data, ensure_ascii=False))


# ad_ = json_restructured("./datasets/ad.json", "ads.ad")
# pprint(ad_)

# cat_ = json_restructured("./datasets/category.json", "ads.category")
# pprint(cat_)

# user_ = json_restructured("./datasets/user.json", "ads.aduser")
# pprint(user_)
#
# loc_ = json_restructured("./datasets/location.json", "ads.location")
# pprint(loc_)



cat_for_fixt = data_to_json_file("./datasets/category.json", "category_fixt.json", "ads.category")
location_for_fixt = data_to_json_file("./datasets/location.json", "location_fixt.json", "ads.location")
user_for_fixt = data_to_json_file("./datasets/user.json", "user_fixt.json", "ads.aduser")
ads_for_fixt = data_to_json_file("./datasets/ad.json", "ad_fixt.json", "ads.ad")
