from django.shortcuts import render,redirect
from django.http import HttpResponse,StreamingHttpResponse
from .Expression_recognition import expressionRecognition
from django.conf import settings
from django.core.mail import send_mail
import face_recognition
import numpy as np
import datetime
# Create your views here.
import threading
from PIL import Image
import base64
import cv2
import time
import json
from .models import UserInfo,WarningRecord

url = "rtsp://admin:admin@59.66.68.38:554/cam/realmonitor?channel=1&subtype=0"
caplist = [cv2.VideoCapture(0),cv2.VideoCapture(url)]
t = ""
while True:
    t = input("the camera index(0/1):")
    if t in ['0','1']:
        break
cap = caplist[int(t)]

recordInfo=""
recordLock = threading.Lock()
imgFailed = ""


imgdataaa = [None]*5
npimg = [None]*5
index = -1
faceData = [None]*5
locations = [None]*5

def test():
    global imgdataaa,index,cap,npimg

    while(True):
        ret, frame = cap.read()
        frame, faces, infos,loc = expressionRecognition(frame)
        npimg[(index+1)%5] = frame[:,:,::-1]
        image = cv2.imencode('.jpg', frame)[1]

        imgdataaa[(index+1)%5] = bytes(image)
        faceData[(index+1)%5] = faces
        locations[(index+1)%5] = loc

        index = (index+1)%5


threading.Thread(target=test).start()


# cap.set(cv2.CAP_PROP_FPS, 60)


def monitor(request):
    status = checkLogStatus(request)
    if(status != None):
        return render(request,'monitor/index.html')
    else:
        return redirect('/monitor/login')


def monitor2(request):
    # return render(request,'monitor/index2.html')
    status = checkLogStatus(request)
    if(status != None):
        if status.isActive:
            return render(request,'monitor/index7.html')
        else:
            return redirect('/monitor/signup')
    else:
        return redirect("/monitor/login")

def personPage(request):
    global imgFailed
    status = checkLogStatus(request)
    if(status != None):
        if status.isActive:
            facelist = [i[0] for i in json.loads(status.faceLabel)]
            recordlist = WarningRecord.objects.filter(user=status)
            hidden = ""
            detectrange = json.loads(status.recordCondition)
            if(status.jurisdiction <=0):
                hidden = "hidden"
            if(imgFailed != ""):
                imgFailed = ""
                return render(request,'monitor/personpage.html',{"faces":facelist,"recordlist":recordlist,"hidden":hidden,"Msg":"alert('未检测人脸或人脸个数过多');","range":detectrange})
            else:
                return render(request,'monitor/personpage.html',{"faces":facelist,"recordlist":recordlist,"hidden":hidden,"Msg":"","range":detectrange})
        else:
            return redirect('/monitor/signup')
    else:
        return redirect("/monitor/login")


def newFrame(request):
    status = checkLogStatus(request)
    if(status != None):
        global cap
        ret, frame = cap.read()
        frame, list, infos = expressionRecognition(frame)
        image = cv2.imencode('.jpg', frame)[1]
        faces = []
        for it in list:
            newface = cv2.imencode('.jpg', it)[1]
            faces.append(str(base64.b64encode(newface))[2:-1])
        base64_data = str(base64.b64encode(image))[2:-1]

        dict = {"imagedata": base64_data,"facelist":faces,"record":""}

        record = checkRecord(user=status, faceInfoList=infos)
        print(record)
        if(record != None):
            dict["record"] = eval(record.recordInfo)["text"]
            print(dict["record"])
        return HttpResponse(json.dumps(dict))
    else:
        return redirect('/monitor/login')


def signUp(request):
    if request.method == 'GET':
        status = checkLogStatus(request)
        hidden = ""
        if status is not None:
            if not status.isActive:
                return render(request,'monitor/activating.html')
        return render(request,"monitor/signup.html",)
    elif(request.method == 'POST'):
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        vcode = request.POST.get("vcode")
        resend = request.POST.get("resend")
        if(vcode == None):
            if(resend == None):
                user = UserInfo.createUser(name=username,password=password,email=email)
                if(user == None):
                    return HttpResponse("email Used")
                else:
                    return HttpResponse("ok")
            else:
                user = UserInfo.objects.get(email=email)
                user.updateVerify()
                verify = eval(user.verificationCode)
                sendEmail(verify["Code"],user.email)
                return HttpResponse("ok")


        else:
            userinfo = UserInfo.objects.get(email=email)
            verifycode = eval(userinfo.verificationCode)["Code"]
            endtime = eval(userinfo.verificationCode)["EndTime"]
            if(datetime.datetime.now()<=endtime):
                if(vcode == verifycode):
                    userinfo.isActive = True
                    userinfo.save()
                    return HttpResponse("ok")
                else:
                    return HttpResponse("Code Wrong")
            else:
                return HttpResponse("offTime")
def sendEmail(code,email):
    msg = '<p>您好，您已被退学，您的验证码为'+code+'</p>'
    send_mail('验证邮件',message='内容', from_email=settings.EMAIL_FROM,
              recipient_list=[email],
              html_message=msg)


def login(request):
    if request.method == "GET":
        return render(request,"monitor/login.html")
    elif request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        result = UserInfo.objects.get(email=email)
        if result == None:
            return HttpResponse("No Such User")
        else:
            if password == result.password:
                request.session["monitorSession"] = result.session
                request.session.set_expiry(0)
                return HttpResponse("success")
                # redirect('/monitor/index')
            else:
                return HttpResponse("Password Wrong")


def checkLogStatus(request):
    session = request.session.get("monitorSession")
    if(session == None):
        return None
    user = UserInfo.objects.filter(session=session)
    if session!= None and len(user) == 1:
        return user[0]
    else:
        return None


def checkRecord(user,faceInfoList):
    try:
        recordText = ""
        condition = eval(user.recordCondition)
        totalnum = malenum = femalenum = 0
        for it in faceInfoList:
            print(it)
            if it["gender"] == "male":
                malenum +=1
            else:
                femalenum +=1
            totalnum +=1
        print(malenum)
        if (condition["totalLimit"] < totalnum):
            recordText += "num of faces >" + str(condition["totalLimit"])
        if(condition["faceLimit"][0]<malenum):
            recordText += "num of male >"+str(condition["faceLimit"][0])
            print(recordText)
        if(condition["faceLimit"][1]<femalenum):
            recordText += "num of female >"+str(condition["faceLimit"][1])
        # if( it["emotion"] in condition["emotions"]):
        #     recordText += "somebody is "+it["emotion"]

        if(recordText != ""):
            result = WarningRecord.objects.filter(user=user,recordInfo=json.dumps({"text":recordText,"info":faceInfoList}),recordTime__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
            if(len(result) == 0):
                record = WarningRecord.createRecord(recordInfo=json.dumps({"text":recordText,"info":faceInfoList}),user=user)
                return record
            else:
                return None
    except:
        return None





def streamFrame(user):
        while True:
            if(index == -1):
                time.sleep(0.1)
                continue
            imgdata = imgdataaa[index]
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + imgdata + b'\r\n\r\n')
            time.sleep(0.1)


def stream(request):
    global cap
    status = checkLogStatus(request)
    if (status != None):
        if status.isActive:
            return StreamingHttpResponse(streamFrame(status),content_type="multipart/x-mixed-replace;boundary=frame")
        else:
            redirect('/monitor/signup')
    else:
        return redirect('/monitor/login')


def getInfo(status):
    while(True):

        if (index == -1):
            time.sleep(0.1)
            continue
        faces = faceData[index]
        loc = locations[index]
        detectrange = json.loads(status.recordCondition)
        print(len(loc))
        print("loc：",loc)
        loclen = len(loc)
        for ele in range(loclen-1,-1,-1):
            print("ele:",loc[ele])
            print("range:",detectrange)
            if loc[ele][0]>detectrange["ymax"] or loc[ele][2]<detectrange["ymin"] or loc[ele][1]<detectrange["xmin"] or loc[ele][3]>detectrange["xmax"]:
                print("remove")
                loc.pop(ele)
        known = []
        name = []
        names = []
        facesLabel = json.loads(status.faceLabel)
        for i in facesLabel:
            known.append(np.array(i[1]))
            name.append(i[0])

        # face = face_recognition.face_encodings(npimg[index],locations[index])
        face = face_recognition.face_encodings(npimg[index],loc)
        print(len(face))
        faces_record = []
        for k_comparing_faces, ele in enumerate(face):
            if(len(known) != 0):
                result = [np.linalg.norm(knownone - ele) for knownone in known]
                for k, t in enumerate(result):
                    if t < 0.6:
                        faces_record.append([k_comparing_faces, k, t])

        names = ['unknown'] * len(face)
        used_k_face = set()
        used_k_known = set()
        faces_record.sort(key=lambda x: x[2])
        for k_face, k, _ in faces_record:
            if k_face not in used_k_face and k not in used_k_known:
                names[k_face] = name[k]
                used_k_face.add(k_face)
                used_k_known.add(k)

        print(names)
        record, info = checkWaring(status, names)
        print(info)
        js = {"names":names,"locations":loc,"info":info}
        # yield js.__str__()
        yield json.dumps(js)
        time.sleep(0.2)

def infoStream(request):
    status = checkLogStatus(request)
    if (status != None):
        if status.isActive:
            WarningRecord.createRecord("[]",status,"Camera "+t+"Connected")
            return StreamingHttpResponse(getInfo(status))
        else:
            return redirect('/monitor/signup')
    else:
        return HttpResponse(status=404)


def get_face_characteristics(face):
    image = Image.fromarray(face)
    face_landmarks_list = face_recognition.face_encodings(image)
    if len(face_landmarks_list) == 0:
        raise ValueError("No person here!")
        # 不想except的话直接return None就行
        # return None
    if len(face_landmarks_list) > 1:
        raise ValueError("More than one person here!")
    return face_landmarks_list[0]


def get_face_characteristics(filename):
    image = face_recognition.load_image_file(filename)
    face_landmarks_list = face_recognition.face_encodings(image)
    if len(face_landmarks_list) == 0:
        raise ValueError("No person here!")
        # 不想except的话直接return None就行
        # return None
    if len(face_landmarks_list) > 1:
        raise ValueError("More than one person here!")
    return face_landmarks_list[0]


import random,string,os
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
def analysisImg(request):
    global imgFailed
    status = checkLogStatus(request)
    if status != None:
        if status.isActive:
            if request.method == "GET":
                return render(request,"monitor/FaceLabel.html")
            elif request.method == "POST":

                facename = request.POST.get("name")
                img = request.FILES.get("img")
                if img == None:
                    return HttpResponse(status=404)
                name = ''.join(random.sample(string.ascii_letters + string.digits, 20))+img._name
                file = open('./monitor/img/'+name,'wb')
                for chunk in img.chunks():
                    file.write(chunk)
                file.close()
                try:
                    known_face_data = get_face_characteristics('./monitor/img/'+name)
                    jsoned = json.dumps(list(known_face_data))
                    print(jsoned)
                    status.updateFace(face=json.loads(jsoned),name=facename)
                except:
                    imgFailed = 'failed'
                    print(imgFailed)
                finally:
                    os.remove('./monitor/img/' + name)
                    return redirect("/monitor/userpage")

            else:
                return redirect('/monitor/signup')
    else:
        return HttpResponse(status=404)



def checkWaring(user,faceNameList):
    strr = json.dumps([temp for temp in faceNameList if temp !="unknown"])
    fr = WarningRecord.objects.filter(user=user).last()
    info = 'Camera '+t+':'
    if(fr != None):
        if fr.recordInfo != strr:

            oldList = json.loads(fr.recordInfo)
            nowList = json.loads(strr)
            for old in oldList:
                if old in nowList:
                    pass
                else:
                    info += old + ' 离开监视区域!'
            for now in nowList:
                if now in oldList:
                    pass
                else:
                    info += now + ' 进入监视区域!'
            return WarningRecord.createRecord(strr,user,info),info
        else:
            return None,info
    else:
        nowList = json.loads(strr)
        for ele in nowList:
            info += ele + '进入监视区域!'
        return WarningRecord.createRecord(strr, user,info),info

def passwordChange(request):
    status = checkLogStatus(request)
    if status != None:
        if status.isActive:
            if request.method == "GET":
                return render(request,'monitor/ChangePassWord.html')
            elif request.method == "POST":
                if request.POST.get("sendEmail") != None:
                    status.updateVerify()
                    verify = eval(status.verificationCode)
                    sendEmail(verify["Code"],status.email)
                    return HttpResponse("ok")
                else:
                    newpassword = request.POST.get("newpassword")
                    oldpassword = request.POST.get("oldpassword")
                    vcode = request.POST.get("vcode")
                    verifycode = eval(status.verificationCode)["Code"]
                    endtime = eval(status.verificationCode)["EndTime"]
                    if (datetime.datetime.now() <= endtime):
                        if (vcode == verifycode):
                            if oldpassword == status.password:
                                status.password = newpassword
                                status.save()
                                return HttpResponse("ok")
                            else:
                                return HttpResponse("PassWord Wrong")
                        else:
                            return HttpResponse("Code Wrong")
                    else:
                        return HttpResponse("offTime")
        else:
            return redirect("/monitor/signup")

    else:
        return redirect("/monitor/login")


def logout(request):
    status = checkLogStatus(request)
    if(status != None):
        request.session.flush()
    return redirect("/monitor/login")


def deleteFace(request):
    status = checkLogStatus(request)
    if(status != None):
        if not status.isActive:
            return redirect("/monitor/signup")
        faces = json.loads(status.faceLabel)
        for key in request.POST:
            for ele in faces:
                if(key == ele[0]):
                    faces.remove(ele)
                    break
        status.faceLabel = json.dumps(faces)
        status.save()
        return redirect("/monitor/userpage")
    else:
        return redirect("monitor/login")

def deleteRecord(request):
    status = checkLogStatus(request)
    if(status != None):
        if not status.isActive:
            return redirect("/monitor/signup")
        for key in request.POST:
            value = WarningRecord.objects.get(id=int(key))
            if(value.user == status):
                value.delete()
        return redirect("/monitor/userpage")
    else:
        return redirect("/monitor/login")

def addUser(request):
    status = checkLogStatus(request)
    if(status == None):
        return redirect("/monitor/login")
    if not status.isActive:
        return redirect("/monitor/signup")
    if(status.jurisdiction<10000):
        return redirect("/monitor/login")
    name = request.POST.get("username")
    passwod = request.POST.get("password")
    email = request.POST.get("email")
    user = UserInfo.createUser(name=name,password=passwod,email=email)
    user.isActive=True
    user.isActive=True
    if(user != None):
        return redirect("/monitor/super")
    else:
        return HttpResponse("emial Used")

def superpage(request):
    status = checkLogStatus(request)
    if(status != None):
        if not status.isActive:
            return redirect("/monitor/signup")
        if(status.jurisdiction >= 10000):
            userlist = UserInfo.objects.all()
            return render(request,'monitor/SuperUserPage.html',{"userlist":userlist})
    return redirect("/monitor/login")


def rangeChange(request):
    status = checkLogStatus(request)
    if (status != None):
        if not status.isActive:
            return redirect("/monitor/signup")
        xmin = int(request.POST.get("xmin"))
        xmax = int(request.POST.get("xmax"))
        ymin = int(request.POST.get("ymin"))
        ymax = int(request.POST.get("ymax"))
        newrange = {"xmax":xmax,"xmin":xmin,"ymax":ymax,"ymin":ymin}
        status.recordCondition = json.dumps(newrange)
        status.save()
        return redirect("/monitor/userpage")
    return redirect("/monitor/login")
