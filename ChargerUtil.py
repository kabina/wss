import jsonschema, json
def checkSchema(original, target, schema):
    """
    OCPP 규격과 다른지 체크, 다를 경우 False Return
    :param original: 점검 대상 스키마 명
    :param target: 점검 대상 Json 본체
    :return: True : 규격 동일, False: 규격 다름
    """
    if schema.startswith("DataTransfer"):
        return True, None
    try:
        schema = open(f"./{schema}/schemas/" + original + ".json").read().encode('utf-8')
        jsonschema.validate(instance=target, schema=json.loads(schema))
    except jsonschema.exceptions.ValidationError as e:
        return False, e.message
    return True, None

# def tc_render(adict, k, value):
#     """
#     dict내 value내에 특정 키워드'%keyword'를 찾아 이를 value로 대체
#     :param adict: 키워드(k)를 찾을 대상 dictionary
#     :param k: value로 대체하고자 하는는 $로 시작하는 값
#     :param value: $로 시작되는 키워드를 대체할 값
#     :return: rendering된 값 adict
#     """
#     typeconv = {
#         "reservationId":int
#     }
#     if isinstance(adict, dict):
#         for key in adict.keys():
#             if adict[key] == k:
#                 try:
#                     adict[key] = value if key not in typeconv else typeconv[key](value)
#                     #if adict[key] not in typeconv else typeconv[adict[key]](value)
#                 except ValueError:
#                     pass  # do nothing if the timestamp is already in the correct format
#             elif isinstance(adict[key], (dict, list)):
#                 tc_render(adict[key], k, value)
#     elif isinstance(adict, list):
#         for l in adict:
#             tc_render(l, k, value)
#     return adict

def tc_render(adict, k, value):
    """
    dict내 value내에 특정 키워드'%keyword'를 찾아 이를 value로 대체
    :param adict: 키워드(k)를 찾을 대상 dictionary
    :param k: value로 대체하고자 하는는 $로 시작하는 값
    :param value: $로 시작되는 키워드를 대체할 값
    :return: rendering된 값 adict
    """
    typeconv = {
        "reservationId":int,
        "connectorId":int
    }
    if isinstance(adict, dict):
        for key in adict.keys():
            if adict[key] == k:
                try:
                    adict[key] = typeconv[key](value) if key in typeconv else value
                except ValueError:
                    pass  # do nothing if the timestamp is already in the correct format
            elif isinstance(adict[key], (dict, list)):
                tc_render(adict[key], k, value)
    elif isinstance(adict, list):
        for l in adict:
            tc_render(l, k, value)
    return adict