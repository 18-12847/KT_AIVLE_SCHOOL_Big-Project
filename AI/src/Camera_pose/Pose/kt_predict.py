
import tensorflow as tf
import boto3
from tensorflow import keras
import numpy as np
import matlab.engine
import matplotlib.pyplot as plt
import h5py
import requests
url = "http://15.165.98.14:8080/"
url_sse = url + "notifications/send-data"
url_db = url + "notifications/send-db"
# AWS 자격 증명 설정
session = boto3.Session(
    aws_access_key_id='',
    aws_secret_access_key=''
)

# S3 클라이언트 생성
s3_client = session.client('s3')

# 모델 파일 다운로드
s3_client.download_file('a031293-bucket', 'model/camera_wifi.h5', 'StateOfArt-load-model.h5')

# Define the path to the .h5 model file
# model_path = 'cnn_wifi.h5'

# Load the model from the .h5 file using h5py
# f = h5py.File(model_path, 'r')
# model_config = f.attrs.get('cnn_wifi.h5')
# model = tf.keras.models.model_from_json(model_config)
# model.load_weights(model_path)

eng = matlab.engine.start_matlab()
#/home/kimyonghwan/2019_Final/src/LR0.0001_BATCHSIZE200_NHIDDEN200/model.ckpt.meta
# saver = tf.train.import_meta_graph('cnn_wifi.h5') #modified
my_model = keras.models.load_model('StateOfArt-load-model.h5', compile=False)
print(my_model.summary())
# graph = tf.get_default_graph()
# x = graph.get_tensor_by_name("Placeholder:0")
# pred = graph.get_tensor_by_name("add:0")
# plt.ion()

b = np.arange(0, 15000)
act = ["onfloor", "empty", "for_lay", "back_lay", "indanger"]
# tmp = 0

#매틀랩으로 실시간 Prediction
while 1: #modified

    # tmp+=1
    k = 1
    t = 0
    #real time data input but now one data
    #/home/kimyonghwan/linux-80211n-csitool-supplementary/netlink/190528_data_2/190528_2_walking2.dat
    # csi_trace = eng.read_bf_file('../190528_Dataset2/sitdown49.dat') #modified
    csi_trace = eng.read_bf_file('aTtest1') #modified
    kkk = len(csi_trace)
    if len(csi_trace) < 500: #modified
        continue #modified
    #여기서부터 시작 그 위는 있을리 없어도 컨티뉴 한다. 혹시 모르니.
    ARR_FINAL = np.empty([0, 90], float)
    xx = np.empty([1, 500, 90], float)
    xx1 = np.empty([0], float)
    yy1 = np.empty([0], float)
    zz1 = np.empty([0], float)
    try:
        while (k <= 500): #실시간 데이터는 500줄만 읽어온다. 그게 아니고 그냥 시간임. #modified
            csi_entry = csi_trace[t] #여기 t를 이해해야겠네. matlab을 이해해야 한다.
            try:
                csi = eng.get_scaled_csi(csi_entry)
                A = eng.abs(csi)
                ARR_OUT = np.empty([0], float)

                ARR_OUT = np.concatenate((ARR_OUT, A[0][0]), axis=0)
                ARR_OUT = np.concatenate((ARR_OUT, A[0][1]), axis=0)
                ARR_OUT = np.concatenate((ARR_OUT, A[0][2]), axis=0)

                xx1 = np.concatenate((xx1, A[0][0]), axis = 0)
                yy1 = np.concatenate((yy1, A[0][1]), axis = 0)
                zz1 = np.concatenate((zz1, A[0][2]), axis = 0)
                ARR_FINAL = np.vstack((ARR_FINAL, ARR_OUT))
                k = k + 1
                t = t + 1

            except matlab.engine.MatlabExecutionError:
                print('MatlabExecutionError occured!!!')
                # break #modified
            xx[0] = ARR_FINAL
            break

    except ValueError:
        print('ValueError occured!!!')
        # continue #modified
    #
    #
    xx = tf.expand_dims(xx, -1)    
    predi = my_model.predict(xx)
    
    n = tf.argmax(predi, 1)
    ddd = {}
    
    ddd["label"] = 0
    ddd["serialNumber"] ="123456"
    ddd["wifi"] = "True"
    ddd["camera"] = "True"
    
    headers = {'Content-Type': 'application/json; charset : utf-8'}
    response = requests.post(url_sse, json=ddd, headers = headers)
    response = requests.post(url_db, json=ddd, headers = headers)
    
    print(ddd)
    print(n)
    #
    # with tf.Session(config=tf.ConfigProto(log_device_placement=True)) as sess:
    #     # saver.restore(sess, 'cnn_wifi.h5')


        # n = pred.eval(feed_dict={x: xx})
        # n2 = tf.argmax(n, 1)
        # result = n2.eval()
        # print(act[int(result)])
        # sess.close()

