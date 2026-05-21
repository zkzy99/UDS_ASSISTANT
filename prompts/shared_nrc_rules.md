# UDS 服务器 NRC 决策通用规则

> 本文件为所有服务 prompt 共享，由 prompt_loader 自动拼接。ISO 14229-1 Figure 5/6 的精简摘要。

## 核心原则

**短路原则**：任一检查不通过立即返回对应 NRC，后续检查不再执行。

## 通用请求拦截（所有服务共用的前置检查，Figure 5）

按以下固定优先级顺序检查，任一步失败即返回 NRC：

| 优先级 | 检查项 | NRC | 说明 |
|--------|--------|-----|------|
| 1 | 服务器繁忙 | 0x21 | busyRepeatRequest，其他客户端占用 |
| 2 | 制造商特定故障 | 0xXX | 厂商自定义 |
| 3 | SID 不支持 | 0x11 | serviceNotSupported |
| 4 | 当前会话不支持 SID | 0x7F | serviceNotSupportedInActiveSession |
| 5 | SID 安全访问未通过 | 0x33 | securityAccessDenied |
| 6 | 供应商特定故障 | 0xXX | 供应商自定义 |

通过后分流：带子功能且非 0x31 → 子功能校验；否则 → 具体服务检查。

## 子功能级别校验（Figure 6，仅带子功能的服务适用）

| 优先级 | 检查项 | NRC | 说明 |
|--------|--------|-----|------|
| 1 | 最小长度（≥ SID+SubFunction） | 0x13 | incorrectMessageLengthOrInvalidFormat |
| 2 | 子功能不支持 | 0x12 | subFunctionNotSupported |
| 3 | 当前会话不支持该子功能 | 0x7E | subFunctionNotSupportedInActiveSession |
| 4 | 子功能安全访问未通过 | 0x33 | securityAccessDenied |
| 5 | 子功能请求序列错误 | 0x24 | requestSequenceError（仅 LinkControl/SecurityAccess） |

## NRC 编码速查

| NRC | 名称 | 适用层级 |
|-----|------|---------|
| 0x11 | serviceNotSupported | 通用 |
| 0x12 | subFunctionNotSupported | 子功能/服务 |
| 0x13 | incorrectMessageLengthOrInvalidFormat | 服务 |
| 0x14 | responseTooLong | 0x22 专有 |
| 0x21 | busyRepeatRequest | 通用 |
| 0x22 | conditionsNotCorrect | 服务 |
| 0x24 | requestSequenceError | 子功能/0x31 |
| 0x31 | requestOutOfRange | 服务 |
| 0x33 | securityAccessDenied | 通用/服务 |
| 0x70 | uploadDownloadNotAccepted | 0x34 专有 |
| 0x72 | generalProgrammingFailure | 0x2E/0x14 |
| 0x7E | subFunctionNotSupportedInActiveSession | 子功能 |
| 0x7F | serviceNotSupportedInActiveSession | 通用 |
