import datetime
import uuid

TC = {
    "TC_000_BOOT" : [
        ["BootNotification", {}],
        ["StatusNotification", {"status": "Available"}],
        ["Authorize", {"idTag": "1031040000069641"}]
    ],
    "TC_003" : [
        ["BootNotification", {}],
        ["StatusNotification", {"status": "Available"}],
        ["Authorize", {"idTag": "1031040000069641"}, {"idTagInfo": {"status": "Accepted"}}],
        ["StartTransaction", {"idTag": "1031040000069641"}],
        ["StatusNotification", {"status": "Charging"}],
        ["MeterValues", {"transactionId":None}],
        ["StopTransaction", {"transactionId": None}],
        ["StatusNotification", {"status": "Finishing"}],
        ["StatusNotification", {"status": "Available"}],
    ],
    # "TC_004_1" : [
    #     ["BootNotification", {}],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["StartTransaction", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["MeterValues", {"transactionId":None}],
    #     ["StopTransaction", {"transactionId": None}],
    #     ["StatusNotification", {"status": "Finishing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_004_2": [
    #     ["BootNotification", {}],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_005_1": [
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StartTransaction", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["MeterValues", {"transactionId":None}],
    #     ["StatusNotification", {"status": "SuspendedEV"}],
    #     ["StopTransaction", {"transactionId": None}],
    #     ["StatusNotification", {"status": "Finishing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_061": [
    #     ["BootNotification", {}],
    #     ["Wait", "Reset"],
    #     ["Reply", "Reset"],
    # ],
    # "TC_010": [
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["Wait", "RemoteStartTransaction"],
    #     ["Reply", "RemoteStartTransaction"],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StartTransaction", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["StopTransaction", {"transactionId": None}],
    #     ["StatusNotification", {"status": "Finishing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_011_1": [
    #     ["BootNotification", {}],
    #     ["Wait", "RemoteStartTransaction"],
    #     ["Reply", "RemoteStartTransaction"],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["StartTransaction", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["Wait", "RemoteStopTransaction"],
    #     ["Reply", "RemoteStopTransaction"],
    #     ["StopTransaction", {"transactionId": None}],
    #     ["StatusNotification", {"status": "Finishing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_011_2": [
    #     ["BootNotification", {}],
    #     ["Wait", "RemoteStartTransaction"],
    #     ["Reply", "RemoteStartTransaction"],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_012": [
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["Wait", "RemoteStartTransaction"],
    #     ["Reply", "RemoteStartTransaction"],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StartTransaction", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["Wait", "RemoteStopTransaction"],
    #     ["Reply", "RemoteStopTransaction"],
    #     ["StopTransaction", {"transactionId": None}],
    #     ["StatusNotification", {"status": "Finishing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_013": [
    #     ["BootNotification", {}],
    #     ["Wait", "Reset"],
    #     ["Reply", "Reset"],
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_014": [
    #     ["Wait", "Reset"],
    #     ["Reply", "Reset"],
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_017_1": [
    #     ["Wait", "Reset"],
    #     ["Reply", "Reset"],
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_018": [
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["Wait", "RemoteStartTransaction"],
    #     ["Reply", "RemoteStartTransaction"],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StartTransaction", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["Wait", "UnlockConnector"],
    #     ["Reply", "UnlockConnector"],
    #     ["StatusNotification", {"status": "Finishing"}],
    #     ["StopTransaction", {"transactionId": None, "reason":"UnlockCommand"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_019": [
    #     ["Wait", "GetConfiguration"],
    #     ["Reply", "GetConfiguration"],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_021": [
    #     ["BootNotification", {}],
    #     ["Wait", "ChangeConfiguration"],
    #     ["Reply", "ChangeConfiguration"],
    # ],
    # "TC_023": [
    #     ["BootNotification", {}],
    #     ["Authorize", {"idTag": "1031040000069642"}], # 없는 번호
    #     ["Authorize", {"idTag": "1031040000069642"}],  # Expired 카드상태02 카드변호 변경 필요
    #     ["Authorize", {"idTag": "1031040000069642"}],  # Blocked 카드변호 변경 필요
    # ],
    # "TC_024": [
    #     ["BootNotification", {}],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["StatusNotification", {"status": "Faulted"}],
    # ],
    # "TC_026": [
    #     ["BootNotification", {}],
    #     ["Wait", "RemoteStartTransaction"],
    #     ["Reply", "RemoteStartTransaction", {"status":"Rejected"}],
    # ],
    # "TC_028": [
    #     ["BootNotification", {}],
    #     ["Wait", "RemoteStopTransaction"],
    #     ["Reply", "RemoteStopTransaction", {"status": "Rejected"}],
    # ],
    # "TC_030": [
    #     ["BootNotification", {}],
    #     ["Wait", "UnlockConnector"],
    #     ["Reply", "UnlockConnector", {"status": "UnlockFailed"}],
    # ],
    # "TC_032": [
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["Wait", "RemoteStartTransaction"],
    #     ["Reply", "RemoteStartTransaction"],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StartTransaction", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Unavailable"}],
    #     ["StopTransaction", {"idTag": "1031040000069641",
    #         "meterStop": 29000,
    #         "timestamp": "2023-02-24T07:26:57.512Z",
    #         "transactionId": 120531947,
    #         "reason": "PowerLoss",
    #         "transactionData": [
    #           {
    #             "sampledValue": [
    #               {
    #                 "value": "29000",
    #                 "measurand": "Energy.Active.Import.Register",
    #                 "unit": "Wh"
    #               }
    #             ],
    #             "timestamp": "2023-02-24T07:26:57.512Z"
    #           }
    #         ]}
    #      ],
    #     ["StatusNotification", {"status": "Finishing"}],
    # ],
    # "TC_037_1": [
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StartTransaction", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["StopTransaction", {"transactionId": None, "reason": "Local"}],
    #     ["StatusNotification", {"status": "Finishing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_037_3": [
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["Authorize", {"idTag": "1031040000069641"}],
    #     ["StartTransaction", {"idTag": "1031040000069641"}],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["StopTransaction", {"transactionId": None, "reason": "DeAuthorized"}],
    #     ["StatusNotification", {"status": "Finishing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_039": [
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["StartTransaction", {
    #         "idTag": "1031040000069641",
    #         "meterStart": 0,
    #         "timestamp": "2023-02-24T07:26:57.512Z"
    #         }
    #      ],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["StopTransaction", {"transactionId": None, "meterStop": 29000,"reason": "Local", "timestamp": "2023-02-24T07:26:57.512Z"}],
    #     ["StatusNotification", {"status": "Finishing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_040_1": [
    #     ["BootNotification", {}],
    #     ["Wait", "ChangeConfiguration", {"UnknownConfigurationKey":"300"}],
    #     ["Reply", "ChangeConfiguration", {"status":"NotSupported"}],
    # ],
    # "TC_040_2": [
    #     ["BootNotification", {}],
    #     ["Wait", "ChangeConfiguration",{"key": "MeterValueSampleInterval", "value": "-1"}],
    #     ["Reply", "ChangeConfiguration", {"status": "Rejected"}],
    # ],
    # "TC_042_1": [
    #     ["BootNotification", {}],
    #     ["Wait", "GetLocalListVersion"],
    #     ["Reply", "GetLocalListVersion", {"listVersion":-1}],
    # ],
    # "TC_042_2": [
    #     ["BootNotification", {}],
    #     ["Wait", "GetLocalListVersion"],
    #     ["Reply", "GetLocalListVersion", {"listVersion":0}],
    # ],
    # "TC_043_1": [
    #     ["BootNotification", {}],
    #     ["Wait", "SendLocalList", {"updateType": "Full" }],
    #     ["Reply", "SendLocalList", {"status": "NotSupported"}],
    # ],
    # "TC_043_3": [
    #     ["BootNotification", {}],
    #     ["Wait", "SendLocalList", {"updateType": "Full"}],
    #     ["Reply", "SendLocalList", {"status": "Failed"}],
    # ],
    # "TC_043_4": [
    #     ["BootNotification", {}],
    #     ["Wait", "SendLocalList", {"updateType": "Full"}],
    #     ["Reply", "SendLocalList", {"status": "Accepted"}],
    # ],
    # "TC_043_5": [
    #     ["BootNotification", {}],
    #     ["Wait", "SendLocalList", {"updateType": "Differential"}],
    #     ["Reply", "SendLocalList", {"status": "Accepted"}],
    # ],
    # "TC_044_1": [
    #     ["BootNotification", {}],
    #     ["Wait", "UpdateFirmware", {"location": "https://s3~~~~", "retrieveDate": "2023-04-15T10:15:00Z" }],
    #     ["Reply", "UpdateFirmware"],
    #     ["StatusNotification", {"status": "Unavailable"}],
    #     ["FirmwareStatusNotification", {"status": "Downloading"}],
    #     ["FirmwareStatusNotification", {"status": "Downloaded"}],
    #     ["FirmwareStatusNotification", {"status": "Installing"}],
    #     ["StatusNotification", {"status": "Unavailable"}],
    #     ["FirmwareStatusNotification", {"status": "Installed"}],
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_044_2": [
    #     ["BootNotification", {}],
    #     ["Wait", "UpdateFirmware", {"location": "ftp://google.com", "retrieveDate": "2023-04-15T10:15:00Z"}],
    #     ["Reply", "UpdateFirmware"],
    #     ["StatusNotification", {"status": "Unavailable"}],
    #     ["FirmwareStatusNotification", {"status": "Downloading"}],
    #     ["FirmwareStatusNotification", {"status": "Downloaded"}],
    #     ["FirmwareStatusNotification", {"status": "Installing"}],
    #     ["StatusNotification", {"status": "Unavailable"}],
    #     ["FirmwareStatusNotification", {"status": "Installed"}],
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_044_3": [
    #     ["BootNotification", {}],
    #     ["Wait", "UpdateFirmware", {"location": "file://google.com", "retrieveDate": "2023-04-15T10:15:00Z"}],
    #     ["Reply", "UpdateFirmware"],
    #     ["StatusNotification", {"status": "Unavailable"}],
    #     ["FirmwareStatusNotification", {"status": "Downloading"}],
    #     ["FirmwareStatusNotification", {"status": "Downloaded"}],
    #     ["FirmwareStatusNotification", {"status": "Installing"}],
    #     ["StatusNotification", {"status": "Unavailable"}],
    #     ["FirmwareStatusNotification", {"status": "InstallationFailed"}],
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_045_1": [
    #     ["BootNotification", {}],
    #     ["Wait", "GetDiagnostics", {
    #         "startTime":datetime.datetime.now().isoformat(),
    #         "stopTime": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()}],
    #     ["Reply", "GetDiagnostics"],
    #     ["DiagnosticsStatusNotification", {"status":"Uploading"}],
    #     ["DiagnosticsStatusNotification", {"status":"Uploaded"}],
    # ],
    # "TC_045_2": [
    #     ["BootNotification", {}],
    #     ["Wait", "GetDiagnostics", {
    #         "location":"",
    #         "startTime": datetime.datetime.now().isoformat(),
    #         "stopTime": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()}],
    #     ["Reply", "GetDiagnostics"],
    #     ["DiagnosticsStatusNotification", {"status": "Uploading"}],
    #     ["DiagnosticsStatusNotification", {"status": "UploadFailed"}],
    # ],
    # "TC_046": [
    #     ["BootNotification", {"chargePointSerialNumber": "EVSCA070008"}],
    #     ["Wait", "ReserveNow", {
    #         "connectorId":1,
    #         "expiryDate":(datetime.datetime.now() + datetime.timedelta(days=1)).isoformat(),
    #         "idTag":"1031040000069641",
    #         "reservationId":3213123 }],
    #     ["Reply", "ReserveNow", {"status":"Accepted"}],
    #     ["StatusNotification", {"status": "Reserved"}],
    #     ["Authorize", {"idTag": "1031040000069642"}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["StartTransaction", {"reservationId": 3213123, "idTag": "1031040000069642"}],
    #     ["StatusNotification", {"status": "Charging"}],
    # ],
    # "TC_047": [
    #     ["BootNotification", {}],
    #     ["Wait", "ReserveNow", {
    #         "connectorId": 1,
    #         "expiryDate": (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat(),
    #         "idTag": "1031040000069641",
    #         "reservationId": 3213123}],
    #     ["Reply", "ReserveNow", {"status":"Accepted"}],
    #     ["StatusNotification", {"status": "Reserved"}],
    #     ["Authorize", {"idTag": "1031040000069642"}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["StartTransaction", {"reservationId": 3213123, "idTag": "1031040000069642"}],
    #     ["StatusNotification", {"status": "Charging"}],
    # ],
    # "TC_048_1": [
    #     ["BootNotification", {}],
    #     ["Wait", "ReserveNow", {
    #         "connectorId": 1,
    #         "expiryDate": (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat(),
    #         "idTag": "1031040000069641",
    #         "reservationId": 3213123}],
    #     ["Reply", "ReserveNow", {"status": "Faulted"}],
    # ],
    # "TC_048_2": [
    #     ["BootNotification", {}],
    #     ["Wait", "ReserveNow", {
    #         "connectorId": 1,
    #         "expiryDate": (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat(),
    #         "idTag": "1031040000069641",
    #         "reservationId": 3213123}],
    #     ["Reply", "ReserveNow", {"status": "Occupied"}],
    # ],
    # "TC_048_3": [
    #     ["BootNotification", {}],
    #     ["Wait", "ReserveNow", {
    #         "connectorId": 1,
    #         "expiryDate": (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat(),
    #         "idTag": "1031040000069641",
    #         "reservationId": 3213123}],
    #     ["Reply", "ReserveNow", {"status": "Unavailable"}],
    # ],
    # "TC_048_4": [
    #     ["BootNotification", {}],
    #     ["Wait", "ReserveNow", {
    #         "connectorId": 1,
    #         "expiryDate": (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat(),
    #         "idTag": "1031040000069641",
    #         "reservationId": 3213123}],
    #     ["Reply", "ReserveNow", {"status": "Rejected"}],
    # ],
    # "TC_049": [
    #     ["BootNotification", {}],
    #     ["Wait", "ReserveNow", {
    #         "connectorId": 0,
    #         "expiryDate": (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat(),
    #         "idTag": "1031040000069641",
    #         "reservationId": 3213123}],
    #     ["Reply", "ReserveNow", {"status": "Reserved"}],
    # ],
    # "TC_051": [
    #     ["BootNotification", {}],
    #     ["Wait", "ReserveNow", {
    #         "connectorId": 1,
    #         "expiryDate": (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat(),
    #         "idTag": "1031040000069641",
    #         "reservationId": 3213123}],
    #     ["Reply", "ReserveNow", {"status": "Accepted"}],
    #     ["StatusNotification", {"status": "Reserved"}],
    #     ["Wait", "CancelReservation", {
    #         "reservationId": 3213123}],
    #     ["Reply", "CancelReservation", {"status": "Accepted"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_052": [
    #     ["BootNotification", {}],
    #     ["Wait", "ReserveNow", {
    #         "connectorId": 1,
    #         "expiryDate": (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat(),
    #         "idTag": "1031040000069641",
    #         "reservationId": 3213123}],
    #     ["Reply", "ReserveNow", {"status": "Accepted"}],
    #     ["StatusNotification", {"status": "Reserved"}],
    #     ["Wait", "CancelReservation", {
    #         "reservationId": 3213124}],
    #     ["Reply", "CancelReservation", {"status": "Rejected"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_053": [
    #     ["BootNotification", {}],
    #     ["Wait", "ReserveNow", {
    #         "connectorId": 1,
    #         "expiryDate": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat(),
    #         "idTag": "1031040000069641",
    #         "reservationId": 120532459}],
    #     ["Reply", "ReserveNow", {"status": "Accepted"}],
    #     ["StatusNotification", {"status": "Reserved"}],
    #     ["StatusNotification", {"status": "Preparing"}],
    #     ["Authorize", {"idTag":"1010010195158522"}],
    #     ["StartTransaction", {"reservationId": 120532459, "idTag": "1010010195158522", "timestamp":datetime.datetime.utcnow().isoformat()}],
    #     ["StatusNotification", {"status": "Charging"}],
    #     ["Authorize", {"idTag": "1010010201665544"}],
    #     ["StopTransaction", {}],
    #     ["StatusNotification", {"status": "Finishing"}],
    #     ["StatusNotification", {"status": "Available"}],
    # ],
    # "TC_054": [
    #     ["BootNotification", {}],
    #     ["Wait", "TriggerMessage", {"requestedMessage": "BootNotification"}],
    #     ["Reply", "TriggerMessage", {"status": "Accepted"}],
    #     ["BootNotification", {}],
    #     ["Wait", "TriggerMessage", {"requestedMessage": "MeterValues"}],
    #     ["Reply", "TriggerMessage", {"status": "Accepted"}],
    #     ["MeterValues", {}],
    #     ["Wait", "TriggerMessage", {"requestedMessage": "HeartBeat"}],
    #     ["Reply", "TriggerMessage", {"status": "Accepted"}],
    #     ["HeartBeat", {}],
    #     ["Wait", "TriggerMessage", {"requestedMessage": "StatusNotification"}],
    #     ["Reply", "TriggerMessage", {"status": "Accepted"}],
    #     ["StatusNotification", {"status":"Available"}],
    #     ["Wait", "TriggerMessage", {"requestedMessage": "DiagnosticsStatusNotification"}],
    #     ["Reply", "TriggerMessage", {"status": "Accepted"}],
    #     ["DiagnosticsStatusNotification", {"status": "Idle"}],
    #     ["Wait", "TriggerMessage", {"requestedMessage": "FirmwareStatusNotification"}],
    #     ["Reply", "TriggerMessage", {"status": "Accepted"}],
    #     ["FirmwareStatusNotification", {"status": "Idle"}],
    # ],
    # "TC_055": [
    #     ["BootNotification", {}],
    #     ["Wait", "TriggerMessage", {"requestedMessage": "MeterValues"}],
    #     ["Reply", "TriggerMessage", {"status": "Rejected"}],
    # ],
    # "TC_056": [
    #     ["BootNotification", {}],
    #     ["Wait", "SetChargingProfile", {}],
    #     ["Reply", "SetChargingProfile", {"status": "Accepted"}],
    # ],
    # "TC_057": [
    #     ["BootNotification", {}],
    #     ["StatusNotification", {"status":"Preparing"}],
    #     ["Authorize", {"idTag":"1031040000069641"}],
    #     ["StartTransaction", {}],
    #     ["StatusNotification",{"status":"Charging"}],
    #     ["Wait", "SetChargingProfile", {}],
    #     ["Reply", "SetChargingProfile", {"status": "Accepted"}],
    # ],
    # "TC_066": [
    #     ["BootNotification", {}],
    #     ["Wait", "SetChargingProfile", {}],
    #     ["Reply", "SetChargingProfile", {"status": "Accepted"}],
    #     ["Wait", "GetCompositeSchedule", {}],
    #     ["Reply", "GetCompositeSchedule", {
    #         "status": "Accepted",
    #         "chargingSchedule": {
    #               "duration": 300,
    #               "chargingRateUnit": "W",
    #               "chargingSchedulePeriod": [
    #                 {
    #                   "startPeriod": 0,
    #                   "limit": 11000
    #                 }
    #               ]
    #             }
    #       }],
    # ],
    # "TC_067": [
    #     ["BootNotification", {}],
    #     ["Wait", "ClearChargingProfile", {}],
    #     ["Reply", "ClearChargingProfile", {"status": "Accepted"}],
    #     ["Wait", "GetCompositeSchedule", {"status":"Accepted"}],
    # ]
}
ocppDocs = {
    "BootNotification": [
        2,
        "19223201",
        "BootNotification",
        {
            "chargePointModel": "$crgr_mdl",
            "chargePointVendor": "EVAR",
            "chargePointSerialNumber": "$crgr_sno",
            #"firmwareVersion": "0.0.13",
            # "imsi": "450061222990181"
        }
    ],
    "StatusNotification": [
        2,
        "19223201",
        "StatusNotification",
        {
            "connectorId": 1,
            "errorCode": "NoError",
            "status": "Available"
        }
    ],
    "HeartBeat": [
        2,
        "19223201",
        "DataTransfer",
        {
            "vendorId": "EVAR",
            "messageId": "heartbeat",
            "data": {}
        }
    ],
    "Authorize": [
        2,
        "19223201",
        "Authorize",
        {
            "idTag": ""
        }
    ],
    "StartTransaction": [
        2,
        "1677223618",
        "StartTransaction",
        {
            "connectorId": 1,
            "idTag": "$idTag1",
            "meterStart": 24000,
            "timestamp":datetime.datetime.utcnow().isoformat("T", "seconds")+'Z'
        }
    ],
    "MeterValues": [
        2,
        "1677228049",
        "MeterValues",
        {
            "connectorId": 1,
            "transactionId": 120532006,
            "meterValue": [
                {
                    "timestamp": datetime.datetime.utcnow().isoformat("T", "seconds")+'Z',
                    "sampledValue": [
                        {
                            "value": "25000",
                            "measurand": "Energy.Active.Import.Register",
                            "unit": "Wh"
                        }
                    ]
                }
            ]
        }
    ],
    "StopTransaction": [
        2,
        "1677228103",
        "StopTransaction",
        {
            "meterStop": 29000,
            "timestamp": datetime.datetime.utcnow().isoformat("T", "seconds")+'Z',
            "transactionId": 120532006
        }
    ],
    "ClearCache":[
        2,
        "123123123",
        "ClearCache",
        {
        }
    ],
    "ClearCacheResponse": [
        3,
        "2023-02-24T08:41:42.615Z",
        {
            "status": "Accepted"
        }
    ],
    "ResetResponse": [
        3,
        "2023-02-24T08:41:42.615Z",
        {
            "status": "Accepted"
        }
    ],
    "UnlockConnectorResponse": [
        3,
        "2023-02-24T08:41:42.615Z",
        {
            "status": "Unlocked"
        }
    ],
    "GetConfigurationResponse": [
        3,
        "123214123123",
        {
            "configurationKey": [{
                "key": "heartbeatInterval",
                "readonly": "true"
            }
            ]
        }
    ],
    "RemoteStartTransaction": [
        2,
        "321312312",
        "RemoteStartTransaction",
        {
          "idTag": "$idTag1"
        }
    ],
    "RemoteStopTransaction": [
        2,
        "321312312",
        "RemoteStopTransaction",
        {
            "transactionId": 12321
        }
    ],
    "RemoteStopTransactionResponse": [
        3,
        "321312312",
        {
            "status":"Accepted"
        }
    ],
    "RemoteStartTransactionResponse": [
        3,
        "2023-02-24T08:41:42.615Z",
        {
            "status": "Accepted"
        }
    ],
    "Reset": [
        2,
        "321312312",
        "Reset",
        {
            "type": "Hard"
        }
    ],
    "UnlockConnector": [
        2,
        "321312312",
        "UnlockConnector",
        {
            "connectorId": 1
        }
    ],
    "GetConfiguration": [
        2,
        "321312312",
        "GetConfiguration",
        {
            "key": [""]
        }
    ],
    "GetLocalListVersion": [
        2, "321312312", "GetLocalListVersion",
        {}
    ],
    "GetLocalListVersionResponse": [
        3, "321312312", {"listVersion": -1}
    ],
    "ChangeConfiguration": [
        2,
        "321312312",
        "ChangeConfiguration",
        {
            "key": "UnknownConfigurationKey",
            "value": "300"
        }
    ],
    "ChangeConfigurationResponse": [
        3, "321312312", {"status":"Accepted"}
    ],
    "ChangeAvailability": [
        2,
        "321312312",
        "ChangeAvailability",
        {
            "type": "Operative"
        }
    ],
    "ChangeAvailabilityResponse": [
        2,
        "321312312",
        {
            "status": "Accepted"
        }
    ],
    "SendLocalList": [
        2,
        "321312312",
        "SendLocalList",
        {
            "listVersion":0,
            "updateType":"Full"
        }
    ],
    "SendLocalListResponse": [
        3,
        "321312312",
        {
            "status":""
        }
    ],
    "UpdateFirmware": [
        2,
        "321312312",
        "UpdateFirmware",
        {
            "location": "https://s3~~~~",
            "retrieveDate": "2023-04-15T10:15:00Z"
        }
    ],
    "UpdateFirmwareResponse": [
        3,
        "321312312",
        {
        }
    ],
    "FirmwareStatusNotification": [
        2,
        "321312312",
        "FirmwareStatusNotification",
        {
            "status":"Downloading"
        }
    ],
    "GetDiagnostics": [
        2,
        "321312312",
        "GetDiagnostics",
        {
            "location": "s3://~~"
        }
    ],
    "GetDiagnosticsResponse": [
        3,
        "321312312",
        {
            "filename": "filename_diagnostics"
        }
    ],
    "DiagnosticsStatusNotification": [
        2,
        "321312312",
        "DiagnosticsStatusNotification",
        {
            "type": "Idle"
        }
    ],
    "DiagnosticsStatusNotificationResponse": [
        3,
        "321312312",
        {
            "type": "Idle"
        }
    ],
    "ReserveNow": [
        2,
        "321312312",
        "ReserveNow",
        {
            "connectorId":1,
            "expiryDate":"",
            "idTag":"$idTag1",
            "reservationId":""
        }
    ],
    "ReserveNowResponse": [
        3,
        "321312312",
        {
            "status":""
        }
    ],
    "CancelReservation": [
        2,
        "321312312",
        "CancelReservation",
        {
            "reservationId": ""
        }
    ],
    "CancelReservationResponse": [
        2,
        "321312312",
        {
            "status": ""
        }
    ],
    "TriggerMessage": [
        2,
        "321312312",
        "TriggerMessage",
        {
            "requestedMessage": "BootNotification"
        }
    ],
    "TriggerMessageResponse": [
        2,
        "321312312",
        {
            "status": "Accepted"
        }
    ],
    "SetChargingProfile":[
        2,
        "2323242423",
        "SetChargingProfile",
        {
          "connectorId": 1,
          "csChargingProfiles": {
            "chargingProfileId": 100,
            "stackLevel": 0,
            "chargingProfilePurpose": "TxDefaultProfile",
            "chargingProfileKind": "Absolute",
            "chargingSchedule": {
              "duration": 300,
              "chargingRateUnit": "W",
              "chargingSchedulePeriod": [
                {
                  "startPeriod": 0,
                  "limit": 11000.0
                }
              ]
            }
          }
        }
      ],
    "SetChargingProfileResponse": [
        3,
        "321312312",
        {
            "status": "Accepted"
        }
    ],
    "GetCompositeSchedule": [
        2,
        "321312312",
        "GetCompositeSchedule",
        {
            "connectorId":1,
            "duration":300
        }
    ],
    "GetCompositeScheduleResponse": [
        3,
        "321312312",
        {
            "status": "Accepted",
            "chargingSchedule": {
                "duration": 300,
                "chargingRateUnit": "W",
                "chargingSchedulePeriod": [
                    {
                        "startPeriod": 0,
                        "limit": 11000
                    }
                ]
            }
        }
    ],
    "ClearChargingProfile": [
        3,
        "321312312",
        "ClearChargingProfile",
        {
            "id": 100
        }
    ],
    "ClearChargingProfileResponse": [
        3,
        "321312312",
        {
            "status": "Accepted"
        }
    ],
}