import requests
import time
import os
import qrcode

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
    'Origin': 'https://www.bilibili.com',
    'Referer': 'https://www.bilibili.com'
}
tempVideoFile='temp\\video.m4s'
tempAudioFile='temp\\audio.m4s'
cookies=None

# example: infos=[['BV1HfK3zPEHE',0]]
infos=[['BV1HfK3zPEHE',0]]

#get qrcode
def getQRCode():
    respLogin=requests.get('https://passport.bilibili.com/x/passport-login/web/qrcode/generate',headers=headers)
    QRUrl=respLogin.json()['data']['url']
    QRKey=respLogin.json()['data']['qrcode_key']
    QRImg=qrcode.QRCode()
    QRImg.border=1
    QRImg.add_data(QRUrl)
    QRImg.print_ascii()
    return QRKey

#wait user to scan qrcode and get cookies
def login():
    QRKey=getQRCode()
    while True:
        respStatus=requests.get('https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key='+QRKey,headers=headers)
        respCode=int(respStatus.json()['data']['code'])
        if respCode==86038:
            QRKey=getQRCode()
            print('上一二维码已失效，请用新二维码扫码')
        elif respCode==86101:
            print('等待扫码')
        elif respCode==86090:
            print('已扫码，等待确认')
        elif respCode==0:
            print('登录成功')
            global cookies
            cookies=respStatus.cookies
            break
        time.sleep(1)

#get the cid of video by bvid
def getCid(bvid):
    respCid=requests.get('https://api.bilibili.com/x/player/pagelist?bvid='+bvid,headers=headers,cookies=cookies)
    plist=respCid.json()
    cid=str(plist['data'][0]['cid'])
    return cid

#get video&audio stream by cid
def getStream(bvid,cid,quality):
    respUrl=requests.get('https://api.bilibili.com/x/player/wbi/playurl?from_client=BROWSER&cid='+cid+'&qn=125&fourk=1&fnver=0&fnval=4048&bvid='+bvid,headers=headers,cookies=cookies)
    plist=respUrl.json()
    streamUrlVideo=str(plist['data']['dash']['video'][0]['baseUrl'])
    streamUrlAudio=str(plist['data']['dash']['audio'][0]['baseUrl'])
    return [streamUrlVideo,streamUrlAudio]

#download video&audio stream
def downloadStream(streamUrl,videoFile=tempVideoFile,audioFile=tempAudioFile): # 0:video 1:audio
    respVideo=requests.get(streamUrl[0],headers=headers,cookies=cookies)
    with open(videoFile,'wb') as f:
        f.write(respVideo.content)
    respAudio=requests.get(streamUrl[1],headers=headers,cookies=cookies)
    with open(audioFile,'wb') as f:
        f.write(respAudio.content)

#integrate video&audio stream
def integrateStream(outputFile,videoFile=tempVideoFile,audioFile=tempAudioFile):
    command=f'ffmpeg -i '+videoFile+' -i '+audioFile+' -c:v copy -c:a copy '+outputFile
    os.system(command)

#remove temp downloaded file
def removeTempFile():
    os.remove(tempVideoFile)
    os.remove(tempAudioFile)

login()

for info in infos:
    bvid=str(info[0])
    quality=str(info[1])
    cid=getCid(bvid)
    streamUrl=getStream(bvid,cid,quality)
    downloadStream(streamUrl)
    integrateStream('output\\'+bvid+'.mp4')
    removeTempFile()