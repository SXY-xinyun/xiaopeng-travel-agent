# Qoder鐮佸姏鏄熸湡鍥浡峰皬楣?AI 鍑鸿Agent

鍙繍琛屻€佸彲浣撻獙鐨?**AI 鍑鸿鏈嶅姟缂栨帓 Agent**锛氳鐩栥€岃溅涓昏嚜椹俱€嶄笌銆孯obotaxi 涔樺鏈嶅姟銆嶏紝寮鸿皟鍦烘櫙鐞嗚В銆佸伐鍏风紪鎺掗棴鐜€佸畨鍏ㄨ竟鐣屼笌鍙В閲婅緭鍑恒€?

杩愯鏃堕粯璁わ細**闃块噷浜戠櫨鐐煎崈闂杞紪鎺?+ 瑙勫垯瀹夊叏鎶ゆ爮**锛涙棤 Key 鑷姩闄嶇骇瑙勫垯寮曟搸銆?

## 蹇€熷惎鍔紙鏈湴锛?

```powershell
cd xiaopeng-travel-agent
copy .env.example .env
# 缂栬緫 .env锛屽～鍏?DASHSCOPE_API_KEY=sk-xxx
.\run.ps1
```

鎵撳紑 http://127.0.0.1:8000  
鐐瑰嚮椤堕儴 **銆岃嚜鍔ㄦ紨绀?4 鍦烘櫙銆?* 鍗冲彲缁欒瘎濮旀紨绀恒€?

## 鍏綉浣撻獙锛圙itHub 鈫?Render锛?

1. 浠ｇ爜鎺ㄩ€佸埌 GitHub锛堟湰浠撳簱锛? 
2. 鎸?[deploy/render.md](deploy/render.md) 鐢?Render 杩炰粨搴撻儴缃? 
3. 鍦?Render 鐜鍙橀噺濉叆 `DASHSCOPE_API_KEY`  
4. 寰楀埌鍏綉閾炬帴锛屼緥濡?`https://xxx.onrender.com`

闃块噷浜戣交閲忔柟妗堣锛歔deploy/aliyun-lightweight.md](deploy/aliyun-lightweight.md)  
Docker 鏈湴锛歚docker compose up -d --build`

## 鑳藉姏瀵圭収璧涢

| 璧涢瑕佹眰 | 鏈」鐩綋鐜?|
|---|---|
| 鍦烘櫙鐞嗚В | 璇嗗埆鈥滄斁姝屸啋鐤插姵鈥濃€滆窇杩囧幓鈫掔┛琛岄闄┾€濈瓑鐪熷疄鎰忓浘 |
| 鏈嶅姟缂栨帓 | 澶氳疆锛氳鍒掆啋鎵ц鈫掔粨鏋滃洖鐏屸啋鏀舵暃锛涘伐鍏峰舰鎴愰棴鐜?|
| 瀹夊叏杈圭晫 | 鐤插姵绂佸ū涔愪富绛栫暐銆佺榧撳姳妯┛銆佸効绔ュ己鍒堕攣闂ㄣ€佹眰鍔╁己鍒惰浆浜哄伐 |
| 缁撴灉杈撳嚭 | 鍥炲 + 鏈嶅姟璁″垝 + 宸ュ叿鐞嗙敱 + 绂佹鍔ㄤ綔 + 瀹夊叏鎻愮ず + 鐘舵€佸姣?|
| 鍙綋楠?Demo | 搴ц埍 HUD銆佽瘎濮斿墽鏈€佸叕缃?Docker 閮ㄧ讲 |

## 鎻愪氦鏉愭枡绱㈠紩

| 鏉愭枡 | 璺緞 |
|---|---|
| **鎻愪氦瀵圭収娓呭崟锛堝厛鐪嬭繖涓級** | [docs/鎻愪氦娓呭崟.md](docs/鎻愪氦娓呭崟.md) |
| 璁哄潧姝ｆ枃锛堝鍒剁矘璐达級 | [docs/forum_post.md](docs/forum_post.md) |
| STAR 浠嬬粛 | [docs/STAR_final.md](docs/STAR_final.md) |
| 鎶€鏈柟妗堟姤鍛?| [docs/tech_report.md](docs/tech_report.md) 路 鎵撳嵃椤?[docs/tech_report_print.html](docs/tech_report_print.html) |
| 杩愯鏁堟灉锛? 鍦烘櫙锛?| [docs/demo_results.md](docs/demo_results.md) |
| Demo 瑙嗛鑴氭湰 | [docs/demo_script.md](docs/demo_script.md) |
| Qoder 璇佹槑娓呭崟 | [docs/qoder_checklist.md](docs/qoder_checklist.md) |
| 鍏綉閮ㄧ讲 | [deploy/aliyun-lightweight.md](deploy/aliyun-lightweight.md) |
| 鎵撳寘鍛戒护 | `.\pack_submission.ps1` 鈫?`submission/` |

璁哄潧鏍囬蹇呴』浠?**銆孮oder鐮佸姏鏄熸湡鍥浡峰皬楣?AI 鍑鸿Agent銆?* 寮€澶淬€?

## 椤圭洰缁撴瀯

```
xiaopeng-travel-agent/
鈹溾攢鈹€ backend/app/
鈹?  鈹溾攢鈹€ main.py
鈹?  鈹溾攢鈹€ agent/          # 澶氳疆缂栨帓銆佸畨鍏ㄦ姢鏍忋€佸満鏅€丩LM
鈹?  鈹溾攢鈹€ tools/          # 妯℃嫙宸ュ叿绠?
鈹?  鈹斺攢鈹€ models/
鈹溾攢鈹€ frontend/public/    # 搴ц埍 Demo
鈹溾攢鈹€ deploy/
鈹溾攢鈹€ docs/
鈹溾攢鈹€ tests/
鈹溾攢鈹€ Dockerfile
鈹溾攢鈹€ docker-compose.yml
鈹斺攢鈹€ run.ps1
```

## API

- `GET /api/health` 鈥?鍚?`llm_configured` / `planner_default`
- `GET /api/scenarios`
- `POST /api/chat`

## 娴嬭瘯

```powershell
.\.venv\Scripts\python tests\test_scenarios.py
```
