
import cv2, os

cam = cv2.VideoCapture(0)
detector = cv2.CascadeClassifier('haarcascade.xml')

student_id = input("Enter Student ID: ")
name = input("Enter Student Name: ")

os.makedirs(f"dataset/{name}", exist_ok=True)

count = 0
while True:
    ret, img = cam.read()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, 1.3, 5)

    for (x,y,w,h) in faces:
        count += 1
        cv2.imwrite(f"dataset/{name}/{student_id}_{count}.jpg", gray[y:y+h, x:x+w])
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)

    cv2.imshow("Register Face", img)
    if cv2.waitKey(1)==27 or count>=30:
        break

cam.release()
cv2.destroyAllWindows()
print("Face registration completed")
