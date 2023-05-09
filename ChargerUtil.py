import jsonschema, json
from datetime import datetime

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


DataTransferMessage = {
    "chargeValue": {
        "connectorId":1, "idTag":"$idTag", "timestamp":"$ctime", "transactionId":"$transactionId"
    },
    "chargeValueResponse":{
        "status":"Accepted", "data":{"watt":1000, "cost":100, "cabletype":""}
    }
}

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
    refreshv = {'$ctime':datetime.now().isoformat(sep='T', timespec='seconds')+'Z'}

    if isinstance(adict, dict):
        for key in adict.keys():
            if adict[key] == k:
                try:
                    if k in refreshv :
                        adict[key] = refreshv[k]
                    else:
                        adict[key] = typeconv[key](value) if key in typeconv else value
                except ValueError:
                    print(f"Rendering Error {adict[key]} assigned with ''")
                    adict[key] = ""
                    pass  # do nothing if the timestamp is already in the correct format
            elif isinstance(adict[key], (dict, list)):
                tc_render(adict[key], k, value)
    elif isinstance(adict, list):
        for l in adict:
            tc_render(l, k, value)
    return adict

class Config():
    def __init__(self, **kwargs):
        self.wss_url = kwargs["wss_url"]
        self.rest_url = kwargs["rest_url"]
        self.auth_token = kwargs["auth_token"]
        self.en_tr = kwargs["en_tr"]
        self.en_tc = kwargs["en_tc"]
        self.lst_cases = kwargs["lst_cases"]
        self.en_status = kwargs["en_status"]
        self.txt_recv = kwargs["txt_recv"]
        self.cid = kwargs["cid"]
        self.rcid = kwargs["rcid"]
        self.sno = kwargs["sno"]
        self.rsno  = kwargs["rsno"]
        self.mdl = kwargs["mdl"]
        self.result = kwargs["result"]
        self.confV = kwargs["confV"]
        self.en_reserve = kwargs["en_reserve"]
        self.lst_tc = kwargs["lst_tc"]
        self.test_mode = kwargs["test_mode"]
        self.ocppdocs = kwargs["ocppdocs"]
        self.txt_tc = kwargs["txt_tc"]
        self.progressbar = kwargs["progressbar"]
        self.curProgress = kwargs["curProgress"]
        self.bt_direct_send = kwargs['bt_direct_send']
        self.lb_mode_alert = kwargs['lb_mode_alert']
        self.testschem = kwargs['testschem']
        self.ciphersuite = kwargs['ciphersuite']
        self.en_meter = kwargs['en_meter']

diag_info = {
       "chargeBoxSerialNumber": "ABCD1234",
       "chargePointModel": "XYZ Model A",
       "vendorErrorCode": "ERR-001",
       "diagnosticTroubleCodes": [
          {
             "code": "P1234",
             "description": "Battery voltage is low",
             "status": "active"
          },
          {
             "code": "P5678",
             "description": "Communication error with vehicle",
             "status": "stored"
          }
       ]
    }

message_map = {
                "BootNotification":[
                    ["StatusNotification", {"status": "Available"}]
                ],
                "Reset": [
                    ["BootNotification", {}],
                    ["StatusNotification", {"status": "Available"}]
                ],
                "RemoteStartTransaction":[
                    ["Authorize", {"idTag": "$idTag1"}, {"idTagInfo": {"status": "Accepted"}}],
                    ["DataTransfer", {"messageId":"chargeValue", "connectorId":1, "idTag":"$idTag", "timestamp":"$ctime"}],
                    ["StartTransaction",{}],
                    ["StatusNotification",{"status":"Charging"}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}],
                    ["MeterValues", {}]
                ],
                "RemoteStopTransaction":[
                    ["StopTransaction",{}],
                    ["StatusNotification", {"status":"Finishing"}],
                    ["StatusNotification", {"status":"Available"}]
                ]
                }