import asyncio
import logging
import ssl
from socket import socket
import websockets
import json
import uuid
from colorlog import ColoredFormatter
import urllib3
from datetime import datetime
import tkinter as tk
from tkinter import *
import timeit
import time
from collections import deque
import ChargerUtil
from ChargerUtil import checkSchema, tc_render, message_map, Config, DataTransferMessage, RequestMessages
lock = asyncio.Lock()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
SCHEMA_CHECK = True

formatter = ColoredFormatter(
    "%(log_color)s[%(asctime)s] %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'white,bold',
        'INFOV':    'cyan,bold',
        'WARNING':  'yellow',
        'ERROR':    'red,bold',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)
ch.setFormatter(formatter)

logger = logging.getLogger('attcap')
logger.setLevel(logging.DEBUG)
logger.handlers = []       # No duplicated handlers
logger.propagate = False   # workaround for duplicated logs in ipython
logger.addHandler(ch)

logging.addLevelName(logging.INFO + 1, 'INFOV')

REQUEST = 3
RESPONSE = 2
SERVER = "dev"
TAGS = {REQUEST:"", RESPONSE:"Response"}
# timestamp= datetime.utcnow().isoformat()

def change_text(obj, text):
    obj.delete(0, END)
    obj.insert(0, text)



class Charger() :

    def __init__(self, config):
        self.start_time = time.time()
        self.ws = None
        self.charger_status = None
        self.transactionId = 0
        self.reserved = False
        self.rmessageId = None
        self.soc = 20
        self.logger = logger
        self.config = config
        self.en_tr = config.en_tr
        self.en_tc = config.en_tc
        self.lst_cases = config.lst_cases
        self.en_status = config.en_status
        self.txt_recv = config.txt_recv
        self.cid = config.cid
        self.rcid = config.rcid
        self.mdl = config.mdl
        self.result = config.result
        self.status = 0
        self.confV = config.confV
        self.en_reserve = config.en_reserve
        self.lst_tc = config.lst_tc
        self.test_mode = config.test_mode
        self.ocppdocs = config.ocppdocs
        self.txt_tc = config.txt_tc
        self.progressbar = config.progressbar
        self.curProgress = config.curProgress
        self.bt_direct_send = config.bt_direct_send
        self.lb_mode_alert = config.lb_mode_alert
        self.testschem = config.testschem
        self.ciphersuite = config.ciphersuite
        self.en_meter = config.en_meter
        self.en_soc = config.en_soc
        self.interval = 300
        self.meter = 0
        self.en_vendor = config.en_vendor
        self.charger_meter = config.charger_meter
        self.charger_soc = config.charger_soc
        print("BEFORE REQ_MESSAGE")
        self.req_message_history = self.load_req_message_history()


        self.arr_messageid = {
            "$uuid":str(uuid.uuid4()),
            "$timestamp":datetime.now().isoformat(sep="T", timespec="seconds")+'Z'
        }
        print("AFTER REQ_MESSAGE")
        self.charger_configuration = json.loads(open("config.json","r", encoding='utf-8').read())
        print("END OF INIT")
        self.message_func_map = {
            "TriggerMessage": self.TriggerMessage
        }


    def log(self, log, attr=None):
        from datetime import datetime
        if attr:
            self.txt_recv.tag_config(attr, foreground=attr)
        if log :
            self.txt_recv.insert(END, datetime.now().isoformat() +' '+ log + '\n', attr)
        self.txt_recv.yview_moveto(1.0)
    def change_result(self, idx, res):
        self.result[idx] = res

    def stop(self):
        self.status = -1

    def update_config(self, config):
        self.config = config
        self.en_tr = config.en_tr
        self.en_tc = config.en_tc
        self.lst_cases = config.lst_cases
        self.en_status = config.en_status
        self.txt_recv = config.txt_recv
        self.cid = config.cid
        self.rcid = config.rcid
        self.mdl = config.mdl
        self.confV = config.confV
        self.en_reserve = config.en_reserve
        self.lst_tc = config.lst_tc
        self.test_mode = config.test_mode
        self.ocppdocs = config.ocppdocs
        self.txt_tc = config.txt_tc
        self.progressbar = config.progressbar
        self.curProgress = config.curProgress
        self.bt_direct_send = config.bt_direct_send
        self.lb_mode_alert = config.lb_mode_alert
        self.testschem = config.testschem
        self.ciphersuite = config.ciphersuite
        self.interval = 600
        self.en_meter = config.en_meter
        self.en_vendor = config.en_vendor
        self.en_soc = config.en_soc
        self.charger_name = self.chargers[idx]['text'],
        self.charger_status = self.chargerstatuses[idx]
        self.charger_meter = self.charger_meter[idx]
        self.charger_soc = self.charger_soc[idx]

    def change_list(self, case, text, attr=None, log=None):
        try:
            idx = self.lst_cases.get(0, "end").index(case.split()[0])
            self.lst_cases.delete(idx)
            self.lst_cases.insert(idx, text)
            fg = attr['fg'] if attr else 'blue'
            if attr:
                self.lst_cases.itemconfig(idx, attr)
            if log:
                self.result[idx] = log
            self.log(log, attr=attr['fg'])
        except Exception as e:
            pass

    async def conn(self, case, type=None):
        if len(case.split('_')) > 1 and 46 <= int(case.split('_')[1]) <= 53 :
            wss_url = f'{self.config.wss_url.replace("$server", SERVER)}/{self.mdl}/{self.config.rsno}'
        else:
            wss_url = f'{self.config.wss_url.replace("$server", SERVER)}/{self.mdl}/{self.config.sno}'
        try :
            # if type == "standalone":
            #     wss_url = "wss://192.168.0.152:8765"
            import ssl
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_3
            ssl_context.set_ciphers(
                ",".join([self.ciphersuite.get(idx)[self.ciphersuite.get(idx).index(",")+1:]
                          for idx in self.ciphersuite.curselection()])
            )
            self.ws = await websockets.connect(
                f'{wss_url}',
                subprotocols=["ocpp1.6"],
                extra_headers={"Authorization": self.config.auth_token},
                ssl=ssl_context
            )
            from OpenSSL import crypto
            import base64
            sslcontext = self.ws.transport.get_extra_info('sslcontext')
            """Server인증서 수신 및 Text 변환 출력"""
            server_cert = self.ws.transport.get_extra_info('ssl_object').getpeercert(binary_form=True)
            # X509 객체로 변환
            x509 = crypto.load_certificate(crypto.FILETYPE_ASN1, server_cert)
            # 인증서의 텍스트 형식으로 변환
            cert_text = crypto.dump_certificate(crypto.FILETYPE_TEXT, x509)
            #print(str(cert_text.decode('utf-8')))
            # base64로 인코딩하여 출력
            #print(base64.b64encode(cert_text).decode())
            cipher_list = sslcontext.get_ciphers()

            print("서버지원 가능 목록+++++++++++++++++++++++++++")
            for c in cipher_list:
                print(f'tls:{c["protocol"]}, cipher:{c["name"]}')
            protocol = self.ws.transport.get_protocol()
            if protocol is not None:
                print(protocol)
            ciphers = sslcontext.get_ciphers()

            print("클라이언트 지원 가능 목록++++++++++++++++++++++++")
            cssl_context = ssl.create_default_context()
            cipher_list= cssl_context.get_ciphers()
            for c in cipher_list:
                print(f'tls:{c["protocol"]}, cipher:{c["name"]}')

            ssl_socket =self.ws.transport.get_extra_info('ssl_object')
            protocol_version = ssl_socket.cipher()[1]
            #print(ssl_socket.cipher())


            # print("Cipher suite used in WebSocket connection:", sslopt_ciphers)
        except Exception as err:
            self.log(str(err))
            self.log(" 연결에 실패했습니다", attr="red")

        await asyncio.sleep(1)
        self.en_tr.delete(0, END)
        self.en_tr.insert(0,"Not In Transaction")

    async def close(self):
        await self.ws.close()

    async def waitMessages(self):
        self.bt_direct_send['state'] = tk.NORMAL
        self.lb_mode_alert['text'] = "충전기가 전문 수신 대기중입니다. '전문직접전송' 버튼 또는 앱/관리자페이지에서 전문을 전송 하십시오"
        try :
            while True:
                message = await asyncio.wait_for(self.ws.recv(), 600)
                message = json.loads(message)
                self.log(f" << {message[2]}:{message}", attr='blue')
                self.rmessageId = message[1]

                """ToDo: 이 위치에 서버의 명령에 따른 처리 추가 필요
                """
                return message
        except Exception as e:
            return

    def save_req_message_history(self):
        import pickle
        with open(f'req_message_history_{datetime.now().strftime("%Y-%m-%d")}', 'wb') as fd:
            pickle.dump(self.req_message_history, fd)

    def load_req_message_history(self):
        # lastest_file = RequestMessages(1000)
        prefix = "req_message_history"
        lastest_file = None
        import os
        for file in os.listdir("."):
            # 파일 이름이 prefix로 시작하고, 파일인 경우
            if file.startswith(prefix) and os.path.isfile(file):
                # latest_file이 None일 경우나 현재 파일이 latest_file보다 최신인 경우
                if latest_file is None or os.path.getmtime(file) > os.path.getmtime(latest_file):
                    latest_file = file
            if lastest_file is not None :
                with open(latest_file, 'rb') as f:
                    loaded_ordered_dict = pickle.load(f)
                    return loaded_ordered_dict
            else:
                return RequestMessages(1000)

    async def sendReply(self, ocpp):
        """
        응답전문 발송 처리
        :param ocpp: 응답전문 본체
        :return: None
        """
        await self.ws.send(json.dumps(ocpp))
        # TC Test에서는 불필요
        self.log(f' >> Reply:{ocpp}', attr='green')

    def convertDocs(self, doc):
        for k in self.confV:
            tc_render(doc, k, self.confV[k])
        return doc

    def convertSendDoc(self, ocpp, uid=None, options=REQUEST) -> dict:
        """
        송신전문 변환
         1. 전문 템플릿 변환
         2. TC내 지정 전문 변환
         3. MessageID처리
        :param ocpp: ["BootNotification, {}]  와 같은 형식
        :return:
        """
        self.confV["$meter"] = self.meter
        self.confV["$transactionId"] = self.transactionId

        doc = json.loads(self.ocppdocs)[ocpp[0]]

        print(self.cid)
        """ 고속 충전인 경우 Soc값 추가"""
        if self.cid.endswith("C") and doc[2] == "MeterValues":
            socstr = '{ "value": "'+str(self.soc)+'", "measurand": "SoC", "unit": "%" }'
            doc[3]["meterValue"][0]["sampledValue"].append(json.loads(socstr))
        print(doc)
        """전문 템플릿 변환"""

        doc[options] = self.convertDocs(doc[options])
        """TC내 지정 전문 변환"""
        ocpp[1] = self.convertDocs(ocpp[1])
        import uuid
        for c in ocpp[1].keys():
            doc[options][c] = ocpp[1][c]
        """messageId 처리"""
        doc[1] = uid if uid else str(uuid.uuid4())

        """ doc가 datatransfer인 경우 문서 추가 렌더링"""
        print(f'ocpp[1] : {ocpp[1]}')
        if "messageId" in ocpp[1] :
            ddoc = ocpp[1]
            print(f'doc : {doc[3]}')
            for k in self.confV:
                tc_render(ddoc, k, self.confV[k])
            doc[3]["messageId"]=ocpp[1]["messageId"]
            print(f'doc : {doc[3]}')

            del ddoc["messageId"]
            doc[3]["data"] = ddoc
            print(f'doc : {doc[3]}')



        return doc
    def change_status(self, status):
        self.charger_status = status
        self.config.charger_status.config(text = status)

    def change_meter(self, meter):
        self.meter = meter
        self.charger_meter.config(text = f'{self.meter} Wh')

    def change_soc(self, soc):
        self.soc = soc
        self.charger_soc.config(text = f'{self.soc} %')

    async def sendDocs(self, doc):

        await self.ws.send(json.dumps(doc))
        self.req_message_history[doc[1]] = doc
        print(doc)
        self.log(f' >> {doc[2]}:{doc}', attr='green')

        recv= await self.ws.recv()
        if recv :
            print(recv)
            jrecv = json.loads(recv)
            if len(jrecv)  == 4 :
                self.req_message_history[jrecv[1]] = jrecv
                self.log(f' << {self.req_message_history[jrecv[1]][2]}:{recv}', attr='blue')
                if jrecv[2] in message_map:
                    await self.process_message(recv)
            else:
                self.log(f' << {self.req_message_history[jrecv[1]][2]}:{recv}', attr='blue')
                if(doc[1] != jrecv[1]):
                    await self.proc_reply(recv)

            # 후처리
            if doc[2]=="StartTransaction" and jrecv[0] == 3 and "transactionId" in jrecv[2]:
                self.transactionId = jrecv[2]["transactionId"]
                self.confV["$transactionId"] = jrecv[2]["transactionId"]
                self.en_tr.delete(0,END)
                self.en_tr.insert(0,jrecv[2]["transactionId"])
                self.confV["$transactionId"] = self.transactionId

            elif doc[2]=="StopTransaction":
                self.transactionId = 0
            elif doc[2]=="BootNotification" :
                self.interval = jrecv[2]["interval"]
                self.charger_configuration["HeartbeatInterval"] = self.interval
            elif doc[2]=="StatusNotification" :
                self.charger_status = doc[3]["status"]
            return jrecv

    async def proc_message(self, recvdoc):
        jrecvdoc = json.loads(recvdoc)
        if len(jrecvdoc) == 4 :
            func = self.message_func_map.get(jrecvdoc[2])
            if func:
                await func(jrecvdoc)

    async def TriggerMessage(self, jrecvdoc):
        print(f'triggermessage : {jrecvdoc}')
        message_name = jrecvdoc[3]["requestedMessage"]
        if message_name is None or len(message_name)==0 :
            status = "Rejected"
            self.log("No Trigger Message Received", attr="red")
        else:
            status = "Accepted"
        doc = self.convertSendDoc([message_name, {"status":status}])
        await self.sendDocs(doc)
        #await proc_message(self.ocppdocs[])
        """Todo: proc_message 호출"""



    async def callbackRequest(self, doc):
        rest_url = self.config.rest_url.replace("$server",SERVER)
        import requests, uuid
        if "transactionId" in doc[3] :
            doc[3]["transactionId"] = self.transactionId
        doc[1] = f'{str(uuid.uuid4())}'
        self.convertDocs(doc)
        reqdoc = {
            "crgrMid":self.config.rcid[:11] if "Reserv" in doc[2] else self.config.cid[:11],
            "data": doc
        }

        header = {
            "Accept":"*/*",
            "Content-Type":"application/json",
            "Cache-Control":"no-cache",
        }
        self.log(f" DATA To Server >> {reqdoc} ...", attr='green')
        response = requests.post(rest_url, headers=header, data= json.dumps(reqdoc), verify=False, timeout=5).json()

    def recv_check(self, recv, target):
        for t in target.keys():
            if isinstance(target[t], dict) :
                return self.recv_check(recv[t], target[t])
            elif t in recv.keys() and target[t] != recv[t]:
                return (False, target)
        return (True, None)

    async def runcase(self, cases):
        """
        전문 처리, 선택된 TC셋을 받아 TC시나리오 내 개별 TC를 처리
        :param cases: 전문 셋(TC별 전문)
        :return: None
        """
        scases = []
        step_count = 0

        self.status = 0

        case_cnt = sum([len(cases[c]) for c in cases.keys()])
        cur_idx = self.lst_cases.curselection()
        cur_idx = cur_idx[0] if cur_idx else 0
        self.lst_cases.selection_clear(cur_idx+1,END)

        for idx, case in enumerate(cases.keys()):
            inner_step_count = 0
            await self.conn(case)
            if self.status == -1 :
                break
            self.log("+===========================================================", attr='green')
            self.log(f"Testing... [{case}]", attr='green')
            self.log("+===========================================================", attr='green')
            change_text(self.en_tc, case)
            self.lst_cases.see(cur_idx+idx)
            if 0 != (cur_idx+idx):
                self.lst_cases.selection_clear(0, cur_idx+idx)
            self.lst_cases.select_set(cur_idx+idx)

            ilen = len(cases[case])
            elapsed_time_most = 0
            for idx2, c in enumerate(cases[case]):

                """일반TC에서는 전문 Client직접접속 버튼 해제"""
                self.bt_direct_send['state'] = tk.DISABLED
                self.lb_mode_alert['text'] =""

                inner_step_count += 1
                self.lst_tc.selection_clear(0, 'end')
                self.lst_tc.select_set(step_count)
                self.lst_tc.itemconfig(step_count, {'fg': 'green'})
                step_count += 1
                """ Progress bar Update"""
                self.curProgress.set(step_count / case_cnt*100)
                self.progressbar.update()
                self.lst_tc.see(step_count)
                self.txt_recv.see(END)
                start_time = timeit.default_timer()
                if c[0] == "Wait" :
                    self.log(f" Waiting message from CSMS [{c[1]}] ...", attr='green')

                    if self.test_mode == 1:
                        doc = json.loads(self.ocppdocs)[c[1]]
                        if len(c) > 2:
                            for d in c[2].keys():
                                doc[3][d] = c[2][d]

                        await self.callbackRequest( doc)

                elif c[0] == "Reply":
                    recv = await self.waitMessages()
                    if recv == None :
                        scases.append(case)
                        result = " None response from server. test case failed"
                        self.change_list(case, f"{case} (Fail)", attr={'fg': 'red'}, log=result)

                        break
                    # schema_check = checkSchema(c[1], recv[2], self.testschem)
                    print(f'{c[1]}')
                    print(f'{recv[3]}')
                    print(f'{self.testschem}')
                    schema_check = checkSchema(c[1], recv[3], self.testschem) if SCHEMA_CHECK else (True, None)
                    if not schema_check[0]:
                        result = f" Fail ( Invalid testcase message from server, expected ({schema_check[1]})"
                        scases.append(case)
                        self.change_list(case, f"{case} (Fail)", attr={'fg':'red'}, log=result)
                        break
                    else:
                        senddoc = json.loads(self.ocppdocs)[f"{recv[2]}Response"]
                        senddoc[1] = recv[1]
                        if len(c)>2 :
                            for d in c[2].keys() :
                                senddoc[2][d]=c[2][d]
                        await self.sendReply(senddoc)
                else :
                    doc = self.convertSendDoc(c)

                    self.txt_tc.delete(1.0, END)
                    self.txt_tc.insert(END, json.dumps(doc, indent=2))
                    if SCHEMA_CHECK :
                        schema_check = checkSchema(f"{c[0]}", doc[3], self.testschem) if c[0]!="DataTransfer" else (True, "DataTransfer는 스키마 체크 하지 않음")
                    else:
                        schema_check = (True,None)
                    if not schema_check[0]:
                        result = f" Fail ( Invalid testcase sending message from server. {schema_check[1]} )"
                        scases.append(case)
                        self.change_list(case, f"{case} (Fail)", attr={'fg':'red'}, log=result)
                        break
                    recv = await self.sendDocs(doc)
                    if SCHEMA_CHECK :
                        schema_check = checkSchema(f"{c[0]}", doc[3], self.testschem) if c[0]!="DataTransfer" else (True, "DataTransfer는 스키마 체크 하지 않음")
                    else:
                        schema_check = (True,None)
                    if not schema_check[0]:
                        result = f" Fail ( Invalid testcase recv message from server. {schema_check[1]} )"
                        scases.append(case)
                        self.change_list(case, f"{case} (Fail)", attr={'fg':'red'}, log=result)
                        break
                    if len(c)>2 and recv[0]==3:
                        chk = self.recv_check(recv[2], c[2])
                        if not chk[0]:
                            result = f" Fail ( Not expected response from server(expected: {chk[1]}. ))"
                            scases.append(case)
                            self.change_list(case, f"{case} (Fail)", attr={'fg': 'red'}, log=result)
                            break
                elapsed_time = timeit.default_timer() - start_time
                if elapsed_time > elapsed_time_most :
                    elapsed_time_most = elapsed_time

                if idx2 == (ilen-1) :
                    self.change_list(case, f"{case} (Pass, {elapsed_time_most})", attr={'fg':'blue'}, log="Passed")
            step_count += (ilen-inner_step_count)
            """ Progress bar Update(TC별 오류로 미처리된 STEP처리"""
            self.curProgress.set(step_count / case_cnt * 100)
            self.progressbar.update()
            self.lst_tc.see(step_count)

            await self.close()

        self.log(f" Total {len(cases)} cases tested and {len(cases)-len(scases)} cases succeed. Failed cases are as follows", attr='green')
        self.log(" ==========================================================================", attr='green')
        for c in scases:
            self.log(f" {c}", attr='green')

    async def proc_reply(self, msg):
        """
        응답메시지를 만들어서 송신 함, 원격요청 또는 Get, Reset 요청 등
        사실상 SendReply의 메시지 전체를 생성
        :param msg: [2, 3213123123132, messageid, {}]의 형태를 가짐
        :return:
        """
        jmsg = json.loads(msg)
        inprog_name = jmsg[2] if len(jmsg) == 4 else self.req_message_history[jmsg[1]][2]

        # 서버로 부터의 단순 응답 메시지 후속 처리
        if len(jmsg)==3 and jmsg[1] in self.req_message_history :
            # self.log(f' << {inprog_name}:{msg}', attr='blue')
            # Server Response 후처리 주로 charger 내부변수 및 UI 값 변경
            orgmsg = self.req_message_history[jmsg[1]]
            if orgmsg[2] == "StartTransaction" and jmsg[0] == 3 and "transactionId" in jmsg[2]:
                self.transactionId = jmsg[2]["transactionId"]
                self.confV["$transactionId"] = jmsg[2]["transactionId"]
                self.en_tr.delete(0, END)
                self.en_tr.insert(0, jmsg[2]["transactionId"])
                self.confV["$transactionId"] = self.transactionId
            elif orgmsg[2] == "StopTransaction":
                self.transactionId = 0
                self.transactionId = 0
                self.confV["$transactionId"] = 0
                self.en_tr.delete(0, END)
                self.en_tr.insert(0, "0")
            elif orgmsg[2] == "BootNotification":
                self.interval = jmsg[2]["interval"]
                self.charger_configuration["HeartbeatInterval"] = self.interval
            elif orgmsg[2] in ( "Authorize", "StartTransaction", "StopTransaction"):
                if jmsg[1] in self.req_message_history and jmsg[1] and \
                            jmsg[2]["idTagInfo"]["status"] != "Accepted":
                    self.log(f'Authorize Error: {jmsg[2]["idTagInfo"]["status"]}', attr="red")

        # [2, ~ ] 로시작하는 메시지들에 대해 [3, ~ ]의 응답 메시지 생성 및 송신
        else :
            #self.log(f' << {jmsg[2]}:{msg}', attr='blue')
            senddoc = self.convertSendDoc([f'{inprog_name}Response', {}], uid=jmsg[1], options=RESPONSE)
            if inprog_name == "RemoteStartTransaction":
                senddoc[2]["status"] = "Accepted"
                print(f'reply:{jmsg}')
                self.transactionId = jmsg[3]["chargingProfile"]["transactionId"]
                self.confV["$transactionId"] = self.transactionId
                self.en_tr.delete(0,END)
                self.en_tr.insert(0, self.transactionId)

            elif inprog_name == "GetDiagnostics":
                senddoc[2]["filename"] = jmsg[3]["location"].split('?')[0].split('/')[-1] # location에서 filename만 가져옴
            elif inprog_name in ("GetConfiguration", "SetConfiguration"):
                keys = jmsg[3]["key"]
                charger_configuration_keys = self.charger_configuration.keys()
                key_list = []
                send_conf_keys = {}
                for k in keys:
                    if k in charger_configuration_keys:
                        send_conf_keys["key"] = k
                        send_conf_keys["readonly"] = "false"
                        key_list.append(send_conf_keys)
                    senddoc[3]["ConfigurationKey"] = key_list

            await self.sendReply(senddoc)

            # if jmsg[2] in message_map:
            #     await self.process_message(msg)
        return True

    def get_diag_info(self):
        """충전기 진단 메시지 생성
        """
        diag_info = ChargerUtil.diag_info
        diag_info["chargeBoxSerialNumber"] = self.config.sno
        diag_info["chargePointModel"] = self.mdl
        diag_info["vendorErrorCode"] = "ERR - 001"
        return diag_info

    async def proc_recvdoc(self, recvdoc):
        """
        서버로 부터의 메시지 처리/원격 요청 처리 및 Response 처리
        :param recvdoc:
        :return:
        """

        # 수신 메시지에 대한 Response 처리 (2,3  모두 Response 처리) 3은 화면 로그만 출력
        if recvdoc:
            self.start_time = time.time()
            message = json.loads(recvdoc)
            # 수신 로그 출력

            self.log(f' << {self.req_message_history[message[1]][2] if len(message)==3 else message[2]}:{recvdoc}', attr='blue')

            result = await self.proc_reply(recvdoc)
            # 진행 중 문제가 있는 경우 트랜잭션 중지
            if not result:
                senddoc = self.convertSendDoc(["StopTransaction", {"transactionId":self.transactionId}])
                await self.sendDocs(senddoc)

            if message[0] == 3:
                return True

            self.req_message_history[message[1]] = message
            message_name = message[2]
            # 메시지가 송신에 대한 응답인 경우
            print(f'proc_recvdoc:{recvdoc}')
            """recv가 2이면서 개별 처리건의 메시지의 경우 처리 """
            if message_name == "TriggerMessage":
                await self.proc_message(recvdoc)
                # fd
                # message_name = message[3]["requestedMessage"]
                # doc = self.convertSendDoc([message_name, {}])
                # recvdoc = await self.sendDocs(doc)

            elif message_name == "BootNotification":
                if (message[2]["status"] == "Pending") :
                    time.sleep(self.interval)
                else :
                    if (message[2]["status"] == "Reserved"):
                        self.reserved = True
            elif message_name == "GetDiagnostics":
                location = message[3]["location"]
                diaginfo = self.get_diag_info()
                filename = location.split('?')[0].split('/')[-1]
                with open(filename, "w") as fd:
                    fd.write(json.dumps(diaginfo))

                header = {
                    "Content-Type": "text/plain",
                    "Accept": "*/*",
                    "Slug": filename
                }
                response = requests.put(location, files={'file': json.dumps(diaginfo)}, headers=header)
            elif message_name == "UpdateFirmware":
                import re
                filename = "firmware_downloaded_file"
                location = message[3]["location"]
                header = {
                    "Content-Type": "application/json"
                }
                response = requests.get(location, allow_redirects=False, verify=False)
                original_url = response.headers.get('Location')
                filename = original_url.split("?")[0].split("/")[-1]

                response = firmware = requests.get(location, headers=header, verify=False)
                if response.status_code == 200:
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    print("파일 다운로드 완료:", filename)
                else:
                    print("파일 다운로드 실패:", response.status_code)
            elif message_name == "RemoteStartTransaction":
                if message[3]["idTag"] :
                    self.confV["idTag"] = message[3]["idTag"]

            if message_name and message_name in message_map:
                return await self.process_message(recvdoc)

            return True

    async def process_message(self, recvdoc):
        """
        기본적으로 CSMS에서 요청하는 작업을 수행 함
        충전 중 또는 연결된 작업 진행 중 메시지 수신이 오는 경우 처리 로직(Recursive)
        :param recvdoc:
        :return:
        """
        message = json.loads(recvdoc)
        send_recv_type, message_name = (REQUEST, message[2]) if len(message) == 4 else (RESPONSE, "")
        print(f'start_process_message:{recvdoc}')
        for idx, c in enumerate(message_map[message_name]):
            doc = self.convertSendDoc(c)
            print(f'Loop:{doc}')
            print(f'cout : {idx} total size : {len(message_map[message_name])}')
            if c[0] == "MeterValues" :
                if self.transactionId > 0 and self.charger_status == "Charging":
                    v = self.meter + 999
                    self.change_meter(v)
                    if self.cid.endswith("C") :
                        s = self.soc + 5
                        self.change_soc(s)
                    doc[3]["meterValue"][0]["sampledValue"][0]["value"] = str(v)
                    await asyncio.sleep(5)
                else:
                    break
            elif c[0] == "StartTransaction":
                doc[3]["meterStart"] = self.en_meter.get()
                """remote start로 시작한 경우 RemoteStartTrasaction의 chargingProfile에 있던 transactionId를 
                ReservationId에 할당
                """
                if self.transactionId > 0 :
                    doc[3]["reservationId"] = self.transactionId
            elif c[0] == "StatusNotification":
                self.change_status(doc[3]["status"])
                #self.charger_status = doc[3]["status"]

            time.sleep(2)
            print(f'doc:{doc}')
            await self.sendDocs(doc)

            try:
                """Message Map 수행 중 수신되는 메시지 처리"""
                recvdoc = await asyncio.wait_for(self.ws.recv(), timeout=2.0)
                result = await self.proc_recvdoc(recvdoc)
                print(f'Unter for result: {result}')
                if result == False :
                    break
            except KeyError:
                print("REQ UUID 없는 RES")
            except asyncio.TimeoutError:
                print("TimeoutError in progress")
                await asyncio.sleep(1)
        else:
            return True

    async def charger_init(self):
        try :
            print("In init")
            await self.ws.close()
        except Exception as e:
            pass
        print("In init")
        await self.conn("TC_02_ColdBoot", type="standalone")
        doc = self.convertSendDoc(["BootNotification", {}])
        await self.sendDocs(doc)
        await asyncio.sleep(0.5)
        recvdoc = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
        await self.proc_recvdoc(recvdoc)

        doc = self.convertSendDoc(["StatusNotification", {"status": "Available"}])
        recvdoc = await self.sendDocs(doc)
        await asyncio.sleep(0.5)
        recvdoc = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
        await self.proc_recvdoc(recvdoc)


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)
