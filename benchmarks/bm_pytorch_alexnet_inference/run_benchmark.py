import os
import os.path
import sys
import urllib.request

import pyperf
from PIL import Image
import torch
from torchvision import transforms


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
if not os.path.exists(DATADIR):
    os.mkdir(DATADIR)

# TODO: Vendor this file (and the pytorch hub model) into the data dir,
# to avoid network access and to pin the data for consistent results.
URL = "https://github.com/pytorch/hub/raw/master/images/dog.jpg"
FILENAME = os.path.join(DATADIR, "dog.jpg")


#############################
# benchmarks

def bench_pytorch(loops=1000):
    """Measure using pytorch to transform an image N times.

    This involves the following steps:

    * load a pre-trained model (alexnet)
    * mark it for evaluation
    * download an image
    * prepare it to be run through the model
    * turn off gradients computation
    * run the image through the model

    Only that last step is measured (and repeated N times).
    """
    model = torch.hub.load('pytorch/vision:v0.6.0', 'alexnet', pretrained=True)
    model.eval()

    urllib.request.urlretrieve(URL, FILENAME)
    input_image = Image.open(FILENAME)
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0) # create a mini-batch as expected by the model

    with torch.no_grad():
        elapsed = 0
        for _ in range(loops):
            t0 = pyperf.perf_counter()
            output = model(input_batch)
            elapsed += pyperf.perf_counter() - t0
        return elapsed


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of pytorch"
    runner.bench_time_func("pytorch", bench_pytorch)
