# Service 0x14 ClearDiagnosticInformation — 用例生成规则

## 服务概述

- **Service ID**: 0x14
- **Service Name**: ClearDiagnosticInformation
- **正响应 SID**: 0x54（0x14 + 0x40）
- **负响应格式**: `7F 14 <NRC>`
- **请求格式**: `14 FF FF FF`（清除所有 DTC 组）
- **合法 SF_DL**: 4 字节（SID + 3 字节 groupOfDTC）
- **关键特性**: 清除 DTC 后需用 0x19 验证清除效果；清除前需先确认有 DTC 可清
- **Functional 寻址特殊规则**: 0x14 服务在 Functional 寻址下**抑制正响应**，所有正向 Functional 用例预期输出均为 `No_Response`
- **NRC 优先级链（服务级，Figure 0x14 专用）**:

| 优先级 | NRC | 触发条件 |
|--------|-----|---------|
| 1 | 0x13 | 长度错误（SF_DL≠4） |
| 2 | 0x31 | groupOfDTC 不支持 |
| 3 | 0x22 | 前提条件不满足 |
| 4 | 0xXX | 厂商/供应商自定义 |
| 5 | 0x72 | 清除操作写入内存失败 |

### 正响应格式

- `54`（无额外 payload，仅 SID 确认，仅 Physical 寻址可见）

### 典型 NRC

| NRC  | 含义 | 触发条件 |
|------|------|---------|
| 0x11 | Service Not Supported | ECU（App 域或 Boot 域）不支持 0x14 服务 |
| 0x13 | Incorrect Message Length Or Invalid Format | 报文长度错误（SF_DL ≠ 4） |
| 0x22 | Conditions Not Correct | 前置条件不满足 |
| 0x31 | Request Out Of Range | groupOfDTC 值不支持 |
| 0x7F | Service Not Supported In Active Session | 当前会话下不支持 0x14 服务 |

---

## 服务支持性判断规则（首要规则，生成前必须读取）

> **在生成任何用例之前，必须先从参数表 `Supported Services` sheet 的 `Support` 列判断 0x14 服务是否支持。**

| 参数表 `Support` 列标注 | 含义 | 用例预期 |
|------------------------|------|---------|
| `M`（Mandatory，强制支持） | ECU **支持** 0x14 服务 | 正向请求预期 `Check DiagData[54]Within[50]ms;` |
| `Y`（Yes，明确支持） | ECU **支持** 0x14 服务 | 正向请求预期 `Check DiagData[54]Within[50]ms;` |
| `S`（Optional/Selectable，**可选但本项目未选用**） | ECU **不支持** 0x14 服务 | 所有请求均预期 `Check DiagData[7F 14 11]Within[50]ms;`（NRC 0x11） |
| `O`（Optional，可选，未实现） | ECU **不支持** 0x14 服务 | 所有请求均预期 `Check DiagData[7F 14 11]Within[50]ms;`（NRC 0x11） |
| `N`（No，明确不支持） | ECU **不支持** 0x14 服务 | 所有请求均预期 `Check DiagData[7F 14 11]Within[50]ms;`（NRC 0x11） |
| 空 / 子功能为 `/` | ECU **不支持** 0x14 服务 | 所有请求均预期 `Check DiagData[7F 14 11]Within[50]ms;`（NRC 0x11） |

> **重要**：`S`（Optional）表示该服务在规范中可选，**不代表本 ECU 实现了该服务**。只有明确标注 `M` 或 `Y` 才视为支持；`S`/`O`/`N`/空值 一律视为不支持，预期 NRC 0x11。

**当 0x14 不支持时的生成规则：**
- App Physical / Boot Physical：所有用例预期为 `Check DiagData[7F 14 11]Within[50]ms;`
- App Functional / Boot Functional：所有用例预期为 `Check No_Response Within[1000]ms;`（Functional 寻址下 NRC 0x11 被抑制）
- 分类结构仍按"整体结构要求"生成，但内容仅保留 Session Layer Test，其余分类标注"无符合条件的用例"

---

## 整体结构要求

按以下固定顺序生成 4 组用例，每组使用 `#` 顶级标题（如 `# 1. Application Service_Physical Addressing`），组间用 `---` 分隔：

1. **Application Service_Physical Addressing** — 分类 1-5
2. **Application Service_Functional Addressing** — 分类 1-5 的 Functional 版本
3. **Boot Service_Physical Addressing** — Session Layer Test（不支持，返回 NRC 0x11）
4. **Boot Service_Functional Addressing** — Session Layer Test（不支持，返回 No_Response）

### 输出格式要求

1. **顶级标题使用 `#`**：如 `# 1. Application Service_Physical Addressing`、`# 2. Application Service_Functional Addressing`、`# 3. Boot Service_Physical Addressing`、`# 4. Boot Service_Functional Addressing`
2. **分类标题使用 `##`**：如 `## 1.1 Session Layer Test`、`## 1.2 Secure Access Test`、`## 1.3 Clear DTC Function Test` 等
3. **各大组之间用 `---` 分隔**
4. **无符合条件的用例时使用 `>` 引用**：如 `> App 域无符合条件的用例。`
5. **输出格式严格为 pipe table**，列顺序：`| Case ID | Case名称 | 测试步骤 | 预期输出 |`
6. **步骤中换行使用 `<br>` 标记**，不用 `\n`
7. **不要生成任何"参数提取结果"或"分析"段落**，直接输出测试用例表格

---

## 生成分类（共 5 类）

按以下固定顺序逐类生成，每个分类使用 `## N.N` 作为标题（如 `## 1.1 Session Layer Test`）。

---

### 分类 1: Session Layer Test

#### 用例数量规则

**当 0x14 服务支持（Support = M 或 Y）时：**
- `Npos` = 支持的会话正向 case 数（每个支持 0x14 的会话 1 条）
- `Nneg_sess` = 不支持的会话负向 case 数（每个不支持 0x14 的会话 1 条）
- **总数 = Npos + Nneg_sess**

**当 0x14 服务不支持（Support = S / O / N / 空，或子功能为 `/`）时：**
- 每个可达会话各生成 1 条，预期均为 NRC 0x11
- **总数 = 可达会话数**

#### 用例命名规则

**0x14 支持（M/Y）时：**
- 正向：`<CurrentSessionName> Session support 0x14 services`
  - 示例：`Default Session support 0x14 services`
- 负向（会话不支持）：`<CurrentSessionName> Session nonsupport 0x14 services`
  - 示例：`Programming Session nonsupport 0x14 services`

**0x14 不支持（S/O/N/空）时：**
- 所有会话均为负向：`<CurrentSessionName> Session nonsupport 0x14 services`
  - 示例：`Default Session nonsupport 0x14 services`

#### 测试步骤模板

**A. 当前会话支持 0x14 服务（正向，仅 Support = M 或 Y 时生成）**
```
1. 进入 <CurrentSessionSupport>
2. Send DiagBy[Physical]Data[14 FF FF FF];
```

**B. 当前会话不支持 0x14 服务（会话级负向）**
```
1. 进入 <CurrentSessionNotSupport>
2. Send DiagBy[Physical]Data[14 FF FF FF];
```

**C. ECU 整体不支持 0x14 服务（Support = S/O/N/空，所有会话均适用）**
```
1. 进入 <CurrentSession>
2. Send DiagBy[Physical]Data[14 FF FF FF];
```

#### Check 规则

**A. 支持会话正向（Support = M 或 Y）：**
- `Check DiagData[54]Within[50]ms;`

**B. 当前会话不支持服务（会话级）：**
- `Check DiagData[7F 14 7F]Within[50]ms;`

**C. ECU 整体不支持 0x14（Support = S/O/N/空）：**
- Physical 寻址：`Check DiagData[7F 14 11]Within[50]ms;`
- Functional 寻址：`Check No_Response Within[1000]ms;`

#### 特殊规则

1. Session Layer Test 仅验证会话是否支持 0x14 服务，不涉及故障制造和清除验证
2. 故障制造和清除验证在分类 3 (Clear DTC Test) 中进行
3. **当 Support = S/O/N/空 时，分类 2-5 均标注"无符合条件的用例"，不生成实质内容**

---

### 分类 2: Secure Access Test

#### 用例数量规则

**当 0x14 服务支持（Support = M 或 Y）时：**
- **必须生成**，即使 0x14 在 Level0 即可执行
- 从参数表读取所有安全等级，为每个安全等级生成 1 条用例
- **总数 = 安全等级数量**（至少 1 条）

**当 0x14 服务不支持（Support = S/O/N/空）时：**
- 标注"无符合条件的用例"，不生成实质内容

#### 用例命名规则

`Security access Lx unlock supports 0x14 services`
- 示例：`Security access L2 unlock supports 0x14 services`

#### 测试步骤模板

```
1. 进入允许安全访问的会话（通常 Extended）
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
3. Send Security Right KeyBy[Physical]Level[<KeySub>];
4. Send DiagBy[Physical]Data[14 FF FF FF];
```

#### Check 规则

- 第 2 步：验证 Seed 响应
- 第 3 步：`Check DiagData[67 <KeySub>]Within[50]ms;`
- 第 4 步：`Check DiagData[54]Within[50]ms;`

#### 特殊规则

1. **无论 Level0 是否支持，都必须生成本类用例**，因为需要验证安全解锁后服务仍正常可用
2. 安全等级不写死，必须从参数表所在软件域的 Access Level 读取
3. SeedSub/KeySub 对应关系：L1 → 27 01/27 02，L2 → 27 03/27 04，L3 → 27 05/27 06，L4 → 27 07/27 08，L5 → 27 09/27 0A

---

### 分类 3: Clear DTC Function Test

#### 用例数量规则

**当 0x14 服务支持（Support = M 或 Y）时：**
固定 5 条，覆盖以下场景：

| 序号 | 场景 | 描述 |
|------|------|------|
| 1 | 无 DTC 时清除 | 验证正响应但无实际效果 |
| 2 | 清除单个 DTC（状态 09） | testFailed + confirmedDTC |
| 3 | 清除多个 DTC（状态 09） | 制造多个故障后一次清除 |
| 4 | 清除单个 DTC（状态 08） | 仅 confirmedDTC |
| 5 | 清除多个 DTC（状态 08） | 多个故障的 08 状态 |

**当 0x14 服务不支持（Support = S/O/N/空）时：**
- 标注"无符合条件的用例"，不生成实质内容

#### 用例命名规则

1. `Failure is not recorded supports 0x14 Service`
2. `0x14 service cleared 1 fault with status "09"`
3. `0x14 service cleared multiple fault with status "09"`
4. `0x14 service cleared 1 fault with status "08"`
5. `0x14 service cleared multiple fault with status "08"`

#### 测试步骤模板

**场景 1: 无 DTC 时清除**
```
1. 进入支持的会话（Extended）
2. Send DiagBy[Physical]Data[19 02 FF];
3. Send DiagBy[Physical]Data[14 FF FF FF];
4. Send DiagBy[Physical]Data[19 02 FF];
```

**场景 2: 清除单个 DTC（状态 09）**
```
1. 进入支持的会话（Extended）
2. <触发故障>（例如 Set Voltage[16.3]V; Delay[2000]ms;）
3. Send DiagBy[Physical]Data[19 02 FF];
4. Send DiagBy[Physical]Data[14 FF FF FF];
5. Send DiagBy[Physical]Data[19 02 FF];
6. <恢复>（例如 Set Voltage[13.5]V; Delay[2000]ms;）
```

**场景 3: 清除多个 DTC（状态 09）**
```
1. 进入支持的会话（Extended）
2. Delay[1000]ms;
3. Send DiagBy[Physical]Data[19 02 FF];
4. Send DiagBy[Physical]Data[14 FF FF FF];
5. Send DiagBy[Physical]Data[19 02 FF];
```

**场景 4: 清除单个 DTC（状态 08）**
```
1. 进入支持的会话（Extended）
2. <触发故障>（例如 Set Voltage[16.5]V; Delay[2000]ms;）
3. <恢复条件但 DTC 仍为 08>（例如 Set Voltage[13.5]V; Delay[2000]ms;）
4. Send DiagBy[Physical]Data[19 02 FF];
5. Send DiagBy[Physical]Data[14 FF FF FF];
6. Send DiagBy[Physical]Data[19 02 FF];
```

**场景 5: 清除多个 DTC（状态 08）**
```
1. 进入支持的会话（Extended）
2. Delay[1000]ms;
3. Send DiagBy[Physical]Data[19 02 FF];
4. Send DiagBy[Physical]Data[14 FF FF FF];
5. Send DiagBy[Physical]Data[19 02 FF];
```

#### Check 规则

- 清除成功（Physical）：`Check DiagData[54]Within[50]ms;`
- DTC 存在验证：`Check DiagData[59 02 <Mask> <DTC_3bytes> <Status>]Within[50]ms;`
- 多 DTC 存在验证：`Check DiagData[59 02 <Mask> <DTC1> <Status1> <DTC2> <Status2> ...]Within[50]ms;`
- DTC 已清除验证（无 DTC）：`Check DiagData[59 02 <Mask>]Within[50]ms;`（仅返回 AvailabilityMask，无 DTC 数据）

#### 特殊规则

1. 每个 DTC 的触发条件不同，需从 DTC 表读取对应方法（电压异常、LIN 通讯故障等）
2. 多 DTC 场景需选择不同的故障分别触发
3. 状态 09 = testFailed + confirmedDTC，状态 08 = 仅 confirmedDTC
4. `19 02 FF` 返回无 DTC 时格式为 `59 02 <AvailabilityMask>`（仅含 SID + SubFunction + AvailabilityMask）

---

### 分类 4: Incorrect Diagnostic Command Test

#### 用例数量规则

**当 0x14 服务支持（Support = M 或 Y）时：**
固定 2 条（仅 SF_DL 等价类测试，不生成 DLC 测试）

| 序号 | 错误类型 | 描述 |
|------|---------|------|
| 1 | SF_DL > 4 | 有效负载长度大于合法值 |
| 2 | SF_DL < 4 | 有效负载长度小于合法值 |

**当 0x14 服务不支持（Support = S/O/N/空）时：**
- 标注"无符合条件的用例"，不生成实质内容

#### 用例命名规则

1. `Valid SF_DL=4, invalid SF_DL > 4, and those with invalid equivalence class SF_DL=5`
2. `Valid SF_DL=4, invalid SF_DL < 4, and those with invalid equivalence class SF_DL=3`

#### 测试步骤模板

**前置步骤：进入支持的会话**

**A. SF_DL > 4**
```
Send DiagBy[Physical]Data[14 FF FF FF]WithLen[5];
```

**B. SF_DL < 4**
```
Send DiagBy[Physical]Data[14 FF FF FF]WithLen[3];
```

#### Check 规则

| 错误类型 | Expected Output |
|---------|----------------|
| SF_DL > 4 | `Check DiagData[7F 14 13]Within[50]ms;` |
| SF_DL < 4 | `Check DiagData[7F 14 13]Within[50]ms;` |

#### 特殊规则

1. 0x14 的合法 SF_DL 为 4 字节（SID + 3 字节 groupOfDTC），不同于 0x10/0x11 的 2 字节
2. **不要生成 DLC 测试**：LIN/DoLIN 协议不适用 DLC 错误测试，DLC 测试仅在 CAN 协议下适用

---

### 分类 5: NRC Priority Test

#### 用例数量规则

**当 0x14 服务支持（Support = M 或 Y）时：**
固定 1 条，验证 NRC 优先级链。

**当 0x14 服务不支持（Support = S/O/N/空）时：**
- 标注"无符合条件的用例"，不生成实质内容

#### 用例命名规则

`NRC 13>31`

#### 测试步骤模板

```
1. 进入支持的会话
2. Send DiagBy[Physical]Data[14 00 FF FF]WithLen[5];
```

#### Check 规则

- 第 2 步：`Check DiagData[7F 14 13]Within[50]ms;`

#### 特殊规则

1. 同时满足 NRC 0x13（长度错误）和 NRC 0x31（groupOfDTC 不支持）条件时，优先返回 0x13
2. `14 00 FF FF` 中 0x00 作为 groupOfDTC 高字节可能触发 NRC 0x31，但因长度错误（5 字节）应优先返回 0x13

---

## 会话进入标准路径

为统一生成，进入各会话的标准路径如下：

| 目标会话 | 标准进入步骤 |
|---------|------------|
| Default（0x01） | `Send DiagBy[Physical]Data[10 01];` |
| Extended（0x03） | `Send DiagBy[Physical]Data[10 01];` → `Send DiagBy[Physical]Data[10 03];` |
| Programming（0x02） | `Send DiagBy[Physical]Data[10 01];` → `Send DiagBy[Physical]Data[10 03];` → `Send DiagBy[Physical]Data[31 01 02 03];` → `Send DiagBy[Physical]Data[10 02];` |

**会话进入步骤的 Expected Output 规则（重要）：**
- 会话进入步骤（10 01、10 03、10 02）**不使用 AndCheckResp**，必须在 Expected Output 中显式写出对应的 Check
- Session 正响应格式：`Check DiagData[50 <SF> XX XX XX XX]Within[50]ms;`（SF 为子功能字节）
  - Default: `Check DiagData[50 01 XX XX XX XX]Within[50]ms;`
  - Extended: `Check DiagData[50 03 XX XX XX XX]Within[50]ms;`
  - Programming: `Check DiagData[50 02 XX XX XX XX]Within[50]ms;`
- RoutineControl（31 01 02 03）正响应：`Check DiagData[71 01 02 03 00]Within[50]ms;`
- 只有 Seed 请求（27 XX）使用 `AndCheckResp[PositiveResponse]`，不需要单独写 Check
- `Delay[...]ms;`、`Set Voltage[...]`、`Stop SendMsg[...]`、`Resume SendMsg[...]` 等非诊断操作步骤不写 Check，**不在 Expected Output 中列出**，**禁止使用 `--` 占位**
- Expected Output 仅列出有实际 Check 的步骤，编号保持与 Test Procedure 对应步骤一致（如跳过步骤 2，则 Expected Output 中无 `2.` 条目）

---

## 功能寻址用例生成规则

当 `Functional = Y`（支持功能寻址）时，为 Application 和 Boot 域分别生成 Functional 版本：

### Application Functional 寻址规则

1. 将 Physical 分类 1-5 的用例复制为 Functional 版本
2. 发送 0x14 请求时 `[Physical]` 改为 `[Function]`
3. Case ID 中 `Phy` 改为 `Fun`，编号按 Functional 组内重新编号
4. 安全访问步骤（0x27 seed/key）仍使用 Physical
5. **所有 0x14 请求的 Functional 用例预期输出均为 `Check No_Response Within[1000]ms;`**
   - 0x14 服务在 Functional 寻址下抑制正响应（ISO 14229 规范）
   - 即使服务在对应会话中支持，Functional 寻址下也不返回 54 正响应
   - NRC 0x11、NRC 0x13 在 Functional 寻址下同样被抑制，返回 No_Response

### Boot 域规则

1. **Boot Physical Session Layer Test**: 每个会话生成 1 条，预期输出为 `Check DiagData[7F 14 11]Within[50]ms;`（serviceNotSupported）
2. **Boot Functional Session Layer Test**: 每个会话生成 1 条，预期输出为 `Check No_Response Within[1000]ms;`
3. Boot 域的 0x14 不支持安全访问、不生成 Clear DTC、不生成 Incorrect Diag
4. **即使参数表未列出 Boot 域支持 0x14，也必须生成 Boot 域 Session Layer 测试**

当 `Functional = N`（不支持功能寻址）时：
- 仅生成 Physical 用例
- 不生成 Functional 和 Boot Functional 用例

---

## 生成注意事项

1. **Case ID 不可重复**，物理寻址 `Diag_0x14_Phy_001` 起递增，功能寻址 `Diag_0x14_Fun_001` 起递增
2. **编号从 001 开始**，按 App Phy → App Fun → Boot Phy → Boot Fun 顺序编写
3. **每个 Send 都要有对应 Check**，除以下豁免：
   - `Delay[...]ms`、`Set Voltage[...]`、`Stop SendMsg[...]`、`Resume SendMsg[...]` 等非诊断操作步骤不写 Check，**不在 Expected Output 中列出**（**禁止使用 `--` 占位**）
   - 只有 `27 XX` Seed 请求使用 `AndCheckResp[PositiveResponse]`，其不单独写 Check
   - 会话进入步骤（10 01、10 03、10 02）和 RoutineControl（31 01 02 03）**必须**在 Expected Output 中写显式 Check
4. **Expected Output 仅列出有实际 Check 的步骤**，编号保持与 Test Procedure 对应步骤一致，**禁止使用 `--` 占位**
5. **DTC 验证必须成对出现**：清除前验证存在 + 清除后验证已清除
6. **故障制造方法从 DTC 表读取**，不同 DTC 的触发条件不同
7. **不要跳过任何分类**：Secure Access 即使 Level0=Y 也必须生成；Boot 域即使不支持也必须生成 Session Layer 测试
8. **输出格式**：使用 pipe table `| Case ID | Case名称 | 测试步骤 | 预期输出 |`，多行用 `<br>` 分隔
9. **不要在会话进入步骤之间添加 Delay**，直接连续发送
10. **不要在会话进入步骤（10 01、10 03、10 02）使用 AndCheckResp**
11. **生成前首先读取参数表 `Support` 列**：值为 `M` 或 `Y` 才视为支持，`S`/`O`/`N`/空/子功能为 `/` 一律视为不支持；不支持时 App 域分类 2-5 全部标注"无符合条件的用例"，所有 Physical 用例预期 NRC 0x11
