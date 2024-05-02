## 2. zeno-image-server
이미지 서버 Node.js v18.18.2
***모튼 TCP통신은 http만 지원합니다.(https미지원)***
***https미지원, MQTT Broker도 http만 지원***
#### 서버실행
```
npm install
npm start
```
#### config.json
```json
{
    "version": "1.0", #설정파일 버젼, 상위버젼 발견시 자동 다운로드
    "config_url": "http://192.168.0.100:3000/config.json", # 설정파일 URL
    "image_url": "http://192.168.0.100:3000", 
           # base url로 image_url/node_{기기아이디} 폴더에서 다운로드 됩니다.
    "mqtt_url": "xxxx.iptime.org", # http 제외한 MQTT Broker 주소
    "mqtt_user": "xxxx",            # 로그인 아이디
    "mqtt_passwd": "xxxx",        # 패스워드
    "mqtt_port": 1883,                # 포트
    "mqtt_keepalive": 120             # Ping 주기, keepalive
}
```
- 

#### node_{DEVICE ID}/images.json
- public 폴더안에 이미지 파일, `node_{기기아이디}` 형식.
- 각 폴더안에 이미지 정보관련 [`images.json`](./public/node_0/images.json).
```json
{
    "version": "1.4", # 이미지 정보 버전
    "images": [
        {
            "url": "logo.png", # 이미지 파일명, config.json 파일내 image_url을 기준으로 함.
            "x": 0, # x좌표
            "y": 0, # y좌표
            "z": 0, # z좌표, 레이어 순서 높을수록 상위 레이어
            "state": "" # 상태값, [""|on|off|boot|retain], boot: 부팅시 표시 이미지
        },
        {
            "url": "logo.png",
            "x": 0,
            "y": 0,
            "z": 0,
            "state": "boot" # 기기 부팅시 표시 이미지
        }
        {
            "url": "name.png",
            "x": 0,
            "y": 200,
            "z": 1,
            "state": "retain" # retain 이미지(상시유지) 
        },
        {
            "url": "in.png",
            "x": 0,
            "y": 50,
            "z": 2,
            "state": "on"
        },
        {
            "url": "out.png",
            "x": 0,
            "y": 200,
            "z": 9,
            "state": "off"
        }, 
    ]
}
```
