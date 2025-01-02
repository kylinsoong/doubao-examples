import time
import os
import requests
import re
from volcenginesdkarkruntime import Ark

base_url = 'https://openspeech.bytedance.com/api/v1/vc'
appid = os.getenv("X_API_APPID")
access_token = os.getenv("X_API_TOKEN")
API_KEY = os.environ.get("ARK_API_KEY")
API_EP_ID = os.environ.get("ARK_API_ENGPOINT_ID")


# 视频字幕出现不连续判断阈值
threshold_ms = 8000

language = 'zh-CN'
file_url = 'https://tos-cfitc.tos-cn-beijing.volces.com/sample_vedio.mp4'

client = Ark(api_key=API_KEY)

def log_time(func):
    """Decorator to log execution time of a function."""
    def wrapper(*args, **kwargs):
        begin_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function '{func.__name__}' executed in {end_time - begin_time:.2f} seconds")
        return result
    return wrapper

@log_time
def ac_vedio_caption():
    response = requests.post(
                 '{base_url}/submit'.format(base_url=base_url),
                 params=dict(
                     appid=appid,
                     language=language,
                     use_itn='True',
                     use_capitalize='True',
                     max_lines=1,
                     words_per_line=15,
                 ),
                 json={
                    'url': file_url,
                 },
                 headers={
                    'content-type': 'application/json',
                    'Authorization': 'Bearer; {}'.format(access_token)
                 }
             )
    print('submit response = {}'.format(response.text))
    assert(response.status_code == 200)
    assert(response.json()['message'] == 'Success')

    job_id = response.json()['id']
    response = requests.get(
            '{base_url}/query'.format(base_url=base_url),
            params=dict(
                appid=appid,
                id=job_id,
            ),
            headers={
               'Authorization': 'Bearer; {}'.format(access_token)
            }
    )
    assert(response.status_code == 200)
    utterances = response.json()['utterances']
    return utterances

@log_time
def analysis_utterances(utterances):
    interruptions = []
    for i in range(len(utterances) - 1):
        current_end = utterances[i]["end_time"]
        next_start = utterances[i + 1]["start_time"]

        gap = next_start - current_end
        if gap > threshold_ms:
            interruptions.append({
                "gap_duration": gap,
                "gap_start": current_end,
                "gap_end": next_start
            })
    if len(interruptions):
        print("字幕检测显示视频不连续(可通过 threshold_ms 设定不连续判断阈值，默认超过8秒不说话则认为视频不连续):")
        for i, interrupt in enumerate(interruptions, 1):
            print(
                f"    中断 {i}: 从 {interrupt['gap_start']} 毫秒 到 {interrupt['gap_end']} 毫秒，"
                f"出现 {interrupt['gap_duration']} 毫秒的间隔"
            )
    else:
        print("视频字幕检查该双录视频是连续的")      

@log_time
def vedio_to_images():
    base_url = "https://tos-cfitc.tos-cn-beijing.volces.com/sample_video/frame_{:06d}.jpg"
    frame_urls = [base_url.format(i * 60) for i in range(100)]
    wrapper_list = [frame_urls[i:i + 10] for i in range(0, 100, 10)]

    results = []
    for lst in enumerate(wrapper_list):
        frames = lst[1]
        results.append(frames)

    for item in results:
        for img in item:
            print("    ", img)
        time.sleep(2)
    return results

def extract_frame_id(url):
    match = re.search(r'frame_(\d+)\.jpg', url)

    if match:
        frame_number = match.group(1)
        return frame_number
    else:
        print("Frame number not found in the URL.")

def print_srage(stage):
    print('-' * 89)
    print(stage)
    print('-' * 89)

def ark_vision_images(item):
    completion = client.chat.completions.create(
        model=API_EP_ID,
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "分析图片，如果有超过2 张图片中没人、或为单一背景色，或为黑屏，则回复1，反之回复0"},
                    {
                        "type": "image_url",
                        "image_url": {"url":  item[0]}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url":  item[1]}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url":  item[2]}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url":  item[3]}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url":  item[4]}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url":  item[5]}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url":  item[6]}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url":  item[7]}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url":  item[8]}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url":  item[9]}
                    },
                ],
            }
        ],
        temperature=0.01
    )
    return completion.choices[0].message.content

@log_time
def main():
    print_srage(" 豆包大模型视频字幕分析阶段...")
    utterances = ac_vedio_caption()
    analysis_utterances(utterances)
    print()

    print_srage(" 视频按每 60 帧切片...")
    frames = vedio_to_images()
    print()
    print_srage(" 豆包大模型视频分析阶段...")
    for item in frames:
        print("    分析帧", extract_frame_id(item[0]), "到", extract_frame_id(item[1]))
        tag = ark_vision_images(item)
        if "1" in tag:
            print("        帧", extract_frame_id(item[0]), "到", extract_frame_id(item[1]),"出现双录视频未录或黑屏现象")
        else:
            print("        正常")


if __name__ == '__main__':
    main()
