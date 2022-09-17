import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse

from io import BytesIO
from rio_tiler.io import COGReader
from PIL import Image
import numpy as np

apps = FastAPI()


@apps.get("/")
async def root():
    return {"message": "Hello World"}


@apps.get("/tile")
async def tile(x: int = None, y: int = None, z: int = None):
    with COGReader("./data/TCI.tif") as image:
        x = x or 2427
        y = y or 1853
        z = z or 12

        # 判断瓦片是否存在
        if not image.tile_exists(x, y, z):
            raise HTTPException(
                status_code=404,
                detail=f"Tile does not exist.",
            )
            return None
        img = image.tile(x, y, z)

        # Numpy 的image数组转变为图片数组
        rgbArray = np.zeros((256, 256, 3), 'uint8')
        rgbArray[..., 0] = img.data[0]
        rgbArray[..., 1] = img.data[1]
        rgbArray[..., 2] = img.data[2]
        imgg = Image.fromarray(rgbArray, 'RGB')
        # imgg = imgg.convert('RGBA')

        # 黑边转为透明
        transImg = imgg.convert("RGBA")
        datas = transImg.getdata()
        newData = list()
        for item in datas:
            if item[0] < 1 and item[1] < 1 and item[2] < 1:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
        transImg.putdata(newData)

        # 数组转字节
        filtered_image = BytesIO()
        transImg.save(filtered_image, "PNG")
        filtered_image.seek(0)

        # 返回图片
        return StreamingResponse(filtered_image, media_type="image/png")
        # imgg.save('./data/py.png', format='png')
        # return FileResponse('./data/py.png', media_type="image/jpeg")


if __name__ == '__main__':
    uvicorn.run(app='fast_main:apps', host="0.0.0.0",
                port=8000, reload=True, debug=True)
