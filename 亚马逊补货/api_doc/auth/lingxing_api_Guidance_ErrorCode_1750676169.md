# 领星API文档 - Guidance/ErrorCode

获取时间: 2025-06-23 18:56:09
文档路径: Guidance/ErrorCode
源URL: https://apidoc.lingxing.com/#/docs/Guidance/ErrorCode
分类: guidance
访问密钥: YESofbbaoY

---

## 全局错误码说明

|  错误码| 说明 | 处理 |
|-------|--------------------------|-----------|-------------|
|2001001| app not exist|appId不存在，检查值有效性|
|2001002| app secret not correct|appSecret不正确，检查值有效性|
|2001003| access token is missing or expire|token不存在或者已经过期，可刷新token重试|
|2001004| the api not authorized, please grant first|请求的api未授权，联系领星相关工作人员确认|
|2001005| access token not match |access_token 不正确，检查值有效性|
|2001006| api sign not correct|接口签名不正确，校验生成签名正确性【[接口签名生成测试](/docs/TestSign/signature)】，检查请求发起时是否有对sign进行urlencode转码处理|
|2001007| api sign has expired |签名已经过期，可重新发起请求，注意检查请求的时间戳是否在有效期内生成|
|2001008| refresh token expired. please get access token again|refresh_token过期，请重新获取|
|2001009| refresh token is invalid|refresh_token值无效，检查值有效性或重新获取|
|3001001| missing query param(access_token,sign,timestamp,app_key)|access_token、sign、timestamp、app_key为必传参数，检查请求参数是否缺失或拼接在url后格式是否正确|
|3001002| ip not permit, please add ip to white list first.|ip未加入白名单，确认发起ip地址后在ERP内自行增加即可|
|3001008| requests too frequently. please request later.|接口请求太频繁触发限流，适当下调接口请求频率|


