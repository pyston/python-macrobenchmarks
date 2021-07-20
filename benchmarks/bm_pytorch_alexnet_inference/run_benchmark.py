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

URL = "https://github.com/pytorch/hub/raw/master/images/dog.jpg"
FILENAME = os.path.join(DATADIR, "dog.jpg")


def bench_pytorch(loops=1000):
    #start = time.time()
    model = torch.hub.load('pytorch/vision:v0.6.0', 'alexnet', pretrained=True)
    # assert time.time() - start < 3, "looks like we just did the first-time download, run this benchmark again to get a clean run"
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

    loops = iter(range(loops))

    with torch.no_grad():
        t0 = pyperf.perf_counter()
        for _ in loops:
            output = model(input_batch)
        return pyperf.perf_counter() - t0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of pytorch"
    runner.bench_time_func("pytorch", bench_pytorch)
