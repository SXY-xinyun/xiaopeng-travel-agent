# 魔搭部署（用户名已填：xxkingxxking）

## 完成后的体验链接（创空间建好并上线后）

https://modelscope.cn/studios/xxkingxxking/xiaopeng-travel-agent

---

## 第 1 步：你先在网页建创空间（必须）

1. 登录 https://www.modelscope.cn/ （账号 `xxkingxxking`）
2. 打开 https://www.modelscope.cn/studios → **新建创空间**
   - 名称：`xiaopeng-travel-agent`
   - 公开
   - 选 **Docker**（没有就先建空的，再靠 `ms_deploy.json`）
   - 资源：免费 **CPU 2核16G**
3. 打开 https://www.modelscope.cn/my/myaccesstoken → 新建 **Git 访问令牌**，复制下来

把 **Token** 发给我（或自己跑下面命令）。

---

## 第 2 步：推送代码（有 Token 后）

在 PowerShell：

```powershell
cd C:\Users\xingx\Desktop\8.2\xiaopeng-travel-agent
$token = "粘贴你的魔搭Token"
git remote remove ms 2>$null
git remote add ms "https://oauth2:$token@www.modelscope.cn/studios/xxkingxxking/xiaopeng-travel-agent.git"
git push ms HEAD:master
# 若报错再试：
# git push ms HEAD:main
```

然后到创空间点 **上线/重启**，等变成运行中。

---

## 交卷时写

- 体验入口：https://modelscope.cn/studios/xxkingxxking/xiaopeng-travel-agent  
- GitHub：https://github.com/SXY-xinyun/xiaopeng-travel-agent  
