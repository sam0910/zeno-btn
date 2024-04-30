# 제노글로벌

> - 주의사항
> POE 랜선과 디버깅용 USB 케이블 절대 같이 연결하시면 안됩니다.
> Olimex POE 보드 자체에 절연이 없어 쇼트 위험 있습니다.

## 보드 고유번호는 보드내 딥스위치로 설정 가능합니다.
> 1byte 개념으로 0~255까지 설정 가능합니다.
```
128  64  32  16  8  4  2  1
  0   0   0   0  0  0  0  0 = 8BIT

예시 : 1번스위치 아래로(ON) 내리면 1이 됩니다.
128  64  32  16  8  4  2  1
  0   0   0   0  0  0  0  1 = 1

예시 : 1,2번스위치 아래로(ON) 내리면 3이 됩니다.
128  64  32  16  8  4  2  1
  0   0   0   0  0  0  2  1 = 3

예시 : 아이디를 17번으로 설정 -> 5번,1번 스위치 내림
128  64  32  16  8  4  2  1
  0   0   0  16  0  0  0  1 = 17
```
<img src="https://github.com/sam0910/zeno-btn/assets/9714538/fdd0b4b4-2120-4eb1-8431-ad5ad76effe2" width="50%">


## 기타 나사 및 아크릴 자재 구매처
- 사용된 나사는 M3*5mm 일자나사입니다. [구매처 링크](http://www.nasakorea.com/goods/goods_view.php?goodsNo=3419)
- 아크릴은 테두리는 지름 5R로 주문시 요청사항에 `5R로 가공해주세요` 라고 적어주시면 됩니다.[아크릴 구매처 링크](https://www.acryiae.com/front/product/view.do?productSeq=1)
- 보드 디버깅, 펌웨어 업로드시 USB-UART 모듈(1개)이 필요합니다. 윈도우/리눅스/맥 사용환경에서 드라이버 지원되는지 확인후 구매 부탁드립니다. CP2102, FT232RL, PL2303HX, CH340G 등이 있습니다.

## 3D-Model
- 3D 모델링 파일 및 나사인서트 도면

## zeno-poe
- POE LAN 통신 Module

## zeno-image-server
- 이미지 서버 Node.js

## zeno-display
- 디스플레이 Module



