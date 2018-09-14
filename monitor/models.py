from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import string
import random
import datetime
import json

class UserInfo(models.Model):
    name = models.CharField(max_length=12)
    password = models.CharField(max_length=16)
    email = models.CharField(max_length=40)
    session = models.CharField(max_length=100)
    jurisdiction = models.IntegerField(default=0)
    verificationCode = models.CharField(max_length=40)
    recordCondition = models.CharField(max_length=2048)
    isActive = models.BooleanField(default=False)
    isDelete = models.BooleanField(default=False)
    faceLabel = models.TextField(default="[]")

    @classmethod
    def createUser(cls,name,password,email,jurisdiction=0):
        searchresult =UserInfo.objects.filter(email=email)
        if(len(searchresult) != 0):
            return None
        user = UserInfo()
        user.name = name;
        user.password = password
        user.email = email
        user.recordCondition = json.dumps({"xmax":640,"ymax":480,"xmin":0,"ymin":0})

        user.session = ''.join(random.sample(string.ascii_letters + string.digits, 20))
        verify = {"Code":''.join(random.sample(string.ascii_letters + string.digits, 6)),"EndTime":datetime.datetime.now()+datetime.timedelta(seconds=60)}
        user.verificationCode = verify.__str__()
        user.jurisdiction = jurisdiction
        user.save()
        return user
    def updateVerify(self):
        verify = {"Code": ''.join(random.sample(string.ascii_letters + string.digits, 6)),
                  "EndTime": datetime.datetime.now() + datetime.timedelta(seconds=60)}
        self.verificationCode = verify.__str__()
        self.save()

    def updateFace(self,face,name):
        sr = json.loads(self.faceLabel)
        ele = []
        ele.append(name)
        ele.append(face)
        sr.append(ele)
        self.faceLabel = json.dumps(sr)
        self.save()





class WarningRecord(models.Model):
    recordTime = models.DateTimeField(auto_created=True)
    recordInfo = models.TextField(default="")
    recordText = models.TextField(default="")
    isDelete = models.BooleanField(default=False)
    recordLevel = models.IntegerField(default=0)
    user = models.ForeignKey(UserInfo,on_delete=models.CASCADE)

    @classmethod
    def createRecord(cls,recordInfo,user,text="",recordLevel=0):
        record = WarningRecord()
        record.recordInfo = recordInfo
        record.recordLevel = recordLevel
        record.recordTime = datetime.datetime.now()
        record.user = user
        record.recordText = text
        record.save()
        return record



