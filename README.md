# 前海供电接入 Home Assistant

![version](https://img.shields.io/badge/version-v0.4.4-blue)

这是基于微信前海供电网页接口实现的 Home Assistant 自定义集成。

> **第一次配置前请先看：** [如何抓包获取前海供电配置字段](docs/packet-capture.md)。教程里写了手机代理、HTTPS 证书、筛选请求、字段位置和 Base64 解码步骤。

当前已还原的调用链：

- 统一入口：`POST https://qhp.qianhaipower.com/wechatWeb/wx/serviceInvoke`
- 账单列表：`hyServiceName: rcvblList`
- 账单详情：`hyServiceName: queryArrearageDetail`
- 历史用电：`hyServiceName: queryRcvblHistoryl`

前端逻辑显示，请求体字段使用 Base64，`sign` 使用 SM2 加密，`hyRequestUrl` 使用 RSA 加密真实业务路径。本集成已经实现这些请求构造逻辑。

## 刷新策略

集成会在 Home Assistant 启动或重载时先获取一次账单数据，之后固定在每月 2 日 00:00 自动刷新一次。

前海供电账单通常按月生成，不做高频轮询。

## 安装

把目录复制到 HA 配置目录：

```text
/config/custom_components/qianhai_power
```

重启 Home Assistant 后，在 `设置 -> 设备与服务 -> 添加集成` 搜索 `前海供电`。

## 配置字段

从自己的前海供电微信网页请求里填这些字段：

详细抓包步骤见：[如何抓包获取前海供电配置字段](docs/packet-capture.md)。

- `open_id`：请求头 `bindingNo`，也是 Cookie 里的 `openId`。
- `settle_acct_no`：请求体 `settleAcctNo` 的明文值。抓包里是 Base64，需要先解码。
- `user_no`：请求体 `userNo` 的明文值，可选。
- `pay_type`：默认 `05`。
- `token`：抓包里为空就留空。
- `jsessionid`：可选。部分会话可能需要。
- `months`：查询最近几个月账单，默认 7。

Base64 示例：

```text
payType: MDU= -> 05
settleAcctNo: <你的 Base64 结算户号> -> <你的结算户号>
userNo: <你的 Base64 用户号> -> <你的用户号>
```

`openId/bindingNo` 属于敏感会话标识，不要提交到 Git。

## 当前实体

- `账单`：状态为账单月份，属性里包含完整账单详情和接口状态。
- `账单月份`
- `账单金额`
- `账单电量`
- `欠费`
- `锁定欠费`
- `合计电费`
- `欠费标记`
- `用户号`
- `客户号`
- `用户名`
- `用电地址`
- `用电类别`
- `账单类型`
- `电价名称`
- `用电性质`
- `上次抄表日期`
- `本次抄表日期`
- `计量点编号`
- `工单号`
- `应收账务流水`
- `电度电费`
- `基本电费`
- `附加费`
- `力调电费`
- `退补电费`
- `阶段性减免电费`
- `上期表码`
- `本期表码`
- `倍率`
- `表计资产编号`
- `示数类型`
- `阶梯一电量`
- `阶梯一名称`
- `阶梯一占比`
- `阶梯一电费`
- `阶梯一电价`
- `阶梯二电量`
- `阶梯二名称`
- `阶梯二占比`
- `阶梯二电费`
- `阶梯二电价`
- `阶梯三电量`
- `阶梯三名称`
- `阶梯三占比`
- `阶梯三电费`
- `阶梯三电价`

实体属性会附带用户号、用户名、地址等响应中可解析的信息。

## 接口说明

集成会先请求账单列表，再请求最新账单详情：

- `rcvblList`：账单列表。
- `queryArrearageDetail`：账单详情。

当前解析的详情字段包括：

- 基本信息：`mpNo`、`elecSort`、`price`、`amtYm`、`ltMrDate`、`readDate`
- 费用：`receAmt`、`pqAmt`、`baseAmt`、`plusAmt`、`pfAmt`、`totalRsAmt`、`reduce`
- 表码：`caReadInfos[].readType`、`ltMeterData`、`ttMeterNum`、`totalFactor`、`assetsNo`
- 阶梯：`stepInfos[].stepSort`、`percent`、`totalPq`、`totalAmt`、`prc`

不同账号如果返回字段略有差异，可以在 issue 中提供已脱敏的响应结构。

## 安全说明

- 不要把 `openId`、`JSESSIONID`、Token、户号、手机号、住址提交到仓库或 issue。
- 这个接口依赖微信网页会话，`openId` 是否长期有效取决于前海供电网页侧策略。
- 账单按月刷新，不要频繁请求前海供电服务端。
