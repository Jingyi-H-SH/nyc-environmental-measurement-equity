"""Native dense-output backends. Inputs are RGB float tensors in [0,1]."""
from pathlib import Path
import json
import torch
from torch import nn
from torch.nn import functional as F

HOME = Path.home()
SEG = HOME/'work/jev-g6a/g6c/segformer'
IJEPA = HOME/'work/jev-g3lx-parallel/ijepa/model'
YOLO = HOME/'g6a-pilot/yolo26n-sem.pt'


def resize(x, shape):
    return F.interpolate(x, size=shape, mode='bilinear', align_corners=False)


class UNet(nn.Module):
    def __init__(self):
        super().__init__()
        from torchvision.models import resnet34
        enc = resnet34(weights=None)
        enc.load_state_dict(torch.load('resnet34.pth', map_location='cpu'))
        self.encoder = nn.ModuleList([nn.Sequential(enc.conv1, enc.bn1, enc.relu),
                                     nn.Sequential(enc.maxpool, enc.layer1),
                                     enc.layer2, enc.layer3, enc.layer4])
        self.decoder = nn.ModuleList()
        for inp, skip, out in [(512,256,128),(128,128,64),(64,64,32),(32,64,32)]:
            self.decoder.append(nn.Sequential(nn.Conv2d(inp+skip,out,3,padding=1),
                                              nn.BatchNorm2d(out),nn.ReLU(),
                                              nn.Conv2d(out,out,3,padding=1),nn.ReLU()))
        self.classifier = nn.Conv2d(32,8,1)

    def forward(self,x):
        skips=[]
        for level in self.encoder:
            x=level(x)
            skips.append(x)
        for block,skip in zip(self.decoder,reversed(skips[:-1])):
            x=block(torch.cat([resize(x,skip.shape[-2:]),skip],dim=1))
        return self.classifier(x)


class Dense(nn.Module):
    def __init__(self, family):
        super().__init__()
        self.family=family
        mean,std=[.485,.456,.406],[.229,.224,.225]
        if family=='cnn':
            self.model=UNet()
        elif family=='segformer':
            from transformers import SegformerForSemanticSegmentation
            self.model=SegformerForSemanticSegmentation.from_pretrained(SEG,local_files_only=True)
            head=self.model.decode_head
            head.classifier=nn.Conv2d(head.classifier.in_channels,8,1)
            self.model.config.num_labels=8
        elif family=='yolo':
            from ultralytics import YOLO as LoadYOLO
            source=LoadYOLO(str(YOLO)).model
            self.model=type(source)(cfg=source.yaml.copy(),nc=8,verbose=False)
            self.model.load(source,verbose=False)
            mean,std=[0]*3,[1]*3
        elif family=='ijepa':
            from transformers import IJepaModel
            self.model=IJepaModel.from_pretrained(IJEPA,local_files_only=True).requires_grad_(False)
            self.decoder=nn.Conv2d(1280,8,1)
        else:
            raise ValueError(family)
        if family in ('ijepa','segformer'):
            cfg=json.loads(((IJEPA if family=='ijepa' else SEG)/'preprocessor_config.json').read_text())
            mean,std=cfg['image_mean'],cfg['image_std']
        self.register_buffer('mean',torch.tensor(mean).view(1,3,1,1))
        self.register_buffer('std',torch.tensor(std).view(1,3,1,1))

    def encoder_parameters(self):
        if self.family=='cnn':return self.model.encoder.parameters()
        if self.family=='segformer':return self.model.segformer.parameters()
        if self.family=='yolo':return self.model.model[:-1].parameters()
        return []

    def forward(self,x):
        x=(x-self.mean)/self.std
        if self.family=='ijepa':
            self.model.eval()
            with torch.no_grad():
                x=self.model(resize(x,(224,224))).last_hidden_state
            assert x.shape[1:]==(256,1280)
            logits=self.decoder(x.transpose(1,2).reshape(-1,1280,16,16))
        elif self.family=='segformer':
            logits=self.model(x).logits
        else:
            logits=self.model(x)
            if isinstance(logits,tuple):logits=logits[0]
        assert logits.ndim==4 and logits.shape[1]==8
        return resize(logits,(512,512))
