# 如何抓包获取前海供电配置字段

这份教程用于获取 Home Assistant 集成需要填写的 `open_id`、`settle_acct_no`、`user_no`、`pay_type`、`token` 和 `jsessionid`。请只抓取你自己的前海供电账号请求，不要把抓包文件、截图或字段原文发到公开仓库。

## 需要准备

- 一台 Mac，和手机连接到同一个 Wi-Fi。
- 一台 iPhone，已登录微信并能正常打开前海供电账单页面。
- 一个 HTTPS 抓包工具，推荐任选其一：
  - Proxyman
  - Charles
  - mitmproxy

下面以 Proxyman/Charles 这类图形工具为例。其他抓包工具的字段位置相同，核心都是查看请求地址、请求头、Cookie 和 JSON 请求体。

## 第一步：开启 Mac 抓包代理

1. 在 Mac 上打开抓包工具。
2. 找到代理监听地址和端口，通常是：
   - Mac IP：例如 `192.168.1.20`
   - 代理端口：Proxyman 常见为 `9090`，Charles 常见为 `8888`
3. 确认抓包工具已经开启 HTTP/HTTPS proxy。
4. 在抓包工具里开启 HTTPS 解密功能：
   - Proxyman：`Certificate` / `SSL Proxying`
   - Charles：`Proxy` / `SSL Proxying Settings`

如果不启用 HTTPS 解密，你通常只能看到域名和连接，不能看到请求头和 JSON 请求体。

## 第二步：给 iPhone 设置 Wi-Fi 代理

1. iPhone 打开 `设置 -> Wi-Fi`。
2. 点当前 Wi-Fi 右侧的详情按钮。
3. 滚动到 `HTTP 代理`。
4. 选择 `手动`。
5. 填入：
   - 服务器：Mac 的局域网 IP，例如 `192.168.1.20`
   - 端口：抓包工具显示的代理端口，例如 `9090` 或 `8888`
6. 点保存。

设置完成后，iPhone 的网页流量会经过 Mac 抓包工具。

## 第三步：安装并信任抓包证书

1. 按抓包工具提示，在 iPhone Safari 打开证书安装地址。常见形式类似：
   - `http://proxy.man/ssl`
   - `http://chls.pro/ssl`
2. 下载描述文件。
3. 打开 `设置`，安装刚下载的描述文件。
4. 安装后继续打开：
   `设置 -> 通用 -> 关于本机 -> 证书信任设置`
5. 找到抓包工具的根证书，打开完全信任。

如果这一步没做完，抓包工具会看到 HTTPS 连接失败，或者看不到解密后的请求内容。

## 第四步：在抓包工具里只关注前海供电请求

在抓包工具的搜索或过滤框里输入：

```text
qhp.qianhaipower.com
```

重点找这个请求：

```text
POST https://qhp.qianhaipower.com/wechatWeb/wx/serviceInvoke
```

这个集成目前会复用前海供电微信网页的同一类接口。你需要从该请求里取配置字段。

## 第五步：在微信里触发账单请求

1. 保持 iPhone Wi-Fi 代理开启。
2. 打开微信。
3. 进入你平时查看前海供电账单的页面。
4. 进入电费账单、欠费查询、缴费记录或类似页面。
5. 如果页面已经打开，先返回上一页再重新进入，或者下拉刷新。
6. 回到 Mac 抓包工具，查看是否出现 `serviceInvoke` 请求。

建议优先选择请求头里有以下内容的请求：

```text
hyServiceName: rcvblList
```

如果看到多个 `serviceInvoke` 请求，可以逐个点开看请求头 `hyServiceName`：

- `rcvblList`：账单列表，最适合提取配置字段。
- `queryArrearageDetail`：账单详情，也可用于确认字段。
- `queryRcvblHistoryl`：历史用电。

## 第六步：读取请求头和 Cookie

点开 `POST /wechatWeb/wx/serviceInvoke` 请求，查看 `Request Headers`。

需要记录：

| 集成字段 | 抓包位置 | 说明 |
| --- | --- | --- |
| `open_id` | 请求头 `bindingNo` | 通常也等于 Cookie 里的 `openId` |
| `token` | 请求头 `token` | 如果为空，集成里也留空 |
| `pay_type` | 请求体里的 `payType` 解码后 | 常见值是 `05` |

再查看该请求的 Cookie，需要记录：

| 集成字段 | 抓包位置 | 说明 |
| --- | --- | --- |
| `open_id` | Cookie `openId` | 如果和 `bindingNo` 一致，填同一个值 |
| `jsessionid` | Cookie `JSESSIONID` | 有就填；没有或为空可以先留空 |

`open_id` / `bindingNo` 是敏感会话标识，不要截图公开，不要提交到 Git。

## 第七步：读取请求体

继续查看同一个请求的 `Request Body` / `Body` / `Payload`。

你要找的是 JSON 请求体里的这些字段：

```json
{
  "payType": "MDU=",
  "settleAcctNo": "...",
  "userNo": "...",
  "amtYmFrom": "202501",
  "amtYmTo": "202506",
  "pageNo": "1",
  "pageNum": "10"
}
```

有些抓包工具会把 JSON 展开显示，有些会显示一整段文本。只要能看到字段名即可。

需要记录：

| 集成字段 | 抓包字段 | 是否需要解码 | 说明 |
| --- | --- | --- | --- |
| `settle_acct_no` | `settleAcctNo` | 需要 Base64 解码 | 必填 |
| `user_no` | `userNo` | 需要 Base64 解码 | 可选，但建议填 |
| `pay_type` | `payType` | 需要 Base64 解码 | 默认通常是 `05` |

不要把 `amtYmFrom`、`amtYmTo` 当成配置项；集成会按 `months` 自动生成查询月份范围。

## 第八步：Base64 解码字段

抓包里的 `settleAcctNo`、`userNo`、`payType` 通常是 Base64 编码，需要先解码成明文再填到 Home Assistant。

### 方法 A：用 Mac 终端解码

把 `<抓到的值>` 换成实际值：

```bash
printf '%s' '<抓到的值>' | base64 --decode
```

例子：

```bash
printf '%s' 'MDU=' | base64 --decode
```

输出：

```text
05
```

### 方法 B：用浏览器控制台解码

在浏览器开发者工具 Console 里执行：

```js
atob("MDU=")
```

输出：

```text
05
```

如果解码出来有中文乱码，可以在 Mac 终端里用 `base64 --decode`，通常更稳。

## 第九步：填写 Home Assistant 集成

在 Home Assistant 里进入：

```text
设置 -> 设备与服务 -> 添加集成 -> 前海供电
```

按下面对应关系填写：

| Home Assistant 字段 | 填写内容 |
| --- | --- |
| `base_url` | 保持默认 `https://qhp.qianhaipower.com` |
| `open_id` | 请求头 `bindingNo`，或 Cookie `openId` |
| `settle_acct_no` | `settleAcctNo` Base64 解码后的明文 |
| `user_no` | `userNo` Base64 解码后的明文，可选 |
| `pay_type` | `payType` Base64 解码后的明文，通常是 `05` |
| `token` | 请求头 `token`，为空就留空 |
| `jsessionid` | Cookie `JSESSIONID`，没有就留空 |
| `months` | 查询最近几个月账单，默认 `7` |

添加后，集成会立即查询一次账单。如果字段有效，你会看到设备和传感器实体。

## 常见问题

### 抓不到 `qhp.qianhaipower.com`

- 确认 iPhone 和 Mac 在同一个 Wi-Fi。
- 确认 iPhone Wi-Fi 代理的服务器 IP 是 Mac 当前局域网 IP。
- 确认代理端口和抓包工具显示一致。
- 确认没有开 iCloud Private Relay、VPN 或其他会绕过代理的网络工具。
- 在微信里重新进入账单页面，不要只停留在已经缓存好的页面。

### 能看到域名，但看不到请求体

- 说明 HTTPS 解密没有成功。
- 重新安装抓包证书。
- 检查 `证书信任设置` 是否已完全信任抓包工具根证书。
- 检查抓包工具是否对 `qhp.qianhaipower.com` 开启 SSL Proxying。

### 找不到 `settleAcctNo`

- 优先找 `hyServiceName: rcvblList` 的请求。
- 如果当前页面只打开了账单详情，返回账单列表后重新进入。
- 在抓包工具里搜索 `settleAcctNo` 或 `payType`。

### 添加集成后提示请求失败

- 重新确认 `open_id` 是否取自 `bindingNo` 或 Cookie `openId`。
- 确认 `settle_acct_no`、`user_no`、`pay_type` 填的是 Base64 解码后的明文，不是抓包里的编码值。
- 如果填了 `JSESSIONID` 后失败，可以尝试清空 `jsessionid` 后重新添加。
- 如果 `openId` 已过期，需要重新打开微信账单页面并重新抓包。

## 脱敏检查

如果需要提交 issue，请先脱敏。不要公开以下内容：

- `bindingNo`
- `openId`
- `JSESSIONID`
- `token`
- `settleAcctNo` 原文或解码值
- `userNo` 原文或解码值
- 用户名、手机号、住址、户号

可以保留字段名和响应结构，例如：

```json
{
  "payType": "<redacted>",
  "settleAcctNo": "<redacted>",
  "userNo": "<redacted>"
}
```
