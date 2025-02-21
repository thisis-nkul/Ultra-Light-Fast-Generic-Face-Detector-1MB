"""
This code is used to batch detect images in a folder.
"""
import argparse
import os
import sys

import cv2

from vision.ssd.config.fd_config import define_img_size

parser = argparse.ArgumentParser(
    description='detect_imgs')

parser.add_argument('--net_type', default="RFB", type=str,
                    help='The network architecture ,optional: RFB (higher precision) or slim (faster)')
parser.add_argument('--input_size', default=1280, type=int,
                    help='define network input size,default optional value 128/160/320/480/640/1280')
parser.add_argument('--threshold', default=0.6, type=float,
                    help='score threshold')
parser.add_argument('--candidate_size', default=1500, type=int,
                    help='nms candidate size')
parser.add_argument('--path', default="imgs", type=str,
                    help='imgs dir')
parser.add_argument('--test_device', default="cuda:0", type=str,
                    help='cuda:0 or cpu')
parser.add_argument('--txt_file', default='/content/folders.txt', type=str,
                    help='txt file containing paths of folders')
args = parser.parse_args()
define_img_size(args.input_size)  # must put define_img_size() before 'import create_mb_tiny_fd, create_mb_tiny_fd_predictor'

from vision.ssd.mb_tiny_fd import create_mb_tiny_fd, create_mb_tiny_fd_predictor
from vision.ssd.mb_tiny_RFB_fd import create_Mb_Tiny_RFB_fd, create_Mb_Tiny_RFB_fd_predictor

result_path = "./detect_imgs_results"
label_path = "./models/voc-model-labels.txt"
test_device = args.test_device

class_names = [name.strip() for name in open(label_path).readlines()]
if args.net_type == 'slim':
    model_path = "models/pretrained/version-slim-320.pth"
    # model_path = "models/pretrained/version-slim-640.pth"
    net = create_mb_tiny_fd(len(class_names), is_test=True, device=test_device)
    predictor = create_mb_tiny_fd_predictor(net, candidate_size=args.candidate_size, device=test_device)
elif args.net_type == 'RFB':
    model_path = "models/pretrained/version-RFB-320.pth"
    # model_path = "models/pretrained/version-RFB-640.pth"
    net = create_Mb_Tiny_RFB_fd(len(class_names), is_test=True, device=test_device)
    predictor = create_Mb_Tiny_RFB_fd_predictor(net, candidate_size=args.candidate_size, device=test_device)
else:
    print("The net type is wrong!")
    sys.exit(1)
net.load(model_path)

if not os.path.exists(result_path):
    os.makedirs(result_path)

paths = []

with open(args.txt_file) as f:
  print('Directories:')
  for line in f.readlines():
    l = line[:-1]
    print(l)
    paths.append(l)

print('\n')

for pth in paths:

  listdir = os.listdir(pth)
  sum = 0
  for file_path in listdir:
        img_path = os.path.join(pth, file_path)
        orig_image = cv2.imread(img_path)
        image = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB)
        boxes, labels, probs = predictor.predict(image, args.candidate_size / 2, args.threshold)
        sum += boxes.size(0)
        for i in range(boxes.size(0)):
            box = boxes[i, :]
            box = [int(x) for x in box]
            face_im = orig_image[box[1]:box[3],box[0]:box[2], :]
            s = face_im.shape
            if s[0]*s[1]*s[2] != 0:
              face_im = cv2.resize(face_im, (160, 160))
              fn, ext = file_path.split('.')[0], '.jpg'
              cv2.imwrite(result_path + '/' + fn + '_' + str(i) + ext, face_im)
            #cv2.rectangle(orig_image, (box[0], box[1]), (box[2], box[3]), (0, 0, 255), 2)
            # label = f"""{voc_dataset.class_names[labels[i]]}: {probs[i]:.2f}"""
            #label = f"{probs[i]:.2f}"
            # cv2.putText(orig_image, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
        #cv2.putText(orig_image, str(boxes.size(0)), (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        #cv2.imwrite(os.path.join(result_path, file_path), orig_image)
        print(f"Found {len(probs)} faces. Currently in {pth}")
  print(sum)
