import numpy as np
import torch
import os

from torch.utils.data.dataset import Dataset
from torch.utils.data import DataLoader
from torchvision import transforms

from PIL import Image
from os import path
from glob import glob

from config import *

dirs = glob(IMAGES_PATH + "/*/")

num_classes = {}

i = 0
for d in dirs:
    d = d.replace(IMAGES_PATH, "")
    d = d.replace("/", "")
    if " " in d:
        d = d.replace(" ", "_")
    num_classes[d] = i
    i+=1

# read mean and dev. standard pre-computed
m = 0
s = 0
if os.path.isfile('./mean_devstd.txt'):
    m_s = open("mean_devstd.txt", "r").read()
    if "," in m_s:
        m_s = m_s.replace("\n", "")
        m_s = m_s.split(",")
        m = m_s[0]
        s = m_s[1]

def get_class(idx):
    for key in num_classes:
        if idx == num_classes[key]:
            return key

def preprocessing():
    train_csv = ""
    test_csv  = ""
    class_files_training = []
    class_files_testing  = []

    for key in num_classes:
        if " " in key:
            os.rename(IMAGES_PATH+"/"+key, IMAGES_PATH+"/"+key.replace(" ", "_"))
            key = key.replace(" ", "_")

        class_files = glob(IMAGES_PATH+"/"+str(key)+"/*")
        class_files = [w.replace(IMAGES_PATH+"/"+str(key)+"/", "") for w in class_files]
        class_files.sort()

        class_files_training = class_files[: int(len(class_files)*.66)] # get 66% class images fo training
        class_files_testing = class_files[int(len(class_files)*.66)+1 :] # get 33% class images fo training

        for f in class_files_training:
            if "," in f or "#" in f or " " in f:
                tmp_f = f.replace(",", "")
                tmp_f = tmp_f.replace("#", "")
                tmp_f = tmp_f.replace(" ", "_")
                os.rename(IMAGES_PATH+"/"+key+"/"+f, IMAGES_PATH+"/"+key+"/"+tmp_f)
                f = tmp_f
            train_csv += f + ","+str(key)+"\n"

        for f in class_files_testing:
            if "," in f or "#" in f or " " in f:
                tmp_f = f.replace(",", "")
                tmp_f = tmp_f.replace("#", "")
                tmp_f = tmp_f.replace(" ", "_")
                os.rename(IMAGES_PATH+"/"+key+"/"+f, IMAGES_PATH+"/"+key+"/"+tmp_f)
                f = tmp_f
            test_csv += f + ","+str(key)+"\n"

    train_csv_file = open("train_file.csv", "w+")
    train_csv_file.write(train_csv)
    train_csv_file.close()

    test_csv_file = open("test_file.csv", "w+")
    test_csv_file.write(test_csv)
    test_csv_file.close()

    # Algorithms to calculate mean and standard_deviation
    dataset = LocalDataset(IMAGES_PATH, TRAINING_PATH, transform=transforms.ToTensor())
    # Mean
    m = torch.zeros(3)
    for sample in dataset:
        m += sample['image'].sum(1).sum(1)
    m /= len(dataset)*256*144

    # Standard Deviation
    s = torch.zeros(3)
    for sample in dataset:
        s+=((sample['image']-m.view(3,1,1))**2).sum(1).sum(1)
    s=torch.sqrt(s/(len(dataset)*256*144))

    print("Calculated mean and standard deviation")
    print(m)
    print(s)
    file = open("mean_devstd.txt", "w+")
    file.write(str(m)+","+str(s))
    file.close()
#preprocessing()


class LocalDataset(Dataset):

    def __init__(self, base_path, txt_list, transform=None):
        self.base_path=base_path
        self.images = np.genfromtxt(txt_list,delimiter=',',dtype='str')
        self.transform = transform

    def __getitem__(self, index):
        f,c = self.images[index]

        image_path = path.join(self.base_path + "/" + str(c), f)
        im = Image.open(image_path)

        if self.transform is not None:
            im = self.transform(im)

        label = num_classes[c]

        return { 'image' : im, 'label':label, 'img_name': f }

    def __len__(self):
        return len(self.images)
