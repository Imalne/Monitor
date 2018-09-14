import cv2
from keras.models import load_model,model_from_json
import numpy as np
import tensorflow as tf
import keras
import face_recognition
import PIL.Image
keras.backend.clear_session()

emotion_classifier = load_model('./monitor/simple_CNN.985-0.66_2.hdf5')
gender_classifier = load_model('./monitor/gender_mini_XCEPTION.21-0.95.hdf5')
graph = tf.get_default_graph()
face_classifier = cv2.CascadeClassifier("./monitor/haarcascade_frontalface_default.xml")



emotion_labels = {
    0: 'angry',
    1: 'Disgust',
    2: 'fear',
    3: 'happy',
    4: 'sad',
    5: 'surprised',
    6: 'neutral'
}

gender_labels = {1:'male',0:'female'}



def  expressionRecognition(img):
    global graph
    with graph.as_default():
        img = cv2.resize(img,(640,480))
        facesImg = []
        faceInfo = []
        locations = []
        test = img[:,:,::-1]
        # result = face_recognition.face_locations(test)
        # locations = result
        # for i in result:
        #     cv2.rectangle(img,(i[3],i[0]),(i[1], i[2]),(255, 255, 255), 2)
        #     face_org = test[(i[3],i[0]),(i[1],i[2])]
        #     facesImg.append(face_org)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=3, minSize=(40, 40))
        # color = (0, 255, 255)
        #
        # facesImg = []


        for (x, y, w, h) in faces:
            # print(x,y,w,h)
            # locations.append([y,x+w,y+h,x])
            locations.append([int(y),int(x+w),int(y+h),int(x)])
            face_org = test[y:y+h, x:x+w]
            # print(test.shape)
            facesImg.append(face_org)
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 255, 255), 2)
        # locations.append([y,x+h,y+w,x])
        # face_org = test[(x,y), (x+w,y+h)]
        # cv2.rectangle(img, (y,x), (y+w,x+h), (255, 255, 255), 2)
        #y+h,x,x+w,y
            gray_face_org = gray[(y):(y + h), (x):(x + w)]
        #     face_org = img[(max(y-100,0)):(min(y + h+40,img.shape[0]-1)), (max(0,x-20)):(min(x + w+20,img.shape[1]-1))]
        #
            gray_face = cv2.resize(gray_face_org, (48, 48))
            gray_face = gray_face / 255.0
            gray_face = np.expand_dims(gray_face, 0)
            gray_face = np.expand_dims(gray_face, -1)
            emotion = emotion_labels[np.argmax(emotion_classifier.predict(gray_face))]
            print(emotion)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(img,emotion, (x + 6, y - 6), font, 1.0, (255, 255, 255), 1)
        #
        #     gray_face_2 = cv2.resize(gray_face_org, (64, 64))
        #     gray_face_2 = gray_face_2 / 255.0
        #     gray_face_2 = np.expand_dims(gray_face_2, 0)
        #     gray_face_2 = np.expand_dims(gray_face_2, -1)
        #     gender = gender_labels[np.argmax(gender_classifier.predict(gray_face_2))]
        #     print(gender)
        #
        #     face_org = face_org[:,:,::-1]
        #
        #     facesImg.append(face_org[0])
        #
        #     faceInfo.append({'gender':gender,'emotion':emotion})
        #     x = int(x)
        #     y = int(y)
        #     w = int(w)
        #     h = int(h)
        #     print(img.shape)
        #     cv2.rectangle(img, (max(x - 20, 0), max(y - 100, 0)),
        #                   (min(x + h + 20, img.shape[1]), min(y + w + 40, img.shape[0])),
        #                   (255, 255, 255), 2)
        #
        #     # cv2.rectangle(img, (x-20, y-100), (x + h+20, y + w+40),
        #     #               (255, 255, 255), 2)
        #     font = cv2.FONT_HERSHEY_DUPLEX
        #     cv2.putText(img, gender+'-'+emotion, (x + 6, y - 6), font, 1.0, (255, 255, 255), 1)
        return img,facesImg,faceInfo,locations