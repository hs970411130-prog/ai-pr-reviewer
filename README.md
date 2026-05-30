# AI PR Review 鍔╂墜

鑷姩鍒嗘瀽 GitHub Pull Request 鐨?AI 浠ｇ爜璇勫宸ュ叿銆傛寚瀹?PR URL锛屼竴閿幏鍙栧彉鏇存憳瑕併€侀闄╄瘑鍒拰 Review 寤鸿銆?
## 蹇€熷紑濮?
```bash
# 1. 鍏嬮殕骞跺畨瑁?git clone https://github.com/hs970411130-prog/ai-pr-reviewer.git
cd ai-pr-reviewer
pip install -e .

# 2. 閰嶇疆 API Key锛堝鍒?.env.example 涓?.env 骞跺～鍏ワ級
cp .env.example .env
# 缂栬緫 .env 濉叆 DEEPSEEK_API_KEY 鍜?GITHUB_TOKEN

# 3. 杩愯 CLI 鍒嗘瀽
python -m src.cli https://github.com/owner/repo/pull/42

# 4. 鎴栧惎鍔?Web UI
streamlit run app.py
```

## 鍔熻兘

- **PR 鍙樻洿鎬荤粨** 鈥?3-5 鍙ヤ腑鏂囨憳瑕侊紝姒傝堪鏈 PR 鐨勭洰鐨勫拰鏀瑰姩鑼冨洿
- **椋庨櫓浠ｇ爜璇嗗埆** 鈥?妫€娴嬪畨鍏ㄦ紡娲炪€佺┖鎸囬拡銆佸苟鍙戦棶棰樸€佽祫婧愭硠婕忕瓑锛屾瘡鏉″甫缃俊搴﹁瘎鍒?- **Review 寤鸿鐢熸垚** 鈥?閽堝浠ｇ爜鍙鎬с€佹€ц兘銆佹渶浣冲疄璺垫彁鍑哄叿浣撴敼杩涘缓璁?- **涓婁笅鏂囧寮?* 鈥?鍏宠仈 Issue 寮曠敤銆乬it blame 淇℃伅銆佹枃妗ｅ彉鏇村垎鏋?- **璇姤鎺у埗** 鈥?姣忔潯鍙戠幇甯?1-5 缃俊搴﹁瘎鍒嗭紝鍘婚噸锛屼綆缃俊搴︽爣娉?寰呬汉宸ョ‘璁?
- **鍙屾牸寮忔姤鍛?* 鈥?鍚屾椂杈撳嚭 Markdown 鍜屼氦浜掑紡鍗曟枃浠?HTML锛堝崱鐗囧竷灞€銆佺疆淇″害绛涢€夈€佹墜椋庣惔鎶樺彔锛?- **Web UI** 鈥?Streamlit 鐣岄潰锛屾敮鎸佽繘搴︽潯銆佸巻鍙茶褰曘€佷竴閿鍑?
## 鐢ㄦ硶

### CLI 妯″紡

```bash
# 鍩烘湰鐢ㄦ硶
python -m src.cli https://github.com/owner/repo/pull/42

# 鎸囧畾杈撳嚭鐩綍
python -m src.cli https://github.com/owner/repo/pull/42 -o ./reports

# 閫氳繃 CLI 浼犲叆 GitHub Token
python -m src.cli https://github.com/owner/repo/pull/42 --github-token ghp_xxx
```

### Web UI 妯″紡

```bash
streamlit run app.py
# 娴忚鍣ㄨ闂?http://localhost:8501
# 渚ц竟鏍忚緭鍏?PR 鍦板潃 鈫?鐐瑰嚮鍒嗘瀽 鈫?鏌ョ湅杩涘害鏉″拰缁撴灉
```

## 椤圭洰缁撴瀯

```
ai-pr-reviewer/
鈹溾攢鈹€ app.py                 # Streamlit Web UI
鈹溾攢鈹€ .streamlit/            # Streamlit 閰嶇疆
鈹溾攢鈹€ src/
鈹?  鈹溾攢鈹€ cli.py             # CLI 鍏ュ彛
鈹?  鈹溾攢鈹€ pipeline.py        # 鍏ㄩ摼璺紪鎺?鈹?  鈹溾攢鈹€ models.py          # 鏁版嵁妯″瀷
鈹?  鈹溾攢鈹€ config/settings.py # 闆嗕腑閰嶇疆
鈹?  鈹溾攢鈹€ fetcher/           # GitHub API 鏁版嵁鑾峰彇
鈹?  鈹溾攢鈹€ parser/            # Diff 缁撴瀯鍖栬В鏋?鈹?  鈹溾攢鈹€ analyzer/          # 鍒嗘瀽寮曟搸 + 5 涓垎鏋愬櫒
鈹?  鈹溾攢鈹€ llm/               # LLM 瀹㈡埛绔?+ Prompt 妯℃澘
鈹?  鈹斺攢鈹€ reporter/          # 鎶ュ憡鐢熸垚 + 缃俊搴﹁瘎鍒?鈹溾攢鈹€ tests/                 # 鍗曞厓娴嬭瘯
鈹溾攢鈹€ reports/               # 鐢熸垚鐨勬姤鍛婏紙gitignore锛?鈹溾攢鈹€ PRODUCT.md             # 浜у搧璁捐鏂囨。
鈹斺攢鈹€ AGENTS.md              # 寮€鍙戣鑼?```

## 璁捐鎬濊矾

### 妯″瀷閫夋嫨

閫夌敤 **DeepSeek-V4锛坉eepseek-chat锛?*锛?
- **鎴愭湰浣?* 鈥?API 浠锋牸绾︿负 GPT-4o 鐨?1/10锛屽崟娆?PR 鍒嗘瀽浠呭嚑鍒嗛挶
- **涓枃濂?* 鈥?涓枃鐞嗚В鍜岀敓鎴愯川閲忎紭绉€锛孯eview 寤鸿琛ㄨ揪鑷劧
- **鍏煎鎬у己** 鈥?瀹屽叏鍏煎 OpenAI API 鍗忚锛岄€氳繃 `openai` SDK 璋冪敤锛孡LM 鎶借薄灞傦紙`llm/client.py`锛夊彧闇€淇敼 `LLM_API_BASE` 鍜?`LLM_MODEL` 閰嶇疆鍗冲彲鍒囨崲鍒板叾浠?OpenAI 鍏煎鏈嶅姟

### 涓婁笅鏂囪幏鍙栨柟寮?
绯荤粺閫氳繃浠ヤ笅閫斿緞鑾峰彇 PR diff 涔嬪鐨勪笂涓嬫枃锛?
1. **鍏宠仈 Issue** 鈥?浠?PR body 涓彁鍙?`#123` 鏍煎紡鐨?Issue 寮曠敤
2. **git blame** 鈥?閫氳繃 GitHub API 鏌ヨ鍙樻洿鏂囦欢鐨勪富瑕佺淮鎶よ€咃紝甯姪璇勫鑰呬簡瑙ｄ唬鐮佸綊灞?3. **鏂囨。鍙樻洿鎰熺煡** 鈥?璇嗗埆 `.md` 绛夋枃妗ｆ枃浠剁殑鍙樻洿锛岃緟鍔╃悊瑙?PR 鐨勪笟鍔¤儗鏅?
### 鏈潵鎵╁睍鏂瑰悜

鏋舵瀯璁捐鏀寔浠ヤ笅鏂瑰悜鐨勬墿灞曪細

- **澶氭ā鍨嬫敮鎸?* 鈥?`llm/client.py` 閫氳繃閰嶇疆鍒囨崲锛屽彲鎺ュ叆 OpenAI銆丆laude銆佽眴鍖呯瓑
- **澶氬钩鍙?* 鈥?`fetcher/base.py` 鎶借薄鎺ュ彛锛屾柊澧?`gitlab.py` / `gitee.py` 鍗冲彲鎵╁睍
- **澧為噺鍒嗘瀽** 鈥?Engine 鍒嗘壒绛栫暐宸叉敮鎸佹寜鏂囦欢璋冨害锛屽彲鎵╁睍涓哄閲?review锛堝彧鍒嗘瀽鏂板 commit锛?- **鑷畾涔夎鍒?* 鈥?Prompt 妯℃澘锛坄llm/prompts/`锛夌嫭绔嬩簬浠ｇ爜锛岃瘎瀹¤鍒欏彲鐏垫椿璋冩暣
- **CI 闆嗘垚** 鈥?Pipeline 璁捐涓烘棤鐘舵€佸嚱鏁帮紝鍙洿鎺ュ祵鍏?GitHub Actions / GitLab CI

## 鎶€鏈爤

| 缁勪欢 | 閫夊瀷 |
|------|------|
| 璇█ | Python 3.11+ |
| LLM | DeepSeek-V4 |
| LLM SDK | openai |
| HTTP | httpx |
| CLI | click |
| Web UI | Streamlit + 绾?HTML 鍗曟枃浠?|

## 杩愯娴嬭瘯

```bash
pip install pytest
pytest tests/ -v
```