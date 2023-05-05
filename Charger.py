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
from ChargerUtil import checkSchema, tc_render
import OpenSSL.crypto

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

# timestamp= datetime.utcnow().isoformat()

def change_text(obj, text):
    obj.delete(0, END)
    obj.insert(0, text)

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

class Charger() :
    _transactionId: int

    def __init__(self, config):
        self.ws = None
        self._transactionId = 0
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

        self.arr_messageid = {
            "$uuid":str(uuid.uuid4()),
            "$timestamp":datetime.now().isoformat(sep="T", timespec="seconds")+'Z'
        }
    def log(self, log, attr=None):
        from datetime import datetime
        if attr:
            self.txt_recv.tag_config(attr, foreground=attr)
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

    async def conn(self, case):
        if len(case.split('_')) > 1 and 46 <= int(case.split('_')[1]) <= 53 :
            wss_url = f'{self.config.wss_url}/{self.mdl}/{self.config.rsno}'
        else:
            wss_url = f'{self.config.wss_url}/{self.mdl}/{self.config.sno}'
        try :
            import ssl
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_3
            ssl_context.set_ciphers(
            'ECDHE-RSA-AES256-GCM-SHA384'
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
            print(str(cert_text.decode('utf-8')))
            # base64로 인코딩하여 출력
            print(base64.b64encode(cert_text).decode())
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
            print(ssl_socket.cipher())


            # print("Cipher suite used in WebSocket connection:", sslopt_ciphers)
        except Exception as err:
            self.log(err)
            self.log(" 연결에 실패했습니다", attr="red")

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
        ocpp[1] = self.rmessageId
        if "transactionId" in ocpp[2] and self._transactionId > 0:
            ocpp[2]["transactionId"] = self._transactionId
        elif "reservationId" in ocpp[2] :
            ocpp[2]["reservationId"]=self.en_reserve
        await self.ws.send(json.dumps(ocpp))
        self.log(f" >> Reply {ocpp}", attr='blue')
        noused = await self.ws.recv()
        self.log(f" << Check Response for Reply |{noused}|")

    def convertDocs(self, doc):
        for k in self.confV:
            tc_render(doc, k, self.confV[k])
        return doc

    def convertSendDoc(self, ocpp) -> dict:
        """
        송신전문 변환
         1. 전문 템플릿 변환
         2. TC내 지정 전문 변환
         3. MessageID처리
        :param ocpp:
        :return:
        """
        doc = json.loads(self.ocppdocs)[ocpp[0]]
        """전문 템플릿 변환"""
        doc[3] = self.convertDocs(doc[3])
        """TC내 지정 전문 변환"""
        ocpp[1] = self.convertDocs(ocpp[1])
        import uuid
        for c in ocpp[1].keys():
            doc[3][c] = ocpp[1][c]
        """messageId 처리"""
        if doc[1] in self.arr_messageid.keys() :
            doc[1] = self.arr_messageid[doc[1]]
        else :
            doc[1] = f'{str(uuid.uuid4())}'

        return doc

    async def sendDocs(self, doc):

        await self.ws.send(json.dumps(doc))

        self.log(f' >> {doc[2]}:{doc}', attr='blue')
        recv = await self.ws.recv()
        self.log(f' << {doc[2]}:{recv}', attr='blue')
        recv = json.loads(recv)
        # 후처리
        if doc[2]=="StartTransaction" and recv[0] == 3 and "transactionId" in recv[2]:
            self._transactionId = recv[2]["transactionId"]
            self.confV["$transactionId"] = recv[2]["transactionId"]
            self.en_tr.delete(0,END)
            self.en_tr.insert(0,recv[2]["transactionId"])
        return recv


    async def callbackRequest(self, doc):
        rest_url = self.config.rest_url
        import requests, uuid
        if "transactionId" in doc[3] :
            doc[3]["transactionId"] = self._transactionId
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

                    schema_check = checkSchema(f"{c[0]}", doc[3], self.testschem.get())
                    if not schema_check[0] :
                        result = f" Fail ( Invalid testcase sending message from server. {schema_check[1]} )"
                        scases.append(case)
                        self.change_list(case, f"{case} (Fail)", attr={'fg':'red'}, log=result)
                        break
                    recv = await self.sendDocs(doc)
                    schema_check = checkSchema(f"{c[0]}Response", recv[2], self.testschem.get())
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
