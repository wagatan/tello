# coding: utf-8
# GUIで動画取得を可能にする。

import Tkinter as tk # Python 2.7 だとTは大文字
import time
import cv2
import datetime
import socket
import threading
import numpy as np

# GUI画面生成
root = tk.Tk()
root.title(u'Tello Auto Sample')
root.geometry('500x300')

event = threading.Event()   # イベント
videoWriter = False         # ビデオライター
isVideo = False             # 録画フラグ・オフ
isShoot = False             # 静止画撮影フラグ
data = []                   # 画像データ格納用のリスト
csvfile_path = "log.csv"    # 記録データの保存先パス
start = time.time()         # 開始時間

# ここに通信用のプログラムを追加

# UDPソケット生成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
sock.bind(('', 9000))

# Tello にコマンドを送る関数
tello_address = ('192.168.10.1', 8889)

# コマンド発行処理
def send_command(msg):
    msg = msg.encode(encoding="utf-8") 
    sock.sendto(msg, tello_address)

# tello 準備
send_command('command') 
send_command('streamon')

# ビデオキャプチャ生成
cap=cv2.VideoCapture('udp://0.0.0.0:11111')

# 画像解析セクション
def yelow_detect(img):
    # HSV色空間に変換
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 黄色のHSVの値域
    hsv_min = np.array([20,80,10])
    hsv_max = np.array([50,255,255])
    mask = cv2.inRange(hsv, hsv_min, hsv_max)

    return mask

# ブロブ解析
def analysis_blob(binary_img):
    # 2値画像のラベリング処理
    label = cv2.connectedComponentsWithStats(binary_img)

    # ブロブ情報を項目別に抽出
    n = label[0] - 1
    data = np.delete(label[2], 0, 0)
    center = np.delete(label[3], 0, 0)

    # ブロブ面積最大のインデックス
    max_index = np.argmax(data[:, 4])

    # 面積最大ブロブの情報格納用
    maxblob = {}

    # 面積最大ブロブの各種情報を取得
    maxblob["upper_left"] = (data[:, 0][max_index], data[:, 1][max_index]) # 左上座標
    maxblob["width"] = data[:, 2][max_index]  # 幅
    maxblob["height"] = data[:, 3][max_index]  # 高さ
    maxblob["area"] = data[:, 4][max_index]   # 面積
    maxblob["center"] = center[max_index]  # 中心座標
    
    return maxblob


# 飛行用のコマンド
# ボタンの定義と処理

def btnTakeoff(): # 離陸
    send_command('takeoff')
    time.sleep(0.5)
  
def btnLand(): # 着陸
    send_command('land')
    time.sleep(0.5)

def btnAuto(): # 自動
    send_command('command') 
    time.sleep(1)
    send_command('streamon')
    time.sleep(1)
    send_command('takeoff')
    time.sleep(5)
    start_rec() # 録画開始
    time.sleep(1)
    send_command('up 50')
    time.sleep(5)
    send_command('cw 360')
    time.sleep(10)
    send_command('down 50')
    time.sleep(5)
    stop_rec()  # 録画終了
    time.sleep(1)
    send_command('land')
  
def btnUp(): # 上昇
    send_command('up 50')
    time.sleep(0.5)
  
def btnDown(): # 下降
    send_command('down 50')
    time.sleep(0.5)

def btnCcw(): # 左旋回
    send_command('ccw 30')
    time.sleep(0.5)

def btnCw(): # 右旋回
    send_command('cw 30')
    time.sleep(0.5)

def btnForward(): # 前進
    send_command('forward 50')
    time.sleep(0.5)
  
def btnBack(): # 後退
    send_command('back 50')
    time.sleep(0.5)
  
def btnLeft(): # 左
    send_command('left 50')
    time.sleep(0.5)
  
def btnRight(): # 右
    send_command('right 50')
    time.sleep(0.5)

# 録画開始
def start_rec():
    global videoWriter
    global isVideo
    FOURCC = cv2.VideoWriter_fourcc(*'mp4v')
    FPS = 30.0
    SIZE = (640, 480)
    now = datetime.datetime.now()
    dt_str = "{0:%Y%m%d%H%M%S}".format(now)
    # vfname='video' + dt_str + '.mp4'
    vfname='video.mp4'
    videoWriter = cv2.VideoWriter( vfname, FOURCC, FPS, SIZE)	
    isVideo = True
    print('rec...')
    btnRec['state'] = tk.DISABLED

# 録画停止
def stop_rec():
    global isVideo
    isVideo = False
    videoWriter.release()
    print("...rec stop")
    btnRec['state'] = tk.NORMAL

# データ受信処理
def recv():
    while True: 
        try:
            # メッセージを受信
            data, server = sock.recvfrom(1518)
      
            # 末尾の改行コードを削除
            strData = data.decode( encoding="utf-8").strip()

            # 2019.08.15 add wagata
            lblInfo['text']=strData
            # バッテリ 30% より少なくなると着陸
            if strData.isdecimal() == True and int(strData) < 30:
                print(lblBattery['fg'])
                lblBattery['fg']='red'
                send_command('land')
                time.sleep(0.5)

            # バッテリー
            if strData.isdecimal() == True:  
                lblBattery['text']='Battery: ' + strData + ' %'
            elif strData[-2:] == 'dm': # 高度
                lblHeight['text'] = 'Height: ' + strData
            elif strData[-1:] == ';':  # 傾き
                # 「;」で区切る
                splitData = strData.split(';')
                # 「:」で区切る
                yaw = splitData[2].split(':')
                lblYaw['text'] = 'Yaw: ' + yaw[1] + ' °'
            else:
                print(strData)
        except Exception as ex:
          #2019.08.15 add wagata
          print(ex)
          break

# ステータスチェック処理
def get_info():
    while True:
        # バッテリー
        send_command('battery?')
        time.sleep(0.5)
        # 高度
        send_command('height?')
        time.sleep(0.5)
        # 傾き
        send_command('attitude?')
        time.sleep(0.5)
        # 時間
        send_command('time?')
        time.sleep(0.5)
        # 温度
        send_command('temp?')
        time.sleep(0.5)

#動画撮影用のスレッドを作成
def get_movie():
    global frame
    global data
    global start
    try:

        while True:
            # キャプチャ画像を画面に表示
            ret, frame = cap.read()
            frame = cv2.resize(frame, dsize=(640,480))

            # カラートラッキング（黄色）
            mask = yelow_detect(frame)
            # マスク画像をブロブ解析（面積最大のブロブ情報を取得）
            target = analysis_blob(mask)

            # 面積最大ブロブの中心座標を取得
            center_x = int(target["center"][0])
            center_y = int(target["center"][1])

            # 最大面積を取得
            area = int(target["area"])

            # フレームに面積最大ブロブの中心周囲を円で描く
            cv2.circle(frame, (center_x, center_y), 30, (0, 200, 0),
                       thickness=1, lineType=cv2.LINE_AA)

            # 経過時間, x, yをリストに追加
            data.append([time.time() - start, center_x, center_y, area])
            sp_time = str((time.time() - start))
            cv2.putText(frame, sp_time, (10, 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), 1, cv2.LINE_AA)

            cv2.imshow('Tello Insp Yellow', frame)

            # 動画保存
            if isVideo:
                videoWriter.write(frame)

            # キー入力待ち
            key = cv2.waitKey(1)
            if key == 27:  # ESCキー
                break

    except Exception as ex:
        print(ex)
    finally:
        # 終了処理
        # cap.release()
        # cv2.destroyAllWindows()
        send_command('streamoff')

# 静止画撮影の準備
def shoot():
    try:
        # 静止画保存
        now = datetime.datetime.now()
        dt_str = "{0:%Y%m%d%H%M%S}".format(now)
        isShoot = True
        cv2.imwrite('img' + dt_str + '.jpg',frame)
        isShoot = False
    except Exception as ex:
        print (ex)
    finally:
        print ('Shoot!')

# Tello EDUの情報
# ラベルの設定（文字と位置）

lblBattery=tk.Label(text=u'Battery: --')
lblHeight = tk.Label(text=u'Height: --')
lblYaw = tk.Label(text=u'Yaw: --')
lblBattery.place(x=10, y=10)
lblHeight.place(x=110, y=10)
lblYaw.place(x=210, y=10)

# 2019.08.15 add wagata
# 受信しているストリーム情報追加
lblInfo=tk.Label(text=u'Info: --')
lblInfo.place(x=10, y=200)

# 離陸、着陸、自動
# ボタンの位置、振る舞いの定義

btnTakeoff = tk.Button(text=u'離陸', width=10, command=btnTakeoff)
btnLand = tk.Button(text=u'着陸', width=10, command=btnLand)
btnAuto = tk.Button(text=u'自動', width=10, command=btnAuto)
btnTakeoff.place(x=10, y=50)
btnLand.place(x=10, y=80)
btnAuto.place(x=10, y=130)

# 上昇、下降、旋回
# ボタンの位置、振る舞いの定義

btnUp = tk.Button(text=u'上昇', width=5, command=btnUp)
btnDown = tk.Button(text=u'下降', width=5, command=btnDown)
btnCcw = tk.Button(text=u'左旋回',width=5, command=btnCcw)
btnCw = tk.Button(text=u'右旋回', width=5, command=btnCw)
btnUp.place(x=200, y=50)
btnDown.place(x=200, y=110)
btnCcw.place(x=150, y=80)
btnCw.place(x=250, y=80)

# 前進、後退、左右
# ボタンの位置、振る舞いの定義

btnForward = tk.Button(text=u'前進', width=5, command=btnForward)
btnBack = tk.Button(text=u'後進', width=5, command=btnBack)
btnLeft = tk.Button(text=u'左', width=5, command=btnLeft)
btnRight = tk.Button(text=u'右', width=5, command=btnRight)
btnForward.place(x=390, y=50)
btnBack.place(x=390, y=110)
btnLeft.place(x=340, y=80)
btnRight.place(x=440, y=80)

# 録画開始、録画終了
# ボタンの位置、振る舞いの定義

btnRec = tk.Button(text=u'録画', width=5, command=start_rec)
btnRecstp = tk.Button(text=u'停止', width=5, command=stop_rec)
btnPhoto = tk.Button(text=u'写真', width=5, command=shoot)
btnRec.place(x=100, y=250)
btnRecstp.place(x=150, y=250)
btnPhoto.place(x=200, y=250)

# スレッドの定義　ステータスチェック処理
# chkThread生成
chkThread = threading.Thread(target=get_info)
chkThread.setDaemon(True)
chkThread.start()

# スレッドの定義　データ受信処理
recvThread=threading.Thread(target=recv)
recvThread.start()

# movTread生成
# スレッドの定義　カメラスタート
movThread = threading.Thread(target=get_movie)
movThread.setDaemon(True)
movThread.start()

root.mainloop() # メインループ

# CSVファイルに保存
np.savetxt(csvfile_path, np.array(data), delimiter=",")

cap.release()
cv2.destroyAllWindows()

sock.close() # 終了処理

print ('--- END ---')

