# UDS 服务器 NRC 决策通用规则

> 本文件为所有服务 prompt 共享，由 prompt_loader 自动拼接。ISO 14229-1 Figure 5/6 的精简摘要。

---

## 服务存在性强制检查（所有服务共用，最高优先级）

> **在生成任何测试用例之前，必须先检查目标服务是否存在于输入的 Excel 数据中。如果服务不存在，必须输出空服务，绝对禁止凭空编造测试用例。**

### 检查方法

1. 在 `=== Sheet:` 文本中搜索目标服务的 Service ID（如 `0x2E`、`0x22`）
2. 检查是否有该服务对应的参数表：
   - `Diagnostic Services` 表格中是否有该 Service ID 的条目
   - 0x22/0x2E → 检查是否存在 DID 表（含 `DID`、`DID Name`、`Byte Length`、`Write Support` 等字段）
   - 0x14/0x19 → 检查是否存在 DTC 表
   - 0x31 → 检查是否存在 RID 表
   - 其他服务 → 检查 `Diagnostic Services` 表中是否有该 Service ID 的条目
3. 确认该服务的 `Support` 字段（若存在且为 `N` 或 `不支持`，则服务不可用）

### 服务不存在时的强制输出格式

**如果目标服务在输入 Excel 中不存在（无任何相关参数表或服务条目），必须输出以下空服务格式，不得生成任何测试用例：**

```
# Service 0xXX ServiceName — 测试用例

> 该服务在输入文件中不存在，无测试用例生成。

---
## 用例统计汇总

| 分类 | 物理寻址 | 功能寻址 | 小计 |
|------|---------|---------|------|
| **总计** | **0** | **0** | **0** |
```

### 禁止行为

- **绝对禁止**根据 UDS 协议知识自行编造 DID、DTC、RID、子功能、参数值等数据
- **绝对禁止**在服务不存在时仍然生成测试用例
- 所有测试数据必须严格来源于输入的 Excel 参数表，不得凭空编造

---

## 参数标识符数据源强制规则（所有服务共用）

> **所有测试用例中使用的标识符（DID、RID、DTC、子功能等）必须严格来自输入 Excel 中对应的参数表。禁止使用参数表中未声明的标识符发送请求并设置预期响应。**

### 各服务标识符数据源对照

| 服务 | 标识符类型 | 唯一合法数据源 |
|------|-----------|--------------|
| 0x22（ReadDataByIdentifier） | DID | **DID 表**（含 `DID`、`DID Name`、`Byte Length`、`Data Type`、`Default Value` 等字段） |
| 0x2E（WriteDataByIdentifier） | DID | **DID 表**（含 `DID`、`DID Name`、`Byte Length`、`Write Support`、`Default Value` 等字段） |
| 0x31（RoutineControl） | RID | **Routine Control 表** / **Control Routine 表**（含 `RID`、`RID Name`、支持的 `Subfunction`、`Access Level`、`Request/Response` 参数等字段） |
| 0x14/0x19（DTC 相关） | DTC | **DTC 表**（含 `DTC`、`DTC Name`、`DTC Status Mask` 等字段） |
| 0x10/0x11/0x27/0x28/0x3E/0x85 | 子功能 | **Diagnostic Services 表**（含 `Subfunction`、`Hex Value`、`Supported Session` 等字段） |

### 正向用例标识符使用规则

1. **正向用例只能使用参数表中 `Support = Y` 或明确支持的本域标识符**
2. 每个标识符必须从参数表精确读取其属性（Byte Length、Default Value、Access Level、支持的 Subfunction 等）
3. **App 域和 Boot 域的标识符列表可能完全不同**，必须分别从各自域的表中读取
4. 禁止跨表引用：如 0x2E 的 DID 不能从 Routine Control 表获取，0x31 的 RID 不能从 DID 表获取

### 负向用例标识符使用规则

1. **测试"不支持的标识符"（NRC 0x31）时**，使用明显非法的值：
   - 不支持的 DID：使用 `0xFFFF`（全局无效 DID）或 `0x0000`
   - 不支持的 RID：使用 `0xFFFF` 或 `0x0000`
   - 不支持的子功能：使用 `0xFF` 等明显非法的子功能码
2. **禁止使用参数表中未声明但看起来"像"合法值的标识符**——这会误导测试结果

### 禁止行为

- **绝对禁止**使用参数表中不存在的 DID/RID/DTC 发送正向请求并设置正响应预期
- **绝对禁止**从其他 Sheet 或其他服务的参数表交叉引用标识符
- **绝对禁止**根据标识符命名规律自行推测编造标识符
- 若参数表中某服务的标识符列表为空，则该服务的正向用例数必须为 0

---

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

## NRC 全覆盖强制规则（所有服务共用）

> **核心要求：参数表中 `Negative response codes` 字段列出的每一个 NRC，都必须有至少一条专用测试用例覆盖。不得遗漏任何一个已声明的 NRC。同时，参数表未声明的 NRC 绝对不得出现在任何测试用例的预期输出中。**

### 规则

1. **【强制】NRC 唯一合法来源**：每个服务的有效 NRC 列表必须**仅从**参数表 `Service` sheet 的 `Negative response codes` 字段精确读取。该字段中列出的 NRC 码（空格分隔，如 `11 7F 13 12 22 7E`）是该服务**唯一合法**的 NRC 集合。
2. **【强制】禁止使用未声明的 NRC**：**参数表中未列出的 NRC 码绝对不得**出现在任何测试用例的预期负响应（`7F <SID> <NRC>`）中。即使 prompt 模板或 NRC 优先级链示例中包含了某个 NRC，只要参数表未声明，就**必须排除**该 NRC。
3. **全量覆盖**：参数表声明的每一个 NRC 都必须有对应的测试用例（可以是正向触发该 NRC 的负向用例）。
4. **NRC 优先级链**：优先级链必须**严格只包含**参数表声明的 NRC（而非 prompt 中的示例链），按参数表排列顺序确定优先级。
5. **服务级 NRC 差异**：不同服务甚至同一服务的不同子功能（如 0x10 的 01/81 vs 02/82），其 `Negative response codes` 字段可能**不同**，必须分别读取。**不得将 A 子功能的 NRC 列表套用到 B 子功能。**
6. **空 NRC 字段处理**：若某服务/子功能的 `Negative response codes` 字段为空，则该服务只能有正响应，**绝对禁止**凭空编造负响应用例。

### NRC 反例规则（强制）

| 禁止行为 | 说明 |
|---------|------|
| 使用 prompt 模板中的 NRC | 每个 prompt 中的 NRC 优先级链仅为**参考模板**，实际 NRC 列表必须从参数表读取 |
| 跨服务复制 NRC | 不得将 0x22 服务的 NRC 列表用于 0x10 服务 |
| 跨子功能复制 NRC | 不得将 0x10 01 子功能的 NRC 列表用于 0x10 02 子功能 |
| 假设"常见 NRC"存在 | 不得因为某个 NRC（如 0x22、0x33）在其他 ECU 中常见就假设当前 ECU 也支持 |
| 预期未声明 NRC | 预期输出中的 `7F <SID> <NRC>` 中的 NRC 码必须逐一与参数表核对 |

### NRC 生成前强制自检

**每生成一条负响应用例之前，必须执行以下检查：**

```
对每条包含 7F <SID> <NRC> 的预期输出：
  ✓ NRC 码是否在参数表 Negative response codes 字段中？
  ✗ 若不在 → 立即删除该用例，不得输出
```

### 各 NRC 的标准触发条件

| NRC | 名称 | 标准触发方式 |
|-----|------|------------|
| 0x11 | serviceNotSupported | 发送不支持的 SID（不在参数表 Service 列表中的 SID）— 该 NRC 由 ECU 在服务不支持时返回，验证方式：向 ECU 发送一个全局不支持的诊断服务 SID，预期返回 `7F <unsupported_SID> 11`。对于被测服务自身，该 NRC 表示"ECU 不支持本服务"，通常在服务全局不支持时由 Session Layer 覆盖。 |
| 0x12 | subFunctionNotSupported | 发送不支持的子功能 |
| 0x13 | incorrectMessageLengthOrInvalidFormat | 发送长度错误请求（WithLen） |
| 0x14 | responseTooLong | 请求读取超长 DID 组合导致响应超限（0x22 专有） |
| 0x21 | busyRepeatRequest | 服务器繁忙（通常难以精确触发，若参数表未声明可跳过） |
| 0x22 | conditionsNotCorrect | 前提条件不满足（如车速不满足、电压异常、Programming 前置条件未满足等） |
| 0x24 | requestSequenceError | 安全访问流程错误（如 key→seed 逆序）、RID 请求序列错误（0x31） |
| 0x31 | requestOutOfRange | DID/RID 不支持、数据记录无效 |
| 0x33 | securityAccessDenied | 安全访问未解锁时请求需安全等级的服务/DID |
| 0x35 | invalidKey | 发送错误密钥（0x27 专有） |
| 0x36 | exceededNumberOfAttempts | 超过最大尝试次数（0x27 专有） |
| 0x37 | requiredTimeDelayNotExpired | 锁定延时未到期（0x27 专有） |
| 0x70 | uploadDownloadNotAccepted | 0x34/0x35 专有 |
| 0x72 | generalProgrammingFailure | 写入服务器内存失败（0x2E）、编程前置条件不满足（0x31） |
| 0x78 | responsePending | 请求已接收但处理未完成（通常 ECU 在处理耗时操作时返回） |
| 0x7E | subFunctionNotSupportedInActiveSession | 子功能在当前会话不支持 |
| 0x7F | serviceNotSupportedInActiveSession | 服务在当前会话不支持 |

### NRC 覆盖率自检清单

生成用例前必须逐项自检：
1. 从参数表 `Negative response codes` 字段提取完整 NRC 列表（每个子功能分别提取）
2. **过滤检查**：逐一检查每条负响应用例的 `7F <SID> <NRC>` 中的 NRC 码，**删除所有 NRC 码不在参数表声明列表中的用例**
3. 对比生成的测试用例，确认每个已声明 NRC 至少有一条用例覆盖
4. 对于仅靠"组合触发"（如 NRC Priority 测试）间接覆盖的 NRC，确认是否有独立的专用用例
5. 如某个 NRC 确实无法触发（如 0x21 busyRepeatRequest），需在输出中注明"参数表声明但无法触发"
6. **最终确认**：生成的预期负响应中不存在任何参数表未声明的 NRC 码

---

## SPRMIB 规则（带子功能的服务共用）

- 抑制位编码：`0x80 + 原子功能`（如 0x01 → 0x81）
- 正响应被抑制（No_Response），负响应仍正常返回
- NRC 0x78（Response Pending）不受 SPRMIB 影响

## 辅助服务协议

- **若参数表 Routine Control 表中存在 RID 0x0203（CheckProgrammingPreCondition）**，进入 Programming 会话前必须先执行 RoutineControl（`31 01 02 03`）
- `31 01 02 03` 正响应格式：`71 01 02 03 00`（5 字节，最后 1 字节为 routineStatus）
- **若参数表中不存在 RID 0x0203，则 Programming 进入路径不经过 `31 01 02 03` 步骤，直接使用 `10 02` 进入**
- **若参数表中不存在 RID 0xFF01（Boot 会话状态验证），Boot 域 S3 Timer 等测试不依赖该 RID**

---

## 软件域规则（所有服务共用）

- APP 和 Boot 各独立生成完整用例集，用 `---` 分隔
- APP 使用 ApplicationServices 表，Boot 使用 BootServices 表
- Boot 域参数可能与 APP 完全不同，必须从 Boot 参数表精确读取
- Boot 域安全访问使用 Boot 的 Seed/Key（通常是 `27 11`/`27 12` 即 LevelFBL）

---

## Session 正响应时序参数编码规则（所有服务共用）

> **重要**：Session 正响应 `50 <Sub>` 的后 4 字节为 P2/P2* 时序参数，**必须从参数表读取并用实际值填充，绝对禁止使用 `XX XX XX XX` 占位**。

- `P2Server Max`（ms 值）→ hex 编码：`P2ms / 1` → 转为 2 字节大端 hex
- `P2*Server Max`（ms 值）→ hex 编码：`P2*ms / 10` → 转为 2 字节大端 hex
- Session 正响应完整格式：`50 <Sub> <P2_H> <P2_L> <P2*_H> <P2*_L>`

**编码示例：**
- P2=50ms → 50 = 0x0032 → `00 32`
- P2*=2000ms → 2000/10 = 200 = 0x00C8 → `00 C8`
- P2*=5000ms → 5000/10 = 500 = 0x01F4 → `01 F4`

**在 Check 中的使用（仅当对应会话被参数表声明支持时才可使用）：**
- Default Session：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- Extended Session：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`（**仅在参数表声明 Extended 时使用**）
- Programming Session：`Check DiagData[50 02 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`（**仅在参数表声明 Programming 时使用**）

---

## 会话支持性强制验证规则（所有服务共用）

> **生成任何测试用例前，必须先验证目标会话是否在参数表中声明为支持。绝对禁止使用参数表中未声明的会话。**

### 会话数据源

每个服务的**可用会话列表**必须从参数表 `Service` Sheet 中该服务的 `Session reference`（或 `Supported Session`）字段精确读取。

- `Session reference` 字段格式示例：`01 02`（空格分隔的会话 ID 列表）
- 每个会话 ID 的含义：`01`=Default, `02`=Programming, `03`=Extended
- **只有在 `Session reference` 中列出的会话才可用于该服务的测试用例**

### 会话使用规则

1. **正向用例**：只能在参数表声明的会话下生成。如 PBL 域仅声明 `01 02`，则所有正向用例只能在 Default 和 Programming 会话下执行，**绝对禁止**使用 Extended (0x03) 会话
2. **负向用例（会话不支持）**：只能使用参数表声明的"不支持的会话"。如某服务声明支持 `01 02` 但不支持 `03`，则测试 NRC 0x7F 时可用 `10 03` 触发
3. **会话切换**：`10 01`（Default）、`10 02`（Programming）、`10 03`（Extended）只有在对应会话被参数表声明时才可使用
4. **正响应验证**：`50 01`（Default）、`50 02`（Programming）、`50 03`（Extended）只有在对应会话声明支持时才可预期
5. **Programming Session 进入路径**：必须先验证 `31 01 02 03`（RID 0x0203 - CheckProgrammingPreCondition）是否存在于 Routine Control 表中。若不存在，则 Programming 进入路径仅使用 `10 02`，不经过 `10 03` 和 `31 01 02 03` 中间步骤

### 禁止行为

- **绝对禁止**在参数表未声明 Extended Session 时，在测试步骤中发送 `10 03` 或预期 `50 03`
- **绝对禁止**在参数表未声明 Programming Session 时，在测试步骤中发送 `10 02` 或预期 `50 02`
- **绝对禁止**假设所有 ECU 都支持三个会话（Default/Programming/Extended）

---

## 会话进入标准路径（所有服务共用）

> **以下为标准参考路径，实际生成时必须先验证目标会话是否在参数表中声明（见上方"会话支持性强制验证规则"）。未声明的会话即使在下表中列出也不得使用。**

| 目标会话 | 标准进入步骤 | 前置条件 |
|---------|------------|---------|
| Default（0x01） | `Send DiagBy[Physical]Data[10 01];` | 无 |
| Extended（0x03） | `Send DiagBy[Physical]Data[10 03];` | **仅当参数表声明 Extended Session 时使用** |
| Programming（0x02） | 路径A（标准，有 0x0203 RID）：`Send DiagBy[Physical]Data[10 01];` → `Delay[1000]ms;` → `Send DiagBy[Physical]Data[10 03];` → `Send DiagBy[Physical]Data[31 01 02 03];` → `Send DiagBy[Physical]Data[10 02];` | **仅当参数表声明 Extended + 0x0203 RID 存在时使用** |
| Programming（0x02） | 路径B（简化，无 0x0203 RID）：`Send DiagBy[Physical]Data[10 01];` → `Send DiagBy[Physical]Data[10 02];` | **当参数表未声明 Extended 或无 0x0203 RID 时使用** |

注意：
- 会话切换之间**不使用 Delay**（Programming 路径A 中的 Delay 除外）
- Boot 域进入路径：先进入 Programming Session 触发 Boot 模式，再切换到目标 Boot 会话
- 各服务若对会话路径有特殊要求，在服务 prompt 中覆盖此规则
- **PBL/SBL 域通常仅支持 Default (01) 和 Programming (02)，不包含 Extended (03)**

---

## 输出格式规则（所有服务共用）

1. **输出格式严格为 pipe table**：`| Case ID | Case名称 | 测试步骤 | 预期输出 |`
2. **步骤中换行使用 `<br>` 标记**，不用 `\n`
3. **步骤编号严格使用 `N. ` 格式**（如 `1. Send...`、`2. Check...`），**绝对禁止使用 `StepN:` 或 `stepN:` 格式**
4. **不要生成任何分析、推理、参数提取段落**，直接输出测试用例表格
5. **每条用例必须完整输出**，禁止 `...`、`略`、`同上` 等省略
6. **每个 `##` 分类下只输出一次表头**，不要中断后重新输出
7. **Case ID 不可重复**：物理寻址 `Diag_0x{SID}_Phy_001` 起递增，功能寻址 `Diag_0x{SID}_Fun_001` 起递增
8. **Functional 编号连续接续 Physical**（不从 001 重启）
9. **每个 Send 都要有对应 Check**，Delay、Set/Stop/Resume 等非诊断操作步骤不写 Check 且**不在预期输出中列出**（**禁止使用 `--` 占位**），带 `AndCheckResp` 的发送豁免
10. **顶级标题 `#`**，分类标题 `##`，各大组之间 `---` 分隔
11. **无符合条件的用例时** 使用 `> 无符合条件的用例。`
12. **正响应 SID = ServiceID + 0x40**，负响应格式 = `7F <SID> <NRC>`（UDS 标准，无需重复说明）
