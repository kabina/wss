import asyncio
import websockets
import ssl
async def save_certificate():
    uri = "wss://ws.devevspcharger.uplus.co.kr/ocpp16/ELA007C05/EVSCA050001"  # 접속할 WSS 사이트의 URI를 입력하세요
    header = {
        ""
    }
    async with websockets.connect(uri,
                                subprotocols=["ocpp1.6"],
                                extra_headers= {"Authorization": "Basic RVZBUjpFVkFSTEdV"},
                                ssl=True) as websocket:
        ssl_object = websocket.transport.get_extra_info('ssl_object')
        cert = ssl_object.getpeercert(True)
        pem_cert = ssl.DER_cert_to_PEM_cert(cert)
        # 인증서 파일로 저장
        with open("certificate_bin.der", "wb") as file:
            file.write(cert)

        with open("certificate_pem.pem", "wb") as file:
            file.write(pem_cert.encode())

        print("인증서가 저장되었습니다.")

asyncio.run(save_certificate())