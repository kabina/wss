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
import urllib3
import tkinter as tk
from tkinter import *
import timeit
from collections import deque
import ChargerUtil
from ChargerUtil import checkSchema, tc_render, message_map, Config, DataTransferMessage
lock = asyncio.Lock()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

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
TAGS = {REQUEST:"", RESPONSE:"Response"}
# timestamp= datetime.utcnow().isoformat()

def change_text(obj, text):
    obj.delete(0, END)
    obj.insert(0, text)


class Charger() :

    def __init__(self, config):
        self.req_message_history = {}
        self.ws = None
        self.transactionId = 0
        self.reserved = False
        self.rmessageId = None
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
        self.interval = 300
        self.en_vendor = config.en_vendor

        self.arr_messageid = {
            "$uuid":str(uuid.uuid4()),
            "$timestamp":datetime.now().isoformat(sep="T", timespec="seconds")+'Z'
        }
        self.charger_configuration = json.loads(open("config.json","r", encoding='cp949').read())
    def log(self, log, attr=None):
        from datetime import datetime
        if attr:
            self.txt_recv.tag_config(attr, foreground=attr)
        if log :
            self.txt_recv.insert(END, datetime.now().isoformat() +' '+ log + '\n', attr)

    def change_result(self, idx, res):
        self.result[idx] = res

    def stop(self):
        self.status = -1

    def update_config(self, config):
        self.config = config
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
            wss_url = f'{self.config.wss_url}/{self.mdl}/{self.config.rsno}'
        else:
            wss_url = f'{self.config.wss_url}/{self.mdl}/{self.config.sno}'
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
            self.log(err)
            self.log(" 연결에 실패했습니다", attr="red")

        await asyncio.sleep(5)
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

    async def sendReply(self, ocpp):
        """
        응답전문 발송
        :param ocpp: 응답전문 본체
        :return: None
        """
        ocpp = self.req_message_history[ocpp[1]]
        if "transactionId" in ocpp[2] and self.transactionId > 0:
            ocpp[2]["transactionId"] = self.transactionId
        elif "reservationId" in ocpp[2] :
            ocpp[2]["reservationId"]=self.en_reserve

        await self.ws.send(json.dumps(ocpp))

        self.log(f" >> Reply {ocpp}", attr='blue')
        noused = await self.ws.recv()
        if noused :
            await self.post_proc(noused)
            self.log(f" << Check Response for Reply |{noused}|")
        else :
            self.log(f" << Check Response for Reply |{noused}|")

    def convertDocs(self, doc):
        for k in self.confV:
            tc_render(doc, k, self.confV[k])
        return doc

    def convertDTDocs(self, doc, messageid):
        """
        DataTransfer Message처리
        :param doc:
        :return:
        """
        for k in self.confV:
            dt_render(DataTransferMessage[messageid], k, self.confV[k])
        return doc

    def convertSendDoc(self, ocpp, uid=None, options=REQUEST) -> dict:
        """
        송신전문 변환
         1. 전문 템플릿 변환
         2. TC내 지정 전문 변환
         3. MessageID처리
        :param ocpp:
        :return:
        """
        self.confV["$meter"] = self.en_meter.get()
        self.confV["$transactionId"] = self.en_tr.get()
        doc = json.loads(self.ocppdocs)[ocpp[0]]
        """전문 템플릿 변환"""

        doc[options] = self.convertDocs(doc[options])
        """TC내 지정 전문 변환"""
        ocpp[1] = self.convertDocs(ocpp[1])
        import uuid
        for c in ocpp[1].keys():
            doc[options][c] = ocpp[1][c]
        """messageId 처리"""
        doc[1] = uid if uid else str(uuid.uuid4())

        # if doc[1] in self.arr_messageid.keys() :
        #     doc[1] = self.arr_messageid[doc[1]]
        # else :
        #     doc[1] = f'{str(uuid.uuid4())}'

        """ doc가 datatransfer인 경우 문서 추가 렌더링"""
        if "messageId" in ocpp[1] :
            ddoc = ocpp[1]
            for k in self.confV:
                tc_render(ddoc, k, self.confV[k])
            del ddoc["messageId"]
            doc[3]["data"] = ddoc

        return doc

    async def sendDocs(self, doc):

        await self.ws.send(json.dumps(doc))
        self.req_message_history[doc[1]] = doc
        print(doc)
        self.log(f' >> {doc[2]}:{doc}', attr='blue')
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
                    await self.post_proc(recv)

                #return jrecv


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


    async def callbackRequest(self, doc):
        rest_url = self.config.rest_url
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
                    schema_check = checkSchema(c[1], recv[3], self.testschem.get())
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

                    schema_check = checkSchema(f"{c[0]}", doc[3], self.testschem.get()) if c[0]!="DataTransfer" else (True, "DataTransfer는 스키마 체크 하지 않음")
                    if not schema_check[0] :
                        result = f" Fail ( Invalid testcase sending message from server. {schema_check[1]} )"
                        scases.append(case)
                        self.change_list(case, f"{case} (Fail)", attr={'fg':'red'}, log=result)
                        break
                    recv = await self.sendDocs(doc)
                    schema_check = checkSchema(f"{c[0]}", doc[3], self.testschem.get()) if c[0]!="DataTransfer" else (True, "DataTransfer는 스키마 체크 하지 않음")
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

    async def post_proc(self, msg):
        """
        응답메시지를 만들어서 송신 함
        :param msg:
        :return:
        """
        jmsg = json.loads(msg)
        inprog_name = jmsg[2]
        if len(jmsg)==3 or isinstance(inprog_name,dict) or inprog_name not in self.ocppdocs :
            print(f'jmsg {jmsg}')
            print(f'reqmsg {self.req_message_history}')
            if jmsg[1] in self.req_message_history :
                self.log(f' << {self.req_message_history[jmsg[1]][2]}:{msg}', attr='blue')
            return None
        self.rmessageId = jmsg[1]
        self.log(f' << {jmsg[2]}:{msg}', attr='blue')
        senddoc = self.convertSendDoc([f'{inprog_name}Response', {}], uid=jmsg[1], options=RESPONSE)
        if inprog_name == "RemoteStartTransaction" and self.charger_status != "Charging":
            senddoc[2]["status"] = "Rejected"
            self.transactionId = int (jmsg[3]["chargingProfile"]["transactionId"])
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
        recvdoc = await self.sendReply(senddoc)

        return recvdoc

    def get_diag_info(self):
        """충전기 진단 메시지 생성
        """
        diag_info = ChargerUtil.diag_info
        diag_info["chargeBoxSerialNumber"] = self.config.sno
        diag_info["chargePointModel"] = self.mdl
        diag_info["vendorErrorCode"] = "ERR - 001"
        return diag_info


    async def process_message(self, recvdoc):
        """
        기본적으로 CSMS에서 요청하는 작업을 수행 함
        충전 중 또는 연결된 작업 진행 중 메시지 수신이 오는 경우 처리 로직(Recursive)
        :param recvdoc:
        :return:
        """
        message = json.loads(recvdoc)
        send_recv_type, message_name = (REQUEST, message[2]) if len(message) == 4 else (RESPONSE, "")
        if send_recv_type == REQUEST:
            # 응답메시지 송신
            # await self.post_proc(recvdoc)
            # 후속 처리가 필요한지에 따라 추가 처리
            if message_name in message_map :
                for idx, c in enumerate(message_map[message_name]):
                    doc = self.convertSendDoc(c)
                    print(f'cout : {idx} total size : {len(message_map[message_name])}')
                    if c[0] == "MeterValues" :
                        if self.transactionId > 0 and self.charger_status == "Charging":
                            v = int(self.en_meter.get()) + 999
                            self.en_meter.delete(0, END)
                            self.en_meter.insert(0, v)
                            doc[3]["meterValue"][0]["sampledValue"][0]["value"] = str(v)
                            await asyncio.sleep(5)
                        else:
                            break
                    elif c[0] == "StopTransaction" :
                        doc[3]["meterStop"] = self.en_meter.get()
                    elif c[0] == "StatusNotification" :
                        self.charger_status = doc[3]["status"]


                    print(f'doc:{doc}')
                    jrecv = await self.sendDocs(doc)
                    print(f'jrecv:{jrecv}')


                    try:
                        """CSMS로 요청 후 리턴값에 대한 예외 처리"""
                        if jrecv and len(jrecv)==3 and c[0] in ("Authorize", "StartTransaction", "StopTransaction") and doc[1] == jrecv[
                            1] and jrecv[2]["idTagInfo"]["status"] != "Accepted":
                            self.log(f"Auth, Start, Stop 오류 jrecv")
                            break
                        recvdoc = await asyncio.wait_for(self.ws.recv(), timeout=2.0)
                        print(f'newmsg:{recvdoc}')
                        if recvdoc :
                            inprog_name = json.loads(recvdoc)[2]
                            jrecvdoc = json.loads(recvdoc)
                            print(recvdoc)
                            if len(json.loads(recvdoc)) == 4 :
                                self.req_message_history[jrecvdoc[1]] = jrecvdoc
                                await self.post_proc(recvdoc)
                            if inprog_name == "Reset":
                                await self.ws.close()
                                break
                            else:
                                await self.process_message(recvdoc)
                    except KeyError:
                        print("REQ UUID 없는 RES")
                    except asyncio.TimeoutError:
                        print("TimeoutError")
                        await asyncio.sleep(1)

    async def standalone(self, cases):
        """
        전문 처리, 선택된 TC셋을 받아 TC시나리오 내 개별 TC를 처리
        :param cases: 전문 셋(TC별 전문)
        :return: None
        """
        self.status = 0

        cur_idx = self.lst_cases.curselection()
        cur_idx = cur_idx[0] if cur_idx else 0
        self.lst_cases.selection_clear(cur_idx+1,END)
        import time, requests
        start_time = time.time()

        while(True) :
            print(f'송수신 히스토리 수:{len(self.req_message_history)}')
            try:
                cur_time = time.time()
                if (cur_time - start_time ) < 1 :
                    time.sleep(1)

                """충전기 최초 부팅 후 StatusNotification까지 수행
                """
                if self.ws is None or self.ws.closed:
                    await self.conn("TC_02_ColdBoot", type="standalone")
                    doc = self.convertSendDoc(["BootNotification",{}])
                    recvdoc = await self.sendDocs(doc)
                    if (recvdoc[2]["status"] == "Pending") :
                        time.sleep(self.interval)
                    else :
                        if (recvdoc[2]["status"] == "Reserved"):
                            self.reserved = True

                        doc = self.convertSendDoc(["StatusNotification",{"status":"Available"}])
                        recvdoc = await self.sendDocs(doc)
                else :
                    """CSMS로부터 Request요청 처리
                    """
                    try :
                        recvdoc = await asyncio.wait_for(self.ws.recv(), timeout=1.0)

                        message = json.loads(recvdoc)
                        message_name = message[2]
                        if len(message) == 3:
                            await self.post_proc(recvdoc)
                        else :

                            if message_name == "TriggerMessage":
                                message_name = message[3]["requestedMessage"]
                                doc = self.convertSendDoc([message_name, {}])
                                recvdoc = await self.sendDocs(doc)
                            elif message_name == "GetDiagnostics":
                                location = message[3]["location"]
                                diaginfo = self.get_diag_info()
                                filename = location.split('?')[0].split('/')[-1]
                                with open(filename, "w") as fd:
                                    fd.write(json.dumps(diaginfo))

                                header = {
                                    "Content-Type": "text/plain",
                                    "Accept":"*/*",
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
                            else:
                                print(f'IN WHILE: {recvdoc}')
                                self.req_message_history[message[1]] = message
                                await self.post_proc(recvdoc)
                                if message_name in message_map:
                                    await self.process_message(recvdoc)
                                start_time = cur_time

                            await asyncio.sleep(1)
                    except asyncio.TimeoutError:
                        await asyncio.sleep(2)
                        """Interval동안 아무런 메시지가 수신되지 않았을 경우 Heartbeat 송신
                        """
                        if (cur_time - start_time) > self.interval :
                            senddoc = self.convertSendDoc(["Heartbeat",{}])
                            recvdoc = await self.sendDocs(senddoc)
                            start_time = cur_time

            except Exception as e:
                import traceback
                print(traceback.print_exc())
                print(self.req_message_history)
                await asyncio.sleep(1)

        # for idx, case in enumerate(cases.keys()):
        #     inner_step_count = 0
        #     await self.conn(case)
        #     if self.status == -1 :
        #         break
        #     self.log("+===========================================================", attr='green')
        #     self.log(f"Testing... [{case}]", attr='green')
        #     self.log("+===========================================================", attr='green')
        #     change_text(self.en_tc, case)
        #     self.lst_cases.see(cur_idx+idx)
        #     if 0 != (cur_idx+idx):
        #         self.lst_cases.selection_clear(0, cur_idx+idx)
        #     self.lst_cases.select_set(cur_idx+idx)
        #
        #     ilen = len(cases[case])
        #     elapsed_time_most = 0
        #     for idx2, c in enumerate(cases[case]):
        #
        #         """일반TC에서는 전문 Client직접접속 버튼 해제"""
        #         self.bt_direct_send['state'] = tk.DISABLED
        #         self.lb_mode_alert['text'] =""
        #
        #         inner_step_count += 1
        #         self.lst_tc.selection_clear(0, 'end')
        #         self.lst_tc.select_set(step_count)
        #         self.lst_tc.itemconfig(step_count, {'fg': 'green'})
        #         step_count += 1
        #         """ Progress bar Update"""
        #         self.curProgress.set(step_count / case_cnt*100)
        #         self.progressbar.update()
        #         self.lst_tc.see(step_count)
        #         self.txt_recv.see(END)
        #         start_time = timeit.default_timer()
        #         if c[0] == "Wait" :
        #             self.log(f" Waiting message from CSMS [{c[1]}] ...", attr='green')
        #
        #             if self.test_mode == 1:
        #                 doc = json.loads(self.ocppdocs)[c[1]]
        #                 if len(c) > 2:
        #                     for d in c[2].keys():
        #                         doc[3][d] = c[2][d]
        #
        #                 await self.callbackRequest( doc)
        #
        #         elif c[0] == "Reply":
        #             recv = await self.waitMessages()
        #             if recv == None :
        #                 scases.append(case)
        #                 result = " None response from server. test case failed"
        #                 self.change_list(case, f"{case} (Fail)", attr={'fg': 'red'}, log=result)
        #
        #                 break
        #             schema_check = checkSchema(c[1], recv[3], self.testschem.get())
        #             if not schema_check[0]:
        #                 result = f" Fail ( Invalid testcase message from server, expected ({schema_check[1]})"
        #                 scases.append(case)
        #                 self.change_list(case, f"{case} (Fail)", attr={'fg':'red'}, log=result)
        #                 break
        #             else:
        #                 senddoc = json.loads(self.ocppdocs)[f"{recv[2]}Response"]
        #                 senddoc[1] = recv[1]
        #                 if len(c)>2 :
        #                     for d in c[2].keys() :
        #                         senddoc[2][d]=c[2][d]
        #                 await self.sendReply(senddoc)
        #         else :
        #             doc = self.convertSendDoc(c)
        #
        #             self.txt_tc.delete(1.0, END)
        #             self.txt_tc.insert(END, json.dumps(doc, indent=2))
        #
        #             schema_check = checkSchema(f"{c[0]}", doc[3], self.testschem.get())
        #             if not schema_check[0] :
        #                 result = f" Fail ( Invalid testcase sending message from server. {schema_check[1]} )"
        #                 scases.append(case)
        #                 self.change_list(case, f"{case} (Fail)", attr={'fg':'red'}, log=result)
        #                 break
        #             recv = await self.sendDocs(doc)
        #             schema_check = checkSchema(f"{c[0]}Response", recv[2], self.testschem.get())
        #             if not schema_check[0]:
        #                 result = f" Fail ( Invalid testcase recv message from server. {schema_check[1]} )"
        #                 scases.append(case)
        #                 self.change_list(case, f"{case} (Fail)", attr={'fg':'red'}, log=result)
        #                 break
        #             if len(c)>2 and recv[0]==3:
        #                 chk = self.recv_check(recv[2], c[2])
        #                 if not chk[0]:
        #                     result = f" Fail ( Not expected response from server(expected: {chk[1]}. ))"
        #                     scases.append(case)
        #                     self.change_list(case, f"{case} (Fail)", attr={'fg': 'red'}, log=result)
        #                     break
        #         elapsed_time = timeit.default_timer() - start_time
        #         if elapsed_time > elapsed_time_most :
        #             elapsed_time_most = elapsed_time
        #
        #         if idx2 == (ilen-1) :
        #             self.change_list(case, f"{case} (Pass, {elapsed_time_most})", attr={'fg':'blue'}, log="Passed")
        #     step_count += (ilen-inner_step_count)
        #     """ Progress bar Update(TC별 오류로 미처리된 STEP처리"""
        #     self.curProgress.set(step_count / case_cnt * 100)
        #     self.progressbar.update()
        #     self.lst_tc.see(step_count)
        #
        #     await self.close()
        #
        # self.log(f" Total {len(cases)} cases tested and {len(cases)-len(scases)} cases succeed. Failed cases are as follows", attr='green')
        # self.log(" ==========================================================================", attr='green')
        # for c in scases:
        #     self.log(f" {c}", attr='green')
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
