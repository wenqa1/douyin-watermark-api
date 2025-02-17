from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiohttp
import re
import os

app = FastAPI()

# 定义 POST 请求的数据模型
class VideoRequest(BaseModel):
    url: str
    wxid: str

# 读取黑名单文件
def read_blacklist(filepath="hmd.txt"):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return [line.strip() for line in f.readlines()]

# 将 wxid 写入请求记录文件
def write_request_log(wxid, filepath="wxid.txt"):
    with open(filepath, 'a') as f:
        f.write(wxid + '\n')

# 验证 wxid 是否在黑名单中
def validate_wxid(wxid):
    blacklist = read_blacklist()
    if wxid in blacklist:
        raise HTTPException(status_code=403, detail="User is banned")

@app.post("/api/remove_watermark")
async def remove_watermark_post(request_data: VideoRequest):
    validate_wxid(request_data.wxid)
    write_request_log(request_data.wxid)
    return await process_video_url(request_data.url)

@app.get("/api/remove_watermark")
async def remove_watermark_get(request: Request):
    wxid = request.query_params.get("wxid")  # 假设 GET 请求也带有 wxid 参数
    if not wxid:
        raise HTTPException(status_code=400, detail="Missing 'wxid' parameter")
    validate_wxid(wxid)
    video_url = request.query_params.get("url")
    write_request_log(wxid)
    return await process_video_url(video_url)

async def process_video_url(video_url):
    # 模拟去水印逻辑
    if not video_url.startswith("https://v.douyin.com"):
        raise HTTPException(status_code=400, detail="Invalid video URL")
    
    # 解析抖音链接
    async with aiohttp.ClientSession() as session:
        async with session.get(video_url) as response:
            response_text = await response.text()
            if "video_id" in response_text:
                video_id = re.search(r'video/(.*?)\?', response_text).group(1)
                processed_url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}"
                return {"data": {"url": processed_url}}
            else:
                raise HTTPException(status_code=404, detail="Video not found")
