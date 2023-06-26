import asyncio
import tkinter
import json, pyperclip, uuid, logging
import tkinter as tk
from Charger import Charger, TextHandler, Config
import ChargerStandalone
from async_tkinter_loop import async_handler, async_mainloop
from tkinter import *
from tkinter import ttk, messagebox
import tkinter.filedialog as filedialog
from datetime import datetime, timedelta
from ChargerUtil import tc_render

TAGGING = 0
COUPLER = 1
STARTTR = 2
STOPTR = 3

class ChargerSim(tk.Tk):

    def __init__(self, async_loop):
        self.async_loop = async_loop
        self.TC = None
        self.TC_original = None
        self.TC_selected = {}
        self.TC_result = []
        self.org_ocppdocs = None
        self.ocppdocs = None
        self.ConfV = {}
        self.config = None
        self.charger = None
        self.chargerlist = {}
        self.conf = json.loads(open("./config.json", encoding="utf-8").read())
        self.status = None
        self.initUI()
        self.startApp()
        self.cur_charger



    def config_update(self):
        self.interval1 = ((datetime.now() + timedelta(
            seconds=int(self.en_timestamp2.get()))).isoformat(sep='T',
                                                         timespec='seconds') + 'Z') if self.en_timestamp2.get() else 0
        self.interval2 = ((datetime.now() + timedelta(
            seconds=int(self.en_timestamp3.get()))).isoformat(sep='T',
                                                         timespec='seconds') + 'Z') if self.en_timestamp3.get() else 0
        self.ConfV = {'$idTag1': self.en_idtag1.get(), '$idTag2': self.en_idtag2.get(), '$idTag3': self.en_idtag3.get(),'$idTag': self.en_idtag1.get(),
                      '$ctime': datetime.now().isoformat(sep='T', timespec='seconds')+'Z', '$ctime+$interval1': self.interval1,
                      '$ctime+$interval2': self.interval2, '$crgr_mdl':self.en_mdl.get(), '$crgr_sno':self.en_sno.get(),
                      '$crgr_rsno':self.en_rsno.get(), '$uuid':str(uuid.uuid4()), '$transactionId':self.en_tr.get(), '$reservationId':self.en_reserve.get(),
                      '$connector':self.en_connector.get(), '$meter':self.en_meter.get(), '$vendor':self.en_vendor.get(), '$soc':self.en_soc.get()}

        self.config = Config(wss_url=self.en_url.get(),
                        rest_url=self.en_rest_url.get(),
                        auth_token=self.en_token.get(),
                        en_status=self.en_status,
                        en_tr=self.en_tr,
                        en_tc=self.en_tc,
                        lst_cases=self.lst_cases,
                        txt_recv=self.txt_recv,
                        cid=self.en_cid.get(),
                        rcid = self.en_rcid.get(),
                        sno = self.en_sno.get(),
                        rsno = self.en_rsno.get(),
                        mdl = self.en_mdl.get(),
                        result=self.TC_result,
                        confV=self.ConfV,
                        en_reserve = self.en_reserve.get(),
                        lst_tc = self.lst_tc,
                        test_mode = self.vmode.get(),
                        ocppdocs = self.ocppdocs,
                        txt_tc = self.txt_tc,
                        progressbar = self.progressbar,
                        curProgress=self.curProgress,
                        bt_direct_send=self.bt_direct_send,
                        lb_mode_alert=self.lb_mode_alert,
                        testschem=self.testschem.get(),
                        ciphersuite=self.lst_ciphersuite,
                        en_meter = self.en_meter,
                        en_vendor = self.en_vendor,
                        en_soc = self.en_soc,
                        charger_name = None,
                        charger_status = None,
                        charger_meter = None,
                        charger_soc = None,
                        charger_server = None
                        )

    def tcload_callback(self):
        try :
            self.en_log.delete(0, END)
            self.TC = json.loads(open(filedialog.askopenfilename(initialdir=".",
                                     title="Select TC cases (json)",
                                     filetypes=(("Json files", "*.json"),
                                                ("txt files", "*.txt"))),encoding="UTF-8").read())
            self.init_result()
        except Exception as err:
            self.en_log.insert(0, f"Please Check your TC json file.{err.with_traceback()}")
            return

        self.lst_cases.delete(0,END)
        for item in self.TC.keys():
            self.lst_cases.insert(END, item )

    def checkocpp(self, event):
        import jsonschema
        key = None
        if self.vtxt_tc_changed.get() == 0 :
            return
        try:
            doc = event.widget.get("1.0", END)
            doc = json.loads(doc)
            key = list(doc.keys())[0]
            with open(f"./{self.testschem.get()}/schemas/" + key + ".json") as fd:
                schema = fd.read().encode('utf-8')
            if str(key).endswith("Response") :
                target =doc[key][2]
            else:
                target =doc[key][3]
            jsonschema.validate(instance=target, schema=json.loads(schema))
            self.org_ocppdocs[key] = doc[key]
            #bt_savetc.config(state='normal')
            self.bt_savetc['state'] = tk.NORMAL
            self.lb_save_notice['text'] = "전문 템플릿이 변경되었습니다. \n유지 하시려면 변경TC를 저장하십시오"
            self.vtxt_tc_changed.set(0)
        except jsonschema.exceptions.ValidationError as e:
            messagebox.showerror(title="알림", message=f"변경된 내용이 {key} 전문 형식에 맞지 않습니다. {e.message}")
        except json.decoder.JSONDecodeError as e:
            messagebox.showerror(title="알림", message="변경 내용이 Json Format에 맞지 않습니다.")
            return False

    def saveocpp(self):
        try :
            with open(f"./{self.testschem.get()}/ocpp.json","w") as fd:
                fd.write(json.dumps(self.org_ocppdocs, indent=2))
            tkinter.messagebox.showinfo(title="성공", message="ocpp template이 저장 되었습니다.")
            self.bt_savetc['state'] = tk.DISABLED
            self.lb_save_notice['text'] = ""
            with open(f"./{self.testschem.get()}/ocpp.json", encoding='utf-8') as fd:
                self.ocppdocs = json.loads(fd.read())
        except Exception as e:
            tkinter.messagebox.showerror(title="오류", message="ocpp template 저장 중 오류 발생")

    async def startEvent(self):
        self.bt_conn['state'] = tk.NORMAL
        self.config_update()
        # TC_update()
        self.en_log.delete(0, END)
        self.en_status.delete(0, END)
        self.en_status.insert(0, "Running")
        if not self.TC_selected  :
            for tc in self.TC_original.keys():
                for t in self.TC_original[tc]:
                    self.lst_tc.insert(END, t)
        self.charger = Charger(self.config)
        await self.charger.runcase(self.TC_selected if len(self.TC_selected.keys())>0 else self.TC)
        self.en_status.delete(0, END)
        self.en_status.insert(0, "Test Finished")
        self.bt_conn['state'] = tk.DISABLED
        self.txt_tc.delete("0.0", END)
        self.curProgress.set(0)
        self.progressbar.update()

    async def standalone(self, idx):
        self.enable_control_button(idx)
        charger = None
        self.logtabs.select(idx)
        if idx in self.chargerlist :
            if messagebox.askyesno(title="충전기동작중", message="연결을 끊고 재시작(Boot)하시겠습니까?"):
                await self.chargerlist[idx].close()
                #await self.chargerlist[idx].charger_init()
            else:
                return
        if self.bt_standalone['state'] == tk.NORMAL :
            self.bt_conn['state'] = tk.NORMAL
            charger_confs = self.conf["properties"]["protocol"]
            chargerlist = list(charger_confs.keys())
            self.testschem.set(chargerlist[idx])

            self.config_update()
            self.en_log.delete(0, END)
            self.en_status.delete(0, END)
            self.en_status.insert(0, "Running")

            if not self.TC_selected  :
                for tc in self.TC_original.keys():
                    for t in self.TC_original[tc]:
                        self.lst_tc.insert(END, t)

            charger_conf_details = None
            for charger in charger_confs.keys():
                if self.chargers[idx]['text'] in charger :
                    charger_conf_details = charger_confs[charger]
            config = Config(
                wss_url=self.en_url.get(),
                rest_url=self.en_rest_url.get(),
                auth_token = charger_conf_details["auth_token"],
                en_tr = self.en_tr,
                en_tc = self.en_tc,
                lst_cases =self.lst_cases,
                en_status = self.en_status,
                txt_recv = self.chargerlogs[idx],
                cid = charger_conf_details["crgr_cid"],
                rcid = charger_conf_details["crgr_rcid"],
                sno = charger_conf_details["crgr_sno"],
                rsno = charger_conf_details["crgr_rsno"],
                mdl = charger_conf_details["crgr_mdl"],
                result = self.TC_result,
                confV = self.ConfV,
                en_reserve = self.en_reserve.get(),
                lst_tc = self.lst_tc,
                test_mode = self.vmode.get(),
                ocppdocs = self.ocppdocs,
                txt_tc = self.txt_tc,
                progressbar = self.progressbar,
                curProgress = self.curProgress,
                bt_direct_send = self.bt_direct_send,
                lb_mode_alert = self.lb_mode_alert,
                testschem = self.testschem.get(),
                ciphersuite = self.lst_ciphersuite,
                en_meter = self.en_meter,
                en_soc = self.en_soc,
                en_vendor = self.en_vendor,
                charger_name = self.chargers[idx]['text'],
                charger_status = self.chargerstatuses[idx],
                charger_meter = self.charger_meter[idx],
                charger_soc = self.charger_soc[idx],
                charger_server = charger_conf_details["server"]
            )
            charger = ChargerStandalone.Charger(config)
            self.cur_charger = idx
            self.chargerlist[idx] = charger

            await charger.standalone(self.TC_selected if len(self.TC_selected.keys())>0 else self.TC)

        else:
            charger.close()

    def change_bt_color(self, idx, type=TAGGING):
        bdic = {
            TAGGING: self.lst_bttag[idx],
            COUPLER: self.lst_btcoupler[idx],
            STARTTR: self.lst_btstarttr[idx],
            STOPTR: self.lst_btstoptr[idx]
        }
        for i in range(4):
            if i == type:
                bdic[i].configure(style="Fixed.TButton")
            else:
                bdic[i].configure(style="TButton")

    async def tagCharger(self, idx, type=TAGGING):
        self.change_bt_color(idx, type=type)
        await self.chargerlist[idx].cardtag()

    async def conn_coupler(self, idx, type=COUPLER):
        self.change_bt_color(idx, type=type)
        await self.chargerlist[idx].conn_coupler()

    async def starttr(self, idx, type=STARTTR):
        self.change_bt_color(idx, type=type)
        await self.chargerlist[idx].starttr()

    async def stoptr(self, idx, type=STOPTR):
        self.change_bt_color(idx, type=type)
        await self.chargerlist[idx].stoptr()

    def enable_control_button(self, idx):
        for i in range(4):
            self.lst_bttag[idx]['state'] = "enabled"
            self.lst_btcoupler[idx]['state'] = "enabled"
            self.lst_btstarttr[idx]['state'] = "enabled"
            self.lst_btstoptr[idx]['state'] = "enabled"

    def directClientSend(self):
        import copy
        self.bt_conn['state'] = tk.NORMAL
        self.config_update()
        # TC_update()
        self.en_log.delete(0, END)
        self.en_status.delete(0, END)
        self.en_status.insert(0, "Running")
        item = self.lst_tc.curselection()[0]
        """ 템플릿 전문 [2, 3213123, ... """
        ocpp = copy.deepcopy(json.loads(self.org_ocppdocs)[self.lst_tc.get(item)[1]])
        """ {} 내부 """

        lst_body = {}
        if len(self.lst_tc.get(item)) > 2:
            lst_body = json.loads((self.lst_tc.get(item)[2]).replace("\'", "\""))

        """TC내 지정 전문 변환"""
        for c in lst_body.keys():
            ocpp[3][c] = lst_body[c]

        """변수값 치환 변환"""
        for k in self.ConfV.keys():
            tc_render(ocpp[3], k, self.ConfV[k])

        self.sendToClient(ocpp)
        self.en_status.delete(0, END)
        self.en_status.insert(0, "전문 Client 전송 완료")
        self.bt_conn['state'] = tk.DISABLED

    async def closeEvent(self):
        for item in self.chargerlist.items():
            item[1].save_req_message_history()
        self.window.destroy()

    async def stopCharger(self):
        self.lb_mode_alert['text'] =""
        await self.charger.close()
    def show_txt_tc(self):
        self.frame_txt_tc_rendered.grid_remove()
        self.frame_txt_tc.grid(row=8, column=3, rowspan=3, sticky="we")

    def show_txt_tc_rendered(self):
        self.frame_txt_tc.grid_remove()
        self.frame_txt_tc_rendered.grid(row=8, column=3, rowspan=3, sticky="we")


    def wssRenew(self):
        self.lb_url_comp.config(text=self.en_url.get()+'/'+self.testschem.get().split('/')[0]+'/'+self.en_mdl.get()+'/'+self.en_sno.get())

    def onSelect(self, event):
        w = event.widget
        self.TC_selected ={}
        for s in w.curselection():
            self.TC_selected[w.get(s).split()[0]] = self.TC[w.get(s).split()[0]]
            self.en_tc.config(state='normal')
            self.en_tc.delete(0,END)
            self.en_tc.insert(0,w.get(s).split())
            self.en_tc.config(state='disabled')
        if w.curselection() :
            index = int(w.curselection()[0])
            self.en_log.delete(0,END)
            self.en_log.insert(END, self.TC_result[index])
            self.lst_tc.delete(0,END)
            for c in self.TC_selected :
                for tc in self.TC_original[c]:
                    self.lst_tc.insert(END, tc)

    def onSelectTcItem(self, event):
        import copy
        w = event.widget
        items= [ w.get(s) for s in w.curselection() ]
        if not items :
            return
        text_item = {}

        for item in items :
            if item[0]  in ('Wait', 'Reply') :
                text_item[item[1]]=json.loads(self.org_ocppdocs)[item[1]]
                self.bt_direct_send['state'] = tk.NORMAL
            else :
                text_item[item[0]]=json.loads(self.org_ocppdocs)[item[0]]
                self.bt_direct_send['state'] = tk.DISABLED

        self.txt_tc.delete(1.0, END)
        self.txt_tc.insert(END, json.dumps(text_item, indent=2))

        doc = copy.deepcopy(text_item)
        for k in self.ConfV.keys():
            tc_render(doc, k, self.ConfV[k])

        doc[list(doc.keys())[0]][1]=str(uuid.uuid4())
        self.txt_tc_rendered.delete(1.0, END)
        self.txt_tc_rendered.insert(END, json.dumps(doc, indent=2))

        schemas = {}
        for msgid in text_item.keys():
            with open(f"./{self.testschem.get()}/schemas/{msgid}{'Request' if '20' in self.testschem.get() else ''}.json", encoding='utf-8') as fd:
                schemas['Request'] = json.loads(fd.read())
            with open(f"./{self.testschem.get()}/schemas/{msgid}Response.json", encoding='utf-8') as fd:
                schemas['Response'] = json.loads(fd.read())
        # schemas = schemas
        self.txt_schema.delete(1.0, END)
        self.txt_schema.insert(END, json.dumps(schemas, indent=2))


    def load_default_tc(self):
        import copy
        try :
            self.en_log.delete(0, END)
            with open(f"./{self.testschem.get()}/props.json", encoding='utf-8') as fd:
                self.TC = json.loads(fd.read())
            self.TC_original = copy.deepcopy(self.TC)

            self.init_result()
            with open(f"./{self.testschem.get()}/ocpp.json", encoding='utf-8') as fd:
                self.ocppdocs = fd.read()
                # for k in self.ConfV.keys():
                #     self.ocppdocs.replace(k, self.ConfV[k])
                # self.ocppdocs = json.loads(self.ocppdocs)
                self.org_ocppdocs = copy.deepcopy(self.ocppdocs)

        except Exception as err:
            self.en_log.insert(0, "Please Check your TC json file.")
            return
        self.lst_cases.delete(0,END)
        for item in self.TC.keys():
            self.lst_cases.insert(END, item )

        self.init_result()

    def ctrlc(self, event: tk.Event = None) -> str:
        try:
            text = event.widget.selection_get()
            pyperclip.copy(text)
        except tk.TclError:
            pass
        return "break"

    # def onEnter(event):
    #     index = event.widget.index("%s, %s" %(event.x, event.y))

    """props.json 파일(기본TC파일) 로드"""
    def reload_tc(self, event) :
        self.load_default_tc()

    def lst_cases_double_click(self,event):
        """
        TC CASE 더블클릭해서 선택 하면 txt_recv log영역내용에서 해당 tc를 찾아 .see 해줌
        :param event:
        :return:
        """
        w = event.widget
        idx = w.curselection()[0]
        line = self.txt_recv.search(self.lst_cases.get(idx).split()[0], "0.0", stopindex=END)
        if line :
            self.txt_recv.see(line)

    async def on_closing(self):
        """
        종료시 편집중 체크
        :return:
        """
        if self.bt_savetc['state'] == tk.NORMAL :
            if messagebox.askokcancel("종료", "편집 중인 전문이 있습니다. 종료 하시겠습니까?"):
                await self.closeEvent()
            else:
                return
        await self.closeEvent()


    def set_time_label(self):
        from datetime import datetime
        currentTime = datetime.now().isoformat(sep='T', timespec='seconds')+'Z'
        self.en_timestamp1.delete(0, END)
        self.en_timestamp1.insert(0, currentTime)
        self.tab2.after(1, self.set_time_label)

    def sendToClient(self, doc):
        rest_url = self.config.rest_url
        import requests, uuid
        if "transactionId" in doc[3]:
            doc[3]["transactionId"] = int(self.en_tr.get())
        doc[1] = f'{str(uuid.uuid4())}'
        reqdoc = {
            "crgrMid":self.config.rcid[:11] if "Reserv" in doc[2] else self.config.cid[:11],
            "data": doc
        }
        header = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }
        self.txt_recv.insert(END, f" << Direct Msg {reqdoc} ...")
        response = requests.post(rest_url, headers=header, data=json.dumps(reqdoc), verify=False, timeout=5).json()
    def testschemChanged(self, *args):
        """
        테스트 프로토콜 변경시 TC 재 로드
        :param args:
        :return:
        """
        self.load_default_tc()
        try :
            with open("./config.json", encoding="utf-8") as fd:
                attr = json.loads(fd.read())
                attr_urls = attr["urls"]
                attr_protocol = attr["properties"]["protocol"][self.testschem.get()]

                for k in attr_protocol.keys() :
                    self.properties[k].delete(0,END)
                    self.properties[k].insert(0,attr_protocol[k])

                for k in attr_urls.keys() :
                    self.urls[k].delete(0,END)
                    self.urls[k].insert(0,attr_urls[k])
                    if k=="wss":
                        self.urls[k].insert(END,'/'+self.testschem.get().split('/')[0])
                self.wssRenew()
        except Exception as e:
            print(e.with_traceback())
            messagebox.showerror(title="구성파일", message="구성파일(config.json) 오류, 파일 존재 및 내용을 확인 하세요")
            self.window.destroy()

    def txt_tc_changed(self, event):
        self.vtxt_tc_changed.set(1)

    def init_result(self):
        self.TC_result = ['Not Tested' for _ in range(len(self.TC.keys()))]

    def charger_status_switch(self, idx):
        self.standalone(idx)
        self.logtabs.select(idx)  # 버튼 순서에 해당하는 하위 탭으로 포커스 이동

    def initUI(self):
        import tkinter.ttk
        from tkinter import Label, Entry, Button, scrolledtext, Listbox

        self.window = tkinter.Tk()
        self.tabs = ttk.Notebook(self.window, width=20)
        s = ttk.Style()
        s.theme_use('default')
        s.configure('Tab', width=20)
        self.tabs.pack(fill=BOTH, expand=TRUE)
        self.tab1 = tkinter.ttk.Frame(self.tabs)
        self.tab2 = tkinter.ttk.Frame(self.tabs)
        self.tab3 = tkinter.ttk.Frame(self.tabs)
        self.tabs.add(self.tab1, text="TC Run")
        self.tabs.add(self.tab2, text="TC Configure")
        self.tabs.add(self.tab3, text="Charger Simulation")

        self.status = 1
        self.vtxt_tc_changed = IntVar()
        self.window.title("EV Charger Simulator (nheo.an@gmail.com)")
        self.window.geometry("1160x990+500+100")
        self.window.resizable(True, True)
        self.frameHat = LabelFrame(self.tab1, text="Configuration", padx=5, pady=5)
        self.frameTop = LabelFrame(self.tab1, text="Configuration", padx=5, pady=5)
        self.frameBot = LabelFrame(self.tab1, text="Log Output", padx=5, pady=5)
        self.frameConfTop = LabelFrame(self.tab2, text="Basic Configuration", padx=5, pady=5)
        self.frameConfBot = LabelFrame(self.tab2, text="Custom Configuration", padx=5, pady=5)


        #self.subtabs = ttk.Notebook(self.tab3)
        self.frameBtChargers = LabelFrame(self.tab3, text="Chargers", padx=5, pady=5)
        self.frameChargerLogs = Frame(self.tab3, padx=5, pady=5)
        self.frameBtChargers.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        self.frameChargerLogs.pack(side="bottom", fill="both", expand=True, padx=5, pady=5)



        self.lst_cases = Listbox(self.frameTop, height=7, selectmode="extended", activestyle="none", exportselection=False)
        self.rdo_frame = Frame(self.frameTop)
        self.bt_frame = Frame(self.frameTop)
        self.bt_rframe = Frame(self.frameTop)


        self.frameHat.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        self.frameTop.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        self.frameBot.pack(side="bottom", fill="both", expand=True, padx=5, pady=5)
        self.frameConfTop.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        self.frameConfBot.pack(side="bottom", fill="both", expand=True, padx=5, pady=5)
        self.menubar = Menu(self.window)
        self.menu1 = Menu(self.menubar, tearoff=0)
        self.menu2 = Menu(self.menubar, tearoff=0)

        self.window.config(menu=self.menubar)
        self.frame_txt_tc = Frame(self.frameTop, width=60, height=15)
        self.frame_txt_tc_rendered = Frame(self.frameTop, width=60, height=15)

        self.txt_tc = scrolledtext.ScrolledText(self.frame_txt_tc, width=70, height=15)
        self.txt_tc_rendered = scrolledtext.ScrolledText(self.frame_txt_tc_rendered, width=70, height=15)
        self.txt_schema = scrolledtext.ScrolledText(self.frameTop, width=50, height=15)
        self.lb_schema = Label(self.frameTop, text="OCPP Schema", width=10)
        self.lst_tc = Listbox(self.frameTop, height=7, selectmode="extended", activestyle="none", width=70)
        self.lb_txt_tc = Label(self.frameTop, text="OCPP Template", width=10)

        self.txt_log = scrolledtext.ScrolledText(self.frameBot, width=143, height=6)
        self.txt_recv = scrolledtext.ScrolledText(self.frameBot, width=143, height=15)
        self.lb_log = Label(self.frameTop, text="로그", width=10)

        self.lb_url = Label(self.frameTop, text="WSS URL", width=10)
        self.lb_rest_url = Label(self.frameTop, text="REST URL", width=10)
        self.lb_cases = Label(self.frameTop, text="Test Case", width=10)
        self.curProgress = tkinter.DoubleVar()
        self.style = tkinter.ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("1.Horizontal.TProgressbar", troughcolor='gray', background='green')
        self.progressbar = tkinter.ttk.Progressbar(self.frameTop, style="1.Horizontal.TProgressbar", maximum=100, variable = self.curProgress)
        self.lb_progress = Label(self.frameTop, text="진행률")


        self.en_url = Entry(self.frameTop, width=60)
        self.en_rest_url = Entry(self.frameTop, width=60)


        self.lb_case = Label(self.frameTop, text="TC Body")
        self.lb_protocol = Label(self.frameHat, text="프로토콜")
        self.lb_sno = Label(self.frameHat, text="충전기ID(일반)")
        self.lb_server = Label(self.frameHat, text="서버")
        self.lb_rsno = Label(self.frameHat, text="충전기ID(예약)")
        self.lb_mdl = Label(self.frameHat, text="모델ID")
        self.lb_cid = Label(self.frameHat, text="충전기CID(일반)", width=13)
        self.lb_rcid = Label(self.frameHat, text="충전기CID(예약)", width=13)
        self.options= [
        ]
        self.testschem = StringVar(self.frameHat)
        self.testschem.set("ocpp16/websocket/standard")
        try :
            with open("./config.json", encoding="utf-8") as fd:
                self.options = json.loads(fd.read())["testschem"]
        except Exception as e:
            messagebox.showerror(title="구성파일", message="구성파일(config.json) 오류, 파일 존재 및 내용을 확인 하세요")
            self.window.destroy()

        self.chargers = []
        self.chargerlogtabs = []
        self.chargerloglabelframe = []
        self.chargerlogs = []
        self.chargerstatuses = []
        self.charger_meter = []
        self.charger_soc = []
        self.lst_bttag = []
        self.lst_btcoupler = []
        self.lst_btstarttr = []
        self.lst_btstoptr = []

        protocols = self.conf["properties"]["protocol"]
        protocol_keys = list(self.conf["properties"]["protocol"].keys())

        style = ttk.Style()
        style.configure("NLabel.TLable", foreground="black", background="white", font=("TkDefaultFont", 12), padding=10)
        style.configure("BLabel.TLabel", foreground="blue")
        style.configure("GLabel.TLabel", foreground="green")
        style.configure("TButton", background="SystemButtonFace")
        style.configure("Blue.TButton", forground="blue")
        style.map('Fixed.TButton',
                  background=[('active', '#ff9900'),
                              ('pressed', '#ff9900'),
                              ('!active', '#ff9900')])

        for idx, c in enumerate(protocol_keys):
            btname = c.split('/')[-1]
            btCharger = ttk.Button(self.frameBtChargers, text=btname, width=12, command=async_handler(self.standalone, idx), style='Blue.TButton')
            btCharger.grid(row=0, column=idx, sticky="we")

            self.chargers.append(btCharger)

        for idx, c in enumerate(protocol_keys):
            chrstn_nm = ttk.Label(self.frameBtChargers, text=f'{protocols[protocol_keys[idx]]["chrstn_nm"]}', width=12, anchor="center", style='NLabel.TLabel')
            chrstn_nm.grid(row=1, column=idx, sticky="we")
            #self.chargerstatuses.append(cid)

        for idx, c in enumerate(protocol_keys):
            mdl = ttk.Label(self.frameBtChargers, text=f'{protocols[protocol_keys[idx]]["server"]}', width=12, anchor="center", style='NLabel.TLabel')
            mdl.grid(row=2, column=idx, sticky="we")
            #self.chargerstatuses.append(mdl)

        for idx, c in enumerate(protocol_keys):
            mdl = ttk.Label(self.frameBtChargers, text=f'{protocols[protocol_keys[idx]]["crgr_mdl"]}', width=12, anchor="center", style='NLabel.TLabel')
            mdl.grid(row=3, column=idx, sticky="we")
            #self.chargerstatuses.append(mdl)

        for idx, c in enumerate(protocol_keys):
            mdl = ttk.Label(self.frameBtChargers, text=f'{protocols[protocol_keys[idx]]["crgr_sno"]}', width=12, anchor="center", style='NLabel.TLabel')
            mdl.grid(row=4, column=idx, sticky="we")
            #self.chargerstatuses.append(mdl)

        for idx, c in enumerate(protocol_keys):
            cid = ttk.Label(self.frameBtChargers, text=f'{protocols[protocol_keys[idx]]["crgr_cid"]}', width=12, anchor="center", style='NLabel.TLabel')
            cid.grid(row=5, column=idx, sticky="we")


        for idx, c in enumerate(protocol_keys):
            stCharger = ttk.Label(self.frameBtChargers, text='Offline', width=12, anchor="center", style='BLabel.TLabel')
            stCharger.grid(row=6, column=idx, sticky="we")
            self.chargerstatuses.append(stCharger)

        for idx, c in enumerate(protocol_keys):
            wh = ttk.Label(self.frameBtChargers, text=f"{0} Wh", width=12, anchor="center", style='GLabel.TLabel')
            wh.grid(row=7, column=idx, sticky="we")
            self.charger_meter.append(wh)

        for idx, c in enumerate(protocol_keys):
            soc = ttk.Label(self.frameBtChargers, text=f"{0} %", width=12, anchor="center", style='GLabel.TLabel')
            soc.grid(row=8, column=idx, sticky="we")
            self.charger_soc.append(soc)

        for idx, c in enumerate(protocol_keys):
            btname = '카드 태깅'
            bttag = ttk.Button(self.frameBtChargers, text=btname, width=12, command=async_handler(self.tagCharger, idx),  state="disabled")
            bttag.grid(row=9, column=idx, sticky="we")
            self.lst_bttag.append(bttag)


        for idx, c in enumerate(protocol_keys):
            btcouplernm = '커플러 연결'
            btcoupler = ttk.Button(self.frameBtChargers, text=btcouplernm, width=12, command=async_handler(self.conn_coupler, idx),  state="disabled")
            btcoupler.grid(row=10, column=idx, sticky="we")
            self.lst_btcoupler.append(btcoupler)


        for idx, c in enumerate(protocol_keys):
            btstarttrnm = '충전시작'
            btstarttr = ttk.Button(self.frameBtChargers, text=btstarttrnm, width=12, command=async_handler(self.starttr, idx),  state="disabled")
            btstarttr.grid(row=11, column=idx, sticky="we")
            self.lst_btstarttr.append(btstarttr)


        for idx, c in enumerate(protocol_keys):
            btchgendnm= '충전종료'
            btchgend = ttk.Button(self.frameBtChargers, text=btchgendnm, width=12, command=async_handler(self.stoptr, idx),  state="disabled")
            btchgend.grid(row=12, column=idx, sticky="we")
            self.lst_btstoptr.append(btchgend)


        self.logtabs = ttk.Notebook(self.frameChargerLogs)
        self.logtabs.pack(fill=BOTH, expand=TRUE)
        style.configure("TNotebook.Tab", width=10)
        for idx, c in enumerate(self.options):
            btname = c.split('/')[-1]
            logtab = tkinter.ttk.Frame(self.logtabs, style='TNotebook.Tab')

            self.chargerlogtabs.append(logtab)
            loglabelframe = LabelFrame(logtab, text=btname, padx=5, pady=5)
            loglabelframe.grid(row=0, column=0, sticky="nsew")
            self.chargerloglabelframe.append(loglabelframe)
            self.logtabs.add(logtab, text=btname)
            chargerlogtxt = scrolledtext.ScrolledText(loglabelframe, width=157, height=40)
            chargerlogtxt.grid(row=0, column=0, sticky="nsew")
            self.chargerlogs.append(chargerlogtxt)

        self.en_protocol = OptionMenu(self.frameHat, self.testschem, *self.options)
        self.en_protocol.configure(width=20)
        self.testschem.trace("w", self.testschemChanged)
        self.en_server = Entry(self.frameHat)
        self.en_sno = Entry(self.frameHat)
        self.en_rsno = Entry(self.frameHat)
        self.en_sno.insert(0, "EVSCA050001")
        self.en_cid = Entry(self.frameHat)
        self.en_rcid = Entry(self.frameHat)
        self.en_mdl = Entry(self.frameHat)
        self.lb_token = Label(self.frameHat, text="Auth Token")
        self.lb_tr = Label(self.frameHat, text="transactionId", width=10)
        self.en_tr = Entry(self.frameHat)
        self.en_token = Entry(self.frameHat)
        self.lb_reserve = Label(self.frameHat, text="reserveId", width=5)
        self.en_reserve = Entry(self.frameHat)
        self.lb_connector = Label(self.frameHat, text="connector", width=5)
        self.en_connector = Entry(self.frameHat)
        self.lb_meter = Label(self.frameHat, text="meter", width=5)
        self.en_meter = Entry(self.frameHat)
        self.en_meter.insert(0, "0")
        self.lb_chrstn_nm = Label(self.frameHat, text="meter", width=5)
        self.en_chrstn_nm = Entry(self.frameHat)
        self.lb_soc = Label(self.frameHat, text="SoC", width=5)
        self.en_soc = Entry(self.frameHat)
        self.lb_vendor = Label(self.frameHat, text="vendor", width=5)
        self.en_vendor = Entry(self.frameHat)
        self.lb_status = Label(self.frameHat, text="Status", width=5)
        self.en_status = Entry(self.frameHat)
        self.lb_url_comp = Label(self.frameTop, text=self.en_url.get()+"/"+self.en_mdl.get()+"/"+self.en_sno.get())
        self.lb_tc = Label(self.frameTop, text="Current TC", width=13)
        self.en_tc = Entry(self.frameTop)
        self.en_log = Entry(self.frameTop, fg='red')
        self.tc_result_rdo_frame = Frame(self.frameTop)
        self.vtc_mode = IntVar()
        self.lb_tc_mode = Label(self.frameTop, text="TC결과상세")
        self.vtc_mode1 = Radiobutton(self.tc_result_rdo_frame, text="Doc Template", variable=self.vtc_mode, value=1)

        self.vtc_mode2 = Radiobutton(self.tc_result_rdo_frame, text="Doc Rendered", variable=self.vtc_mode, value=2)
        self.lb_txt = Label(self.frameBot, text="실행로그", width=10)
        self.lb_recv = Label(self.frameBot, text="송수신로그", width=10)
        self.s=tk.ttk.Separator(self.frameBot, orient="horizontal")
        """Configuration Tab"""
        """========================================================="""

        self.lb_idtag1 = Label(self.frameConfTop, text="idTag1", width=20)
        self.en_idtag1 = Entry(self.frameConfTop)
        self.lb_idtag2 = Label(self.frameConfTop, text="idTag2", width=20)
        self.en_idtag2 = Entry(self.frameConfTop)
        self.lb_idtag3 = Label(self.frameConfTop, text="idTag3", width=20)
        self.en_idtag3 = Entry(self.frameConfTop)
        self.lb_ciphersuite = Label(self.frameConfTop, text="CipherSuite\nBase Local OpenSSL", width=20)
        self.lst_ciphersuite = Listbox(self.frameConfTop, height=10, selectmode="extended", activestyle="none",
                                 exportselection=False, width=50)
        try :
            import ssl
            context = ssl.create_default_context()
            for c in [f"{cipher['protocol']},{cipher['name']}" for cipher in context.get_ciphers()] :
                self.lst_ciphersuite.insert(END, c)
            self.lst_ciphersuite.select_set(0, tk.END)
        except Exception as e:
            messagebox.showerror(title="구성파일", message="구성파일(config.json) 오류, 파일 존재 및 내용을 확인 하세요")
            self.window.destroy()

        self.lb_timestamp1 = Label(self.frameConfTop, text="$ctime", width=25)
        self.en_timestamp1 = Entry(self.frameConfTop)
        self.lb_timestamp2 = Label(self.frameConfTop, text="($ctime+$interval1) - seconds", width=25)
        self.en_timestamp2 = Entry(self.frameConfTop)
        self.lb_timestamp3 = Label(self.frameConfTop, text="($ctime+$interval2) - seconds", width=25)
        self.en_timestamp3 = Entry(self.frameConfTop)

        self.vmode = IntVar()
        self.lb_mode = Label(self.rdo_frame, text="원격제어방법")
        self.lb_mode_alert = Label(self.rdo_frame, text="", fg='red')
        self.test_mode1 = Radiobutton(self.rdo_frame, text="Local호출", variable=self.vmode, value=1)
        self.test_mode2 = Radiobutton(self.rdo_frame, text="CSMS", variable=self.vmode, value=2)
        self.vmode.set(1)
        self.bt_conn = Button(self.bt_frame, text="시험 중지", command=async_handler(self.stopCharger), state=DISABLED, width=15)
        self.bt_start = Button(self.bt_frame, text="TC 실행", command=async_handler(self.startEvent), width=15)
        self.bt_reload = Button(self.bt_frame, text="TC Reload", width=15)
        self.bt_close = Button(self.bt_frame, text="시뮬레이터 종료", command=async_handler(self.closeEvent), width=15)
        self.bt_standalone = Button(self.bt_frame, text="충전기모드수행", command=async_handler(self.standalone, 1), width=15, background="yellow")
        self.bt_savetc = Button(self.bt_rframe, text="변경TC 저장", width=15, command=self.saveocpp)
        self.bt_direct_send = Button(self.bt_rframe, text="전문직접전송(To 충전기)", width=20, bg="lightgreen", command=self.directClientSend, state="disabled")
        self.lb_save_notice = Label(self.bt_rframe)
        self.bt_savetc.config(state='disabled')

        self.properties = {
            "server": self.en_server,
            "crgr_sno": self.en_sno,
            "crgr_rsno": self.en_rsno,
            "crgr_cid": self.en_cid,
            "crgr_rcid": self.en_rcid,
            "crgr_mdl": self.en_mdl,
            "auth_token": self.en_token,
            "idTag1": self.en_idtag1,
            "idTag2": self.en_idtag2,
            "idTag3": self.en_idtag3,
            "connector": self.en_connector,
            "interval1": self.en_timestamp2,
            "interval2": self.en_timestamp3,
            "vendor": self.en_vendor,
            "chrstn_nm":self.en_chrstn_nm
        }
        self.urls = {
            "rest": self.en_rest_url,
            "wss": self.en_url
        }
    def startApp(self):

        self.menu1.add_command(label="Load TC (Json)", command=self.tcload_callback)
        self.bt_conn.configure(command=async_handler(self.stopCharger))
        self.menu1.add_command(label="Exit")
        self.menubar.add_cascade(label="File", menu=self.menu1)
        self.menu2.add_command(label="About")
        self.menubar.add_cascade(label="About", menu=self.menu2)

        self.txt_recv.tag_config('blue', foreground='blue')
        self.txt_recv.tag_config('green', foreground='green')
        self.txt_recv.tag_config('red', foreground='red')

        # Create textLogger
        text_handler = TextHandler(self.txt_log)

        # Logging configuration
        logging.basicConfig(filename='test.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s')

        # Add the handler to logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(text_handler)
        self.status = 0

        self.en_rsno.insert(0, "EVSCA050002")
        self.en_cid.insert(0, "115001514011A")
        self.en_rcid.insert(0, "115001514021A")
        self.en_mdl.insert(0, "ELA007C05")
        self.en_token.insert(0, 'Basic RVZBUjpFVkFSTEdV')
        self.en_status.insert(0, 'Idle')
        self.lb_protocol.grid(row=0, column=0, sticky="we")
        self.en_protocol.grid(row=0, column=1, sticky="we")
        self.lb_sno.grid(row=0, column=2, sticky="we")
        self.en_sno.grid(row=0, column=3, sticky="we")
        self.lb_rsno.grid(row=0, column=4, sticky="we")
        self.en_rsno.grid(row=0, column=5, sticky="we")
        self.lb_cid.grid(row=0, column=6, sticky="we")
        self.en_cid.grid(row=0, column=7, sticky="we")
        self.lb_rcid.grid(row=0, column=8, sticky="we")
        self.en_rcid.grid(row=0, column=9)
        self.lb_mdl.grid(row=1, column=0, sticky="we")
        self.en_mdl.grid(row=1, column=1, sticky="we")
        self.lb_token.grid(row=1, column=2, sticky="we")
        self.en_token.grid(row=1, column=3, sticky="we")
        self.lb_tr.grid(row=1, column=4, sticky="we")
        self.en_tr.grid(row=1, column=5, sticky="we")
        self.lb_reserve.grid(row=1, column=6, sticky="we")
        self.en_reserve.grid(row=1, column=7, sticky="we")
        self.lb_status.grid(row=1, column=8, sticky="we")
        self.en_status.grid(row=1, column=9, sticky="we")
        self.lb_connector.grid(row=2, column=0, sticky="we")
        self.en_connector.grid(row=2, column=1, sticky="we")
        self.lb_meter.grid(row=2, column=2, sticky="we")
        self.en_meter.grid(row=2, column=3, sticky="we")
        self.lb_vendor.grid(row=2, column=4, sticky="we")
        self.en_vendor.grid(row=2, column=5, sticky="we")
        self.lb_chrstn_nm.grid(row=2, column=6, sticky="we")
        self.en_chrstn_nm.grid(row=2, column=7, sticky="we")
        self.lb_soc.grid(row=2, column=8, sticky="we")
        self.en_soc.grid(row=2, column=9, sticky="we")
        self.lb_server.grid(row=3, column=0, sticky="we")
        self.en_server.grid(row=3, column=1, sticky="we")
        self.vtc_mode1.configure(command=self.show_txt_tc)
        self.vtc_mode2.configure(command=self.show_txt_tc_rendered)
        self.lb_url.grid(row=3, column=0, sticky="we")
        self.lb_rest_url.grid(row=5, column=0, sticky="we")
        self.en_url.grid(row=3, column=1, sticky="we")
        self.lb_progress.grid(row=3, column=2, sticky="we")
        self.progressbar.grid(row=3, column=3, sticky="we")
        self.lb_url_comp.grid(row=4, column=1, sticky="w")
        self.en_rest_url.grid(row=5, column=1, sticky="we")
        self.lb_tc.grid(row=5, column=2, sticky="we")
        self.en_tc.config(state='disabled')
        self.en_tc.grid(row=5, column=3, sticky="we")
        self.lb_cases.grid(row=6, column=0, sticky="we")
        self.lst_cases.grid(row=6, column=1, sticky="we")
        self.lb_log.grid(row=7, column=0, sticky="we")
        self.en_log.grid(row=7, column=1, sticky="we")
        self.tc_result_rdo_frame.grid(row=7, column=3, columnspan=2, sticky="w")
        self.lb_tc_mode.grid(row=7, column=2)
        self.vtc_mode1.grid(row=0, column=1)
        self.vtc_mode2.grid(row=0, column=2)
        self.vtc_mode.set(1)
        self.lb_schema.grid(row=8, column=0, sticky="we")
        self.txt_schema.grid(row=8, column=1, sticky="we")
        self.lb_case.grid(row=6, column=2)
        self.frame_txt_tc.grid(row=8, column=3, rowspan=3, sticky="we")
        self.txt_tc.grid(row=0, column=0, rowspan=3, sticky="we")
        self.txt_tc_rendered.grid(row=0, column=0, rowspan=3, sticky="we")
        self.lb_txt_tc.grid(row=8, column=2, sticky="we")
        self.lst_tc.grid(row=6, column=3, sticky="we")

        self.lb_txt.grid(row=0, column=0)
        self.txt_log.grid(row=0, column=1, columnspan=3)
        self.s.grid(row=1, column=1, sticky='ew', columnspan=3)
        self.lb_recv.grid(row=2, column=0)
        self.txt_recv.grid(row=2, column=1, columnspan=3)

        self.lb_idtag1.grid(row=0, column=0)
        self.lb_idtag2.grid(row=1, column=0)
        self.lb_idtag3.grid(row=2, column=0)
        self.en_idtag1.grid(row=0, column=1)
        self.en_idtag1.insert(0, '1031040000069641')
        self.en_idtag2.grid(row=1, column=1)
        self.en_idtag3.grid(row=2, column=1)
        self.lb_ciphersuite.grid(row=3, column=0, sticky="we")
        self.lst_ciphersuite.grid(row=3, column=1, columnspan=3, sticky="we")


        self.lb_timestamp1.grid(row=0, column=2)
        self.lb_timestamp2.grid(row=1, column=2)
        self.lb_timestamp3.grid(row=2, column=2)
        self.en_timestamp1.grid(row=0, column=3)
        self.en_timestamp2.grid(row=1, column=3)
        self.en_timestamp3.grid(row=2, column=3)
        self.rdo_frame.grid(row=12, column=0, columnspan=4, sticky="W", padx=10, pady=10)
        self.bt_frame.grid(row=13, column=0, columnspan=4, sticky="we", padx=10, pady=10)
        self.bt_rframe.grid(row=13, column=2, columnspan=4, sticky="e", padx=10, pady=10)

        self.lb_mode.grid(row=0, column=0)
        self.lb_mode_alert.grid(row=0, column=4, sticky="e")
        self.test_mode1.grid(row=0, column=1)
        self.test_mode2.grid(row=0, column=2)
        self.bt_conn.grid(row=1, column=0, ipady=3, pady=3, sticky="w")
        self.bt_start.grid(row=1, column=1, ipady=3, pady=3, sticky="w")
        self.bt_reload.grid(row=1, column=2, ipady=3, pady=3, sticky="w")
        self.bt_close.grid(row=1, column=3, ipady=3, pady=3, sticky="E")
        self.bt_standalone.grid(row=1, column=4, ipady=3, pady=3, sticky="E")
        self.bt_direct_send.grid(row=1, column=1, ipady=3, pady=3, sticky="WE")
        self.bt_savetc.grid(row=1, column=2, ipady=3, pady=3, sticky="WE")
        self.lb_save_notice.grid(row=1, column=0, sticky="e")

        self.interval1 = ((datetime.now() + timedelta(
            seconds=int(self.en_timestamp2.get()))).isoformat(sep='T', timespec='seconds') + 'Z') if self.en_timestamp2.get() else 0
        self.interval2 = ((datetime.now() + timedelta(
            seconds=int(self.en_timestamp3.get()))).isoformat(sep='T', timespec='seconds') + 'Z') if self.en_timestamp3.get() else 0

        self.en_sno.bind('<KeyRelease>', self.wssRenew)
        self.en_mdl.bind('<KeyRelease>', self.wssRenew)
        self.lst_cases.bind('<<ListboxSelect>>', self.onSelect)
        self.lst_tc.bind('<<ListboxSelect>>', self.onSelectTcItem)
        self.txt_schema.bind("<Key>", lambda e: "break")
        self.bt_reload.bind("<Button-1>", self.reload_tc)
        self.txt_tc.bind('<FocusOut>', self.checkocpp)
        self.txt_tc.bind('<Control-c>', self.ctrlc)
        self.txt_tc.bind('<KeyRelease>', self.txt_tc_changed)
        self.txt_tc_rendered.bind('<Control-c>', self.ctrlc)
        self.lst_cases.bind('<Double-Button>', self.lst_cases_double_click)
        self.window.protocol("WM_DELETE_WINDOW", async_handler(self.on_closing))
        self.set_time_label()


        """App최초 실행시 초기 값 config.json에서 불러와서 셋팅"""
        self.testschemChanged()

        self.load_default_tc()
        self.config_update()

        async_mainloop(self.window)

def main(async_loop):
    ChargerSim(async_loop)

if __name__ == "__main__":
    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)
    main(async_loop)
