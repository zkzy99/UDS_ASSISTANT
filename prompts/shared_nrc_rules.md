# UDS 服务器 NRC 决策通用规则

> 本文件为所有服务 prompt 共享，由 prompt_loader 自动拼接。ISO 14229-1 Figure 5/6 的精简摘要。

## 核心原则

**短路原则**：任一检查不通过立即返回对应 NRC，后续检查不再执行。

## 通用请求拦截（Figure 5）

| 优先级 | 检查项 | NRC |
|--------|--------|-----|
| 1 | 服务器繁忙 | 0x21 |
| 2 | 制造商特定故障 | 0xXX |
| 3 | SID 不支持 | 0x11 |
| 4 | 当前会话不支持 SID | 0x7F |
| 5 | SID 安全访问未通过 | 0x33 |
| 6 | 供应商特定故障 | 0xXX |

通过后分流：带子功能且非 0x31 → 子功能校验；否则 → 具体服务检查。

## 子功能级别校验（Figure 6）

| 优先级 | 检查项 | NRC |
|--------|--------|-----|
| 1 | 最小长度（≥ SID+SubFunction） | 0x13 |
| 2 | 子功能不支持 | 0x12 |
| 3 | 当前会话不支持该子功能 | 0x7E |
| 4 | 子功能安全访问未通过 | 0x33 |
| 5 | 子功能请求序列错误 | 0x24 |

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

---

## SPRMIB 规则（带子功能的服务共用）

- 抑制位编码：`0x80 + 原子功能`（如 0x01 → 0x81）
- 正响应被抑制（No_Response），负响应仍正常返回
- NRC 0x78（Response Pending）不受 SPRMIB 影响

## 辅助服务协议

- 进入 Programming 会话前必须先执行 RoutineControl（`31 01 02 03`）
- `31 01 02 03` 正响应格式：`71 01 02 03 00`（5 字节，最后 1 字节为 routineStatus）

---

## 软件域规则（所有服务共用）

- APP 和 Boot 各独立生成完整用例集，用 `---` 分隔
- APP 使用 ApplicationServices 表，Boot 使用 BootServices 表
- Boot 域参数可能与 APP 完全不同，必须从 Boot 参数表精确读取
- Boot 域安全访问使用 Boot 的 Seed/Key（通常是 `27 11`/`27 12` 即 LevelFBL）

## 会话进入标准路径（所有服务共用）

| 目标会话 | 标准进入步骤 |
|---------|------------|
| Default（0x01） | `Send DiagBy[Physical]Data[10 01];` |
| Extended（0x03） | `Send DiagBy[Physical]Data[10 03];` |
| Programming（0x02） | `Send DiagBy[Physical]Data[10 01];` → `Delay[1000]ms;` → `Send DiagBy[Physical]Data[10 03];` → `Send DiagBy[Physical]Data[31 01 02 03];` → `Send DiagBy[Physical]Data[10 02];` |

注意：
- 会话切换之间**不使用 Delay**（Default → Programming 路径中的 Delay 除外）
- 从 Default 进入 Extended 直接 `10 03` 即可
- Boot 域进入路径：先进入 Programming Session 触发 Boot 模式，再切换到目标 Boot 会话
- 各服务若对会话路径有特殊要求，在服务 prompt 中覆盖此规则

---

## 输出格式规则（所有服务共用）

1. **输出格式严格为 pipe table**：`| Case ID | Case名称 | 测试步骤 | 预期输出 |`
2. **步骤中换行使用 `<br>` 标记**，不用 `\n`
3. **不要生成任何分析、推理、参数提取段落**，直接输出测试用例表格
4. **每条用例必须完整输出**，禁止 `...`、`略`、`同上` 等省略
5. **每个 `##` 分类下只输出一次表头**，不要中断后重新输出
6. **Case ID 不可重复**：物理寻址 `Diag_0x{SID}_Phy_001` 起递增，功能寻址 `Diag_0x{SID}_Fun_001` 起递增
7. **Functional 编号连续接续 Physical**（不从 001 重启）
8. **每个 Send 都要有对应 Check**，Delay 和带 `AndCheckResp` 的发送豁免
9. **顶级标题 `#`**，分类标题 `##`，各大组之间 `---` 分隔
10. **无符合条件的用例时** 使用 `> 无符合条件的用例。`
11. **正响应 SID = ServiceID + 0x40**，负响应格式 = `7F <SID> <NRC>`（UDS 标准，无需重复说明）
