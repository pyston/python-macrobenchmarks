import json
import time
import torch
import urllib
import sys

if __name__ == "__main__":
    start = time.time()
    model = torch.hub.load('pytorch/vision:v0.6.0', 'alexnet', pretrained=True)
    # assert time.time() - start < 3, "looks like we just did the first-time download, run this benchmark again to get a clean run"
    model.eval()

    url, filename = ("https://github.com/pytorch/hub/raw/master/images/dog.jpg", "dog.jpg")
    urllib.request.urlretrieve(url, filename)

    from PIL import Image
    from torchvision import transforms
    input_image = Image.open(filename)
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0) # create a mini-batch as expected by the model

    n = 1000
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    with torch.no_grad():
        times = []
        for i in range(n):
            times.append(time.time())
            if i % 10 == 0:
                print(i)
            output = model(input_batch)
        times.append(time.time())
    print((len(times) - 1) / (times[-1] - times[0]) , "/s")

    if len(sys.argv) > 2:
        json.dump(times, open(sys.argv[2], 'w'))
