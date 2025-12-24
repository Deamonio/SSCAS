## SERVER ##

import socket
from _thread import *
from roboflow import Roboflow
import cv2
import sys
import numpy as np
import json
import seaborn as sns
from datetime import datetime
import matplotlib.pyplot as plt
num=1
client_sockets = []

HOST = socket.gethostbyname(socket.gethostname())
PORT = 9999

file_path="prediction.json"

def threaded(client_socket, addr):
    num=1
    print('>> Connected by :', addr[0], ':', addr[1])

    ## process until client disconnect ##
    while True:
        level_Density=[]
        try:
            ## send client if data recieved(echo) ##
            data = client_socket.recv(1024)

            if not data:
                print('>> Disconnected by ' + addr[0], ':', addr[1])
                break

            for client in client_sockets:
                if client != client_socket:
                    client.send(data)

            if data.decode()=="recog":
                print('>> Received from ' + addr[0], ':', addr[1], data.decode())
                current_time = datetime.now()
                rf = Roboflow(api_key="TiNMvhxIoHsoajs9cDg4")
                project = rf.workspace().project("lg-cns")
                model = project.version(2).model
                predict_json=model.predict("static/assets/img/pre_picture.jpg", confidence=40, overlap=30).json()
                print(predict_json)

                with open("prediction.json", "w") as json_file:
                    json.dump(predict_json, json_file)
                print("Prediction saved to prediction.json")
                try:
                    with open(file_path, 'r') as json_file:
                        data = json.load(json_file)
                        print('JSON 데이터:', data)
                except FileNotFoundError:
                    print(f'파일을 찾을 수 없습니다: {file_path}')
                except json.JSONDecodeError as e:
                    print(f'JSON 파일 파싱 오류: {e}')
                except Exception as e:
                    print(f'오류 발생: {e}')
                
                image_path = 'static/assets/img/pre_picture.jpg'

                desired_width = int(data.get('image').get('width'))
                desired_height = int(data.get('image').get('height'))
                print(desired_width,desired_height)

                image = cv2.imread(image_path)
                try:
                    resized_image = cv2.resize(image, (desired_width, desired_height))
                except:
                    pass
                predictions = data.get("predictions", [])
                results = []
                person_num=0

                for prediction in predictions:
                    class_name = "person"
                    x = prediction.get("x", 0)
                    y = prediction.get("y", 0)
                    width = prediction.get("width", 0)
                    height = prediction.get("height", 0)
                    person_num+=1
                    # 결과 배열에 추가
                    results.append([class_name, x, y, width, height])

                # 결과 출력
                for result in results:
                    print(result)
                # 바운딩 박스 그리기
                for result in results:
                    class_name, x, y, width, height = result
                    x1, y1 = int(x - width / 2), int(y - height / 2)  # 바운딩 박스 좌측 상단 꼭짓점 계산
                    x2, y2 = int(x + width / 2), int(y + height / 2)  # 바운딩 박스 우측 하단 꼭짓점 계산
                    color = (0, 255, 0)  # 바운딩 박스 색상 (여기서는 녹색)
                    thickness = 2  # 바운딩 박스 두께

                    cv2.rectangle(resized_image, (x1, y1), (x2, y2), color, thickness)

                    text = f"{class_name}"
                    cv2.putText(resized_image, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)

                output_image_path = 'static/assets/img/saved_picture.jpg'
                cv2.imwrite(output_image_path, resized_image)
                
                Full_Size=desired_width*desired_height
                people_area=0
                for result in results:
                    people_area += (int(result[3])*int(result[4]))
                FUll_Density=(people_area/Full_Size)*100
                print(f'{FUll_Density}%')
                                 
                Small_Area=Full_Size/25
                Full_Area = [[0 for i in range(desired_width)] for j in range(desired_height)]
                for person_area in results:
                    class_name, x, y, width, height = person_area
                    x1, y1 = int(x - width / 2), int(y - height / 2)  # 바운딩 박스 좌측 상단 꼭짓점 계산
                    x2, y2 = int(x + width / 2), int(y + height / 2)  # 바운딩 박스 우측 하단 꼭짓점 계산
                    for j in range(y1,y2):
                        for i in range(x1,x2):
                            Full_Area[j][i]=1

                print("\n")
                cnt=0
                temp_Small_Area_Density=[]
                for col in range(5):
                    for row in range(5):
                        x_range=[(desired_width/5)*row,(desired_width/5)*(row+1)]
                        y_range=[(desired_height/5)*col,(desired_height/5)*(col+1)]
                        # print(x_range,y_range)
                        for j in range(int(y_range[0]),int(y_range[1])-1):
                            for i in range(int(x_range[0]),int(x_range[1]-1)):
                                if Full_Area[j][i]==1:
                                    cnt+=1
                        temp=(cnt/Small_Area)*100
                        temp_Small_Area_Density.append(temp)
                        cnt=0
                print(temp_Small_Area_Density)
                Small_Area_Density=[]
                for j in range(5):
                    Small_Area_Density.append([int(temp_Small_Area_Density[5*(j+1)-5]),int(temp_Small_Area_Density[5*(j+1)-4]),int(temp_Small_Area_Density[5*(j+1)-3]),int(temp_Small_Area_Density[5*(j+1)-2]),int(temp_Small_Area_Density[5*(j+1)-1])])
                print(Small_Area_Density)
                level_Density=[]
                for j in range(5):
                    level_arr=[]
                    for i in range(5):
                        if Small_Area_Density[j][i]>=0 and Small_Area_Density[j][i]<10:
                            level_arr.append(0)
                        if Small_Area_Density[j][i]>=10 and Small_Area_Density[j][i]<20:
                            level_arr.append(1)
                        if Small_Area_Density[j][i]>=20 and Small_Area_Density[j][i]<30:
                            level_arr.append(2)
                        if Small_Area_Density[j][i]>=30 and Small_Area_Density[j][i]<40:
                            level_arr.append(3)
                        if Small_Area_Density[j][i]>=40 and Small_Area_Density[j][i]<50:
                            level_arr.append(4)
                        if Small_Area_Density[j][i]>=50 and Small_Area_Density[j][i]<60:
                            level_arr.append(5)
                        if Small_Area_Density[j][i]>=60 and Small_Area_Density[j][i]<70:
                            level_arr.append(6)
                        if Small_Area_Density[j][i]>=70 and Small_Area_Density[j][i]<80:
                            level_arr.append(7)
                        if Small_Area_Density[j][i]>=80 and Small_Area_Density[j][i]<90:
                            level_arr.append(8)
                        if Small_Area_Density[j][i]>=90 and Small_Area_Density[j][i]<=100:
                            level_arr.append(9)
                    level_Density.append(level_arr)

                try:
                    sns.heatmap(level_Density, vmin=0, vmax=9, annot=False, cmap='RdPu')
                    plt.savefig(f'static/assets/img/heatmap.jpg',format='jpg')
                except:
                    pass

                try:
                    plt.close()
                except:
                    pass
                data=''
                time_data=current_time.strftime("%Y-%m-%d %H'%M'%S")
                place="지하철역"
                for client in client_sockets:
                    client.send(f'analysis:{round(FUll_Density,2)}:{person_num}:{time_data}:{place}'.encode())


        except ConnectionResetError as e:
            print('>> Disconnected by ' + addr[0], ':', addr[1])
            break
    
    if client_socket in client_sockets:
        client_sockets.remove(client_socket)
        print('remove client list : ', len(client_sockets))

    client_socket.close()

############# Create Socket and Bind ##

print('>> Server Start with ip :', HOST)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

############# Client Socket Accept ##

try:
    while True:
        print('>> Wait')

        client_socket, addr = server_socket.accept()
        client_sockets.append(client_socket)
        start_new_thread(threaded, (client_socket, addr))
        print("참가자 수 : ", len(client_sockets))
except Exception as e:
    print('에러 : ', e)

finally:
    server_socket.close()