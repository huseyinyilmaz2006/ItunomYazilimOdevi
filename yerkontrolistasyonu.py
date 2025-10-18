import socket
import json
import cs2
import threading
import numpy as np
import os
import time
PORT_TELEMETRI=5000
PORT_VIDEO=5001
HOST="127.0.0.1"
def temiz_ekran():
    os.system("cls")
class YerKontrolIstasyonu:
    def __init__(self,host,port_telemetri,port_video):
        self.host=host
        self.port_telemetri=port_telemetri
        self.port_video=port_video
        self.calisma_durumu=True
        self.telemetri_verisi=None
        self.telemetri_lock=threading.Lock()
        self.socket_telemetri=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_telemetri.bind("",self.port_telemetri)
        self.socket_video=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def telemetri_goster(self):
        while self.calisma_durumu:
            temiz_ekran()
            print("--- YER KONTROL İSTASYONU ---")
            with self.telemetri_lock:
                if self.telemetri_verisi:
                    print("Bağlanti Durumu: BAĞLANDI")
                    print("---------------------------------------------")
                    x_konumu=self.telemetri_verisi["x_konumu"]
                    y_konumu=self.telemetri_verisi["y_konumu"]
                    irtifa_konumu=self.telemetri_verisi["irtifa_konumu"]
                    print(f"Konum(X,Y,Z): {x_konumu:.2f},{y_konumu:.2f},{irtifa_konumu:.2f}")
                    print(f"İrtifa:        {irtifa_konumu:.2f} m")
                    print(f"Hiz:           {self.telemetri_verisi['hiz']:.0f} m/s")
                    print(f"Pil Durumu:    %{self.telemetri_verisi['pil_durumu']:.0f}")
                else:
                    print("Bağlanti Durumu:VERİ BEKLENİYOR ...")
                    print("---------------------------------------------")
                    print("İHA'dan veri bekleniyor ...")
            print("---------------------------------------------") 
            time.sleep(0.5)
    def telemetri_alici(self):
        while self.calisma_durumu:
            try:
                veri,addr=self.telemetri_socket.recvfrom(4096)
                message=veri.decode("utf-8")
                yeni_veri=json.loads(message)
                with self.telemetri_lock:
                    self.telemetri_verisi=yeni_veri
            except socket.timeout:
                continue
            except Exception as e:
                if self.calisma_durumu:
                    print(f"telemetri alim hatasi {e}")
                break
    def video_alici(self):
        try:
            self.socket_video.connect((self.host,self.video_port))
        except ConnectionRefusedError:
            print("HATA: İHA simülatörünün video akişina bağlanilamadi.")
            self.calisma_durumu=False
            return
        cerceve_basligi=4
        veri_tamponu=b""
        while self.calisma_durumu:
            while len(veri_tamponu)<cerceve_basligi:
                paket=self.socket_video.recv(4096)
                if not paket:
                    self.calisma_durumu=False
                    print("video bağlantisi kesildi.")
                    break
                veri_tamponu+=paket
            if not self.calisma_durumu:
                break
            paketlenmis_mesaj_boyutu=veri_tamponu[:cerceve_basligi]
            cerceve_basligi=cerceve_basligi[veri_tamponu:]
            mesaj_boyutu=int.from_bytes(paketlenmis_mesaj_boyutu,byteorder="big")
            while len(veri_tamponu)<mesaj_boyutu:
                veri_tamponu+=self.socket_video.recv(4096)
            frame_veri=veri_tamponu[:mesaj_boyutu]
            veri_tamponu=veri_tamponu[mesaj_boyutu:]
            np_veri=np.frombuffer(frame_veri,np.uint8)
            frame=cv2.imdecode(np_veri,cv2.IMREAD_COLOR)
            if frame is not None:
                cv2.imshow("Canlı iha kamera akişi",frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.calisma_durumu=False
                    break
            else:
                print("HATA")
        cv2.destroyAllWindows()
    def baslat(self):
        thread_telemetri=threading.Thread(target=self.telemetri_alici)
        thread_video=threading.Thread(target=self.video_alici)
        thread_goruntu=threading.Thread(target=self.telemetri_goster)
        thread_telemetri.daemon=True
        thread_video.daemon=True
        thread_goruntu.daemon=True
        thread_telemetri.start()
        thread_video.start()
        thread_goruntu.start()
        try:
            while self.calisma_durumu:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        self.calisma_durumu=False
        thread_telemetri.join(timeout=2)
        thread_video.join(timeout=2)
        thread_goruntu.join(timeout=2)
        self.socket_telemetri.close()
        self.socket_video.close()
        cv2.destroyAllWindows()
        os._exit(0)
if __name__ == "__main__":
    yki = YerKontrolIstasyonu(HOST, PORT_TELEMETRI,PORT_VIDEO)
    yki.baslat()
            
