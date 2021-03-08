import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
import torch.nn.functional as F
import numpy as np
from torchvision.models.segmentation import fcn_resnet50
from torchvision.models.segmentation.fcn import FCNHead
from torchvision.models.segmentation.deeplabv3 import DeepLabHead
import os
import sys
from PIL import Image

from segmentation.models import all_models

seg_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(seg_dir)
sys.path.append(root_dir)

from utils.file_utils import training_data_dir, training_image_feature_dir,testing_data_perception_dir,data_root_dir
from seg.datasets import FCNTrainingDataset, RGBTrainingDataset, RGBTestingDataset
from seg.seg_utils import class_weights
from benchmark_pose_and_detection.sem_seg_evaluator import Evaluator

model_name = "fcn8_resnet18"
device = torch.device('cuda:1')
batch_size = 4
n_classes = 82
num_epochs = 10
image_axis_minimum_size = 200
pretrained = True
fixed_feature = False

training_dataset = RGBTestingDataset(testing_data_perception_dir, image_axis_minimum_size)
training_loader = DataLoader(training_dataset, batch_size=batch_size, shuffle=False, num_workers=8)
### Model
net = all_models.model_from_name[model_name](n_classes, batch_size,
                                               pretrained=pretrained,
                                               fixed_feature=fixed_feature)
print(dir(net))
exit()
net.load_state_dict(torch.load(root_dir + '/saved_models/seg/fcn_epoch20_step1000.pth'))
net.eval()
net.to(device)
os.system('rm '+ data_root_dir + "/testing_pred_perception/*.png")
for step, (data, instance_ids) in tqdm(enumerate(training_loader)):
    data = data.to(device)
    preds = net(data)
    preds = F.interpolate(preds, size=[720,1280], mode='bilinear', align_corners=False)
    preds_label = preds.max(dim=1).indices
    preds_label = preds_label.cpu().numpy()
    for pred, instance_id in zip(preds_label, instance_ids):
        pred = pred.astype(np.uint8)
        im = Image.fromarray(pred)
        #im = im.resize(size=[1280,720], resample=Image.NEAREST)
        im.save(data_root_dir + "/testing_pred_perception/%s_label_kinect.png"%instance_id)