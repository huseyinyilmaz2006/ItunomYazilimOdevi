import random
import time
import threading
import socket
import json
import cv2
import sys

PORT_TELEMETRI=5000
PORT_VIDEO=5001
HOST="127.0.0.1"

class IHAsimulator(object):
    def __init__(self,host,port_telemetri,port_video):
        self.host=host
        self.port_telemetri=port_telemetri
        self.port_video=port_video
        self.telemetri_verisi=self.baslangic_verileri()
        self.telemetri_socketi=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_cap = cv2.VideoCapture(0)
        self.calisma_durumu=True
    def baslangic_verileri(self):
        return {"x_konumu":0.0,
                "y_konumu":0.0,
                "irtifa_konumu":0.0,
                "hiz":3.0,
                "pil_durumu":100.0,
                "zaman":time.time()
                }
    
    def random_telemetri(self):
        self.baslangic_verileri["x_konumu"]+=random.uniform(-5,5)
        self.baslangic_verileri["y_konumu"]+=random.uniform(-5,5)
        self.baslangic_verileri["irtifa_konumu"]+=random.uniform(-3,3)
        self.baslangic_verileri["hiz"]+=random.uniform(-8,8)
        self.baslangic_verileri["pil_durumu"]-=random.uniform(0.3,0.7)
        self.baslangic_verileri["zaman"]=time.time()
        if self.baslangic_verileri["pil_durumu"]<0:
            self.baslangic_verileri["zaman"]=0
            self.calisma_durumu=False
    def telemetri_aktarici(self):
        while self.calisma_durumu:
            self.random_telemetri()
            gonderi=json.dumps(self.telemetri_verisi).encode("utf-8")
            time.sleep(1)
    def video_aktarici(self):
        baglanti=None
        server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server_socket.bind(("",self.port_video))
        server_socket.listen(1)
        baglanti, addr=server_socket.accept()
        try:
            while self.calisma_durumu:
                ret,frame=self.video_cap.read()
                if not ret:
                    break
                encode_param=[int(cv2.INWRITE_JPEG_QUALITY),90]
                result,img_encoded=cv2.imencode(".jpg",frame,encode_param)
                data=img_encoded.tobytes()
                data_size=len(data)
                baglanti.sendall(data_size.to_bytes(4,byteorder="big"))
                baglanti.sendall(data)
                time.sleep(0.033)
        except Exception as e:
            print(f"video akiş hatasi {e}")
        finally:
            baglanti.close()
            server_socket.close()
            self.calisma_durumu=False
            if self.video_cap:
                self.video_cap.release()
            print("video akisi sonlandi")
    def baslat(self):
        thread_telemetri=threading.Thread(target=self.telemetri_aktarici)
        thread_video=threading.Thread(target=self.video_aktarici)
        thread_telemetri.daemon=True
        thread_video.daemon=True
        thread_telemetri.start()
        thread_video.start()
        print("İHA simulatoru başlatildi")
        try:
            while self.calisma_durumu:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nSimülatör sonlandiriliyor...")
        finally:
            self.calisma_durumu=False
            thread_telemetri.join(timeout=2)
            thread_video.join(timeout=2)
            self.telemetri_socket.close()
            sys.exit(0)
if __name__ == "__main__":
    simulator = IHAsimulator(HOST,PORT_TELEMETRI,PORT_VIDEO)
    simulator.baslat()

