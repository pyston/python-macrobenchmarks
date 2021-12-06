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
    elapsed, _ = _bench_pytorch(loops)
    return elapsed


def _bench_pytorch(loops=1000, *, legacy=False):
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
    start = pyperf.perf_counter()
    model = torch.hub.load('pytorch/vision:v0.6.0', 'alexnet', pretrained=True)
    # assert pyperf.perf_counter() - start < 3, "looks like we just did the first-time download, run this benchmark again to get a clean run"
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
    input_batch = input_tensor.unsqueeze(0)  # create a mini-batch as expected by the model

    with torch.no_grad():
        elapsed = 0
        times = []
        for i in range(loops):
            if legacy and (i % 10 == 0):
                print(i)
            # This is a macro benchmark for a Python implementation
            # so "elapsed" covers more than just how long model() takes.
            t0 = pyperf.perf_counter()
            output = model(input_batch)
            t1 = pyperf.perf_counter()

            elapsed += t1 - t0
            times.append(t0)
        times.append(pyperf.perf_counter())
        return elapsed, times


#############################
# the script

if __name__ == "__main__":
    from legacyutils import maybe_handle_legacy
    maybe_handle_legacy(_bench_pytorch, legacyarg='legacy')

    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of pytorch"
    runner.bench_time_func("pytorch", bench_pytorch)
