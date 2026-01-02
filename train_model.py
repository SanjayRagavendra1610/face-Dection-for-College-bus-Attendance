
import cv2, os, numpy as np

recognizer = cv2.face.LBPHFaceRecognizer_create()
faces, ids = [], []

for root, dirs, files in os.walk("dataset"):
    for file in files:
        if file.lower().endswith(".jpg"):
            path = os.path.join(root, file)
            img = cv2.imread(path, 0)
            if img is None:
                continue
            id = int(file.split("_")[0])
            faces.append(img)
            ids.append(id)

if len(faces) == 0:
    print("No training images found")
    exit()

recognizer.train(faces, np.array(ids))
os.makedirs("trainer", exist_ok=True)
recognizer.save("trainer/trainer.yml")
print("Training completed successfully")
