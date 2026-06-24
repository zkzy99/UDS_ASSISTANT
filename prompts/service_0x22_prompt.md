# Service 0x22 ReadDataByIdentifier — 用例生成规则

<!--
## 版本管控

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.0 | — | 初始版本 |
| v1.1 | 2026-05-06 | 1) APP不支持会话NRC从0x7F修正为0x31；2) Secure Access即使Level0也必须生成；3) 新增Unsupported DID测试规则；4) Boot功能寻址完整覆盖；5) DID Range/Incorrect Command/NRC Priority多会话覆盖 |
| v1.2 | 2026-05-06 | 基于奇瑞/华智/蔚来/恒润四方对比优化：1) 新增核心原则宁滥勿缺+精准度；2) Functional=Y时完整镜像；3) 新增CAN DLC测试；4) Delay可选；5) Fun连续编号；6) 混合寻址安全访问；7) 数据填充优先用精确值 |
| v1.3 | 2026-05-22 | 强化输出纪律：禁止分析推理段落、禁止重复表头、禁止省略号、每条用例必须完整 |
| v1.4 | 2026-05-22 | 对标参考文件精简：1) 去掉不支持会话负向用例；2) 去掉Unsupported DID测试；3) Secure Access仅为需安全等级DID生成；4) Boot域简化为代表性DID |
| v1.5 | 2026-05-22 | 对标 shared_nrc_rules.md 精简：移除输出纪律、典型NRC表、软件域规则、会话进入路径、生成注意事项等已共享的重复内容 |
-->

## 核心原则

1. **宁滥勿缺**：用例覆盖率优先，宁可多生成不可漏生成。所有分类、会话、DID组合都必须覆盖完整，不可为简化而减少用例数量
2. **精准度要求**：预期输出中的参数必须精确——从参数表中提取 DefaultValue、Byte Length、数据类型等信息填充实际值，尽量避免使用 xx 占位符。只有参数表确实未定义且无法推断的值才使用 xx

## 服务概述

- **Service ID**: 0x22
- **Service Name**: ReadDataByIdentifier
- **请求格式**: `22 <DID_H> <DID_L>`
- **无 Subfunction**（DID 替代子功能角色）
- **合法 SF_DL**: 3 字节（SID + DID 2 字节）
- **关键特性**: 不存在 NRC 0x12（因为没有子功能概念）；NRC 0x31 用于不支持的 DID
- **NRC 优先级链（服务级，0x22 专用）**:

> **关键规则**：以下为 0x22 服务的**完整** NRC 优先级链模板。实际生成时必须从参数表 `Negative response codes` 字段读取精确的 NRC 列表和顺序，**参数表声明了哪些 NRC 就覆盖哪些**。下表列出 0x22 所有可能的 NRC 及触发条件，生成时按参数表实际声明的 NRC 筛选使用。

| 优先级 | NRC | 触发条件 |
|--------|-----|---------|
| 1 | 0x13 | 长度错误（SF_DL≠3 或非模2整除） |
| 2 | 0x11 | 服务不支持（ECU 全局不支持 0x22 服务时） |
| 3 | 0x7F | 服务在当前会话不支持 |
| 4 | 0x31 | DID 不支持 / 数据记录无效 |
| 5 | 0x33 | 安全访问未解锁 |
| 6 | 0x22 | DID 前提条件不满足 |
| 7 | 0x14 | 响应总长度超限（0x22 专有） |
| 8 | 0xXX | 厂商/供应商自定义 |

**NRC 全覆盖要求**：参数表 `Negative response codes` 字段中列出的**每一个** NRC 都必须有至少一条专用测试用例。常用覆盖策略：
- **0x13**：Incorrect Diagnostic Command（SF_DL≠3）覆盖
- **0x11**：若参数表声明，Session Layer 覆盖（当前会话不支持 0x22 服务）
- **0x7F**：若参数表声明，Session Layer 覆盖（服务在当前会话不支持）
- **0x31**：DID Range Test 覆盖（不支持的 DID）、Session Layer 覆盖
- **0x33**：Secure Access Test 覆盖（安全访问未解锁时读取需安全等级的 DID）
- **0x22**：NRC Priority Test 覆盖（DID 前提条件不满足）
- **0x14**：NRC Priority Test 覆盖（读取超长 DID 组合导致响应超限）

### 正响应格式

- `62 <DID_H> <DID_L> <Data...>`
- 数据长度 = DID 的 Byte Length（从 DID 表读取）
- 数据内容使用 DefaultValue（如参数表有定义）或 xx 占位

---

## 寻址规则

- **Physical 寻址**：生成完整测试集
- **Functional 寻址**：即使 Functional Request = N，仍需生成功能寻址用例集（全部预期 No_Response）
- 当 Functional Request = Y 时，功能寻址用例必须是物理寻址的完整镜像（每个 DID × 每个会话全部覆盖）

---

## 生成分类（共 7 类）

按以下固定顺序逐类生成，每个分类使用 `## N.N` 作为标题（如 `## 1.1 Session Layer Test`）。

---

### 分类 1: Session Layer Test (APP)
#### 用例数量规则

- **正向用例**: `Npos` = 可读 DID × 支持的会话数（每个可读 DID 在每个支持的会话下各 1 条）
- **总数 = Npos**（仅正向用例，不生成不支持会话的负向用例）

#### 生成顺序

按会话分组，每组内按 DID 排序：
1. Default Session 正向（每个可读 DID 1 条）
2. Extended Session 正向（每个可读 DID 1 条）

#### 用例命名规则

- 正向：`<CurrentSessionName> Session supports reading DID: 0x<DID> PositiveCase-$22`
  - 示例：`Default Session supports reading DID: 0xF197 PositiveCase-$22`

#### 测试步骤模板

**⚠️ 关键规则：test_procedure 中只写 Send/Delay/Set 操作，绝对不要写 Check 语句！Check 一律放到 expected_output 中。**

**A. Default 会话正向（可读 DID）**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
```

**B. Extended 会话正向（可读 DID）**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
```

#### Check 规则（expected_output）

**A. Default 会话正向：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[62 <DID_H> <DID_L> <DataContent>]Within[50]ms;`

**B. Extended 会话正向：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：`Check DiagData[62 <DID_H> <DID_L> <DataContent>]Within[50]ms;`

**DataContent 填充规则：**
- DataContent 长度 = DID 的 Byte Length
- 固定值用实际值（如 F186=当前会话号 01/02/03）
- 可变值用 xx

#### 特殊规则

1. 每个 DID 单独一条用例，不可合并
2. DID 数据内容中，固定值用实际值，可变值用 xx
3. 若 DID 支持 Read 但未定义 Default 值，用 xx 占位
4. 特殊 DID 示例：DID 0xF186（Active Diagnostic Session），1 字节，值=当前会话号（01/02/03）
5. DID 列表从 DID 表（Sheet 含 "DID" 或 "0x22"/"0x2E"）读取，包括 Basic DIDs 和 RDBI DIDs
6. **test_procedure 中只写操作（Send/Delay/Set），绝对禁止写 Check；Check 一律写到 expected_output 中**
7. **Expected Output 编号与 Test Procedure 步骤编号一一对应，session entry 的 Check 不可省略**

---

### 分类 2: Secure Access Test
#### 用例数量规则

- **仅为 Read Access Level 不为 Level0 的 DID 生成安全访问用例**
- Read Access Level 为 Level0（无安全限制）的 DID 不需要生成安全访问用例
- **APP 域**：在 Extended Session 中执行 Seed/Key 解锁，然后读取需安全等级的 DID → **总数 = APP 需安全等级的 DID 数**
- **Boot 域（简化）**：在 Programming Session 中执行 Boot 级 Seed/Key 解锁，然后读取 3-5 个代表性 Boot DID（不需要为每个 Boot DID 都生成）→ **总数 = 3~5 条**

#### 用例命名规则

- APP 域：`Security access Lx unlock supports 0x22 service read DID 0x<DID>`
  - 示例：`Security access L2 unlock supports 0x22 service read DID 0xF198`
- Boot 域：`Boot Security access Lx unlock supports 0x22 service read DID 0x<DID>`
  - 示例：`Boot Security access L12 unlock supports 0x22 service read DID 0xF180`

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send/Delay/Set 操作，绝对不要写 Check 语句！AndCheckResp 步骤除外（但也不写 Check）。**

**APP 域（Extended Session）**：
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PostiveResponse];
4. Send Security Right KeyBy[Physical]Level[<KeySub>];
5. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
```

**Boot 域（Programming Session）**：
```
1. Send DiagBy[Physical]Data[10 01];
2. Delay[1000]ms;
3. Send DiagBy[Physical]Data[10 03];
4. Send DiagBy[Physical]Data[31 01 02 03];
5. Send DiagBy[Physical]Data[10 02];
6. Send DiagBy[Physical]Data[27 <BootSeedSub>]AndCheckResp[PostiveResponse];
7. Send Security Right KeyBy[Physical]Level[<BootKeySub>];
8. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
```

#### Check 规则（expected_output）

**APP 域（Extended Session）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：不写 Check（AndCheckResp 内含检查）
- 第 4 步：`Check DiagData[67 <KeySub>]Within[50]ms;`
- 第 5 步：`Check DiagData[62 <DID_H> <DID_L> <DataContent>]Within[50]ms;`

**Boot 域（Programming Session）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：不写 Check（Delay 为非诊断操作）
- 第 3 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 4 步：`Check DiagData[71 01 02 03 00]Within[50]ms;`
- 第 5 步：`Check DiagData[50 02 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 6 步：不写 Check（AndCheckResp 内含检查）
- 第 7 步：`Check DiagData[67 <BootKeySub>]Within[50]ms;`
- 第 8 步：`Check DiagData[62 <DID_H> <DID_L> <DataContent>]Within[50]ms;`

**注意**：非诊断步骤（Delay）不在 Expected Output 中列出，禁止使用 `--` 占位。

#### 特殊规则

1. 安全等级从 DID 表的 Read Access Level 字段读取，不写死
2. APP 域 SeedSub/KeySub：从 ApplicationServices 的安全等级表获取（如 L1 → 27 01/27 02，L2 → 27 03/27 04）
3. Boot 域 SeedSub/KeySub：从 BootServices 的安全等级表获取（如 L11 → 27 11/27 12，与 APP 域可能不同）
4. **Read Access Level 为 Level0 的 DID 不生成安全访问用例**
5. Boot 域简化：选取 3-5 个代表性 DID（如 System DID 中选 2-3 个 + ECU DID 中选 1-2 个）

---

### 分类 3: Boot Session Layer Test（简化）

#### 用例数量规则

- Boot 域**简化生成**，选取 5-8 个代表性 DID（覆盖不同类型：System DID、版本号 DID、供应商 DID 等）
- `Npos_boot` = 代表性 DID × Boot 支持的会话数
- **不生成** APP-only DID 的负向用例和 unsupported DID 测试
- Boot 域的标准进入路径：`Default → Extended → Programming → Default(Boot)`

#### 生成顺序

按 Boot 会话分组：
1. Boot Default Session 正向（每个代表性 DID 1 条）
2. Boot Programming Session 正向（每个代表性 DID 1 条）
3. Boot Extended Session（如支持）正向

#### 用例命名规则

- 正向：`Boot <SessionName> Session supports reading DID: 0x<DID> PositiveCase-$22`
  - 示例：`Boot Programming Session supports reading DID: 0xF180 PositiveCase-$22`

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send/Delay/Set 操作，绝对不要写 Check 语句！**

**Boot Programming Session 正向（代表性 DID）**
```
1. Send DiagBy[Physical]Data[10 01];
2. Delay[1000]ms;
3. Send DiagBy[Physical]Data[10 03];
4. Send DiagBy[Physical]Data[31 01 02 03];
5. Send DiagBy[Physical]Data[10 02];
6. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
```

**Boot Default Session 正向（代表性 DID）**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
```

#### Check 规则（expected_output）

**Boot Programming Session 正向：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：不写 Check（Delay 为非诊断操作）
- 第 3 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 4 步：`Check DiagData[71 01 02 03 00]Within[50]ms;`
- 第 5 步：`Check DiagData[50 02 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 6 步：`Check DiagData[62 <DID_H> <DID_L> <DataContent>]Within[50]ms;`

**Boot Default Session 正向：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[62 <DID_H> <DID_L> <DataContent>]Within[50]ms;`

**注意**：非诊断步骤（Delay）不在 Expected Output 中列出，禁止使用 `--` 占位。

---

### 分类 4: DID Range Test
#### 用例数量规则

- **APP 域**：每个支持 0x22 的会话各 1 条 → 通常 Default + Extended = **2 条**
- **Boot 域（简化）**：仅 Default Session 1 条 → **1 条**

#### 用例命名规则

- APP Default 物理寻址：`DID range traversal test by physical addressing in Default Session`
- APP Extended 物理寻址：`DID range traversal test by physical addressing in Extended Session`
- Boot Default 物理寻址：`Boot DID range traversal test by physical addressing in Default Session`
- Boot Programming 物理寻址：`Boot DID range traversal test by physical addressing in Programming Session`
- Boot Extended 物理寻址：`Boot DID range traversal test by physical addressing in Extended Session`

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send/Delay/Set 操作，绝对不要写 Check 语句！AndCheckResp 步骤除外。**

**APP Default Session**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DIDTraversalBy[Physical]Service[0x22]Excluding[<AllSupportedDIDList>]AndCheckResp[0x31];
```

**APP Extended Session**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DIDTraversalBy[Physical]Service[0x22]Excluding[<AllSupportedDIDList>]AndCheckResp[0x31];
```

其中：
- `<AllSupportedDIDList>` = 所有 Support=Y 的 DID（含 Basic DIDs 和 RDBI DIDs）
  - 示例：`F1 86 F1 87 F1 88 F1 89 F1 90 F1 91 F1 92 F1 93 ...`
- Boot 版本的 Excluding 列表使用 Boot 域的 DID 列表（仅生成 Default Session 1 条）

#### Check 规则（expected_output）

**APP Default Session：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：不写 Check（AndCheckResp 内含检查，遍历不支持的 DID → `7F 22 31`）

**APP Extended Session：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：不写 Check（AndCheckResp 内含检查）

#### 特殊规则

1. Excluding 列表必须包含所有 Support=Y 的 DID，包括 3.1(Basic DIDs) 和 3.2(RDBI DIDs) Sheet 中的
2. Boot 域 DID Range 使用 Boot 域的 Excluding 列表

---

### 分类 5: Incorrect Diagnostic Command Test
#### 用例数量规则

- **APP 域**：每个支持 0x22 的会话各 2 条（SF_DL > 3 + SF_DL < 3）→ 通常 Default + Extended = **4 条**
- **Boot 域（简化）**：仅 Default Session 2 条 → **2 条**

| 序号 | 错误类型 | 描述 |
|------|---------|------|
| 1 | SF_DL > 3 | 有效负载长度大于合法值 |
| 2 | SF_DL < 3 | 有效负载长度小于合法值 |

#### 用例命名规则

1. `<SessionName> Session invalid SF_DL > 3 triggers NRC 0x13`
2. `<SessionName> Session invalid SF_DL < 3 triggers NRC 0x13`

Boot 域加前缀 `Boot `。每个会话独立生成一对用例。

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send/Delay/Set 操作，绝对不要写 Check 语句！**

选择一个代表性可读 DID（如 F1 86）进行测试。

**Default Session — SF_DL > 3**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[22 F1 86]WithLen[4];
```

**Default Session — SF_DL < 3**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[22 F1]WithLen[2];
```

**Extended Session — SF_DL > 3**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[22 F1 86]WithLen[4];
```

**Extended Session — SF_DL < 3**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[22 F1]WithLen[2];
```

APP 域在 Default 和 Extended 会话下分别生成；Boot 域仅在 Default Session 下生成。

#### Check 规则（expected_output）

**Default Session — SF_DL 错误：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[7F 22 13]Within[50]ms;`

**Extended Session — SF_DL 错误：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：`Check DiagData[7F 22 13]Within[50]ms;`

#### 特殊规则

1. 0x22 的合法 SF_DL 为 3 字节（SID + DID 2 字节）
2. 不存在 NRC 0x12（0x22 无子功能概念）
3. SF_DL 错误使用 `Send DiagBy...WithLen[...]`
4. Boot 域必须独立生成 2 条 Incorrect Command 用例

#### CAN DLC 测试（仅 CAN 协议项目适用）

当协议为 CAN（非 LIN）时，还需额外生成 DLC 级别测试用例：

| 序号 | 错误类型 | 描述 |
|------|---------|------|
| 3 | DLC < 8 | CAN帧DLC不足8字节，ISO-TP无法解析 |
| 4 | DLC > 8 | CAN帧DLC超过8字节（正常响应） |

- **DLC < 8**：使用原始 CAN 帧格式 `Send Msg[<CAN_ID>]Data[03 22 F1 86]WithDLC[7]`，预期 `Check No_Response Within[1000]ms;`
- **DLC > 8**：使用原始 CAN 帧格式 `Send Msg[<CAN_ID>]Data[03 22 F1 86 00 00 00 00 00]WithDLC[9]`，预期正常正响应
- CAN_ID 从参数表 General 中获取（物理寻址ID）
- LIN 协议项目不生成 DLC 测试用例

---

### 分类 6: NRC Priority Test
#### 用例数量规则

- **【强制】NRC 全量覆盖**：优先级链必须包含参数表 `Negative response codes` 字段声明的**所有 NRC**。每个已声明的 NRC 必须至少有一条专用用例覆盖。
- **APP 域**：每个支持 0x22 的会话各 1 条 → 通常 Default + Extended = **2 条**
- **Boot 域（简化）**：仅 Default Session 1 条 → **1 条**

#### 用例命名规则

- APP：`<SessionName> Session NRC priority test for service 0x22`
- Boot：`Boot <SessionName> Session NRC priority test for service 0x22`

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send/Delay/Set 操作，绝对不要写 Check 语句！**

在对应会话下，发送长度错误的 0x22 请求（如 SF_DL < 3），验证 ECU 优先返回 NRC 0x13 而非其他 NRC。

**Default Session**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[22 F1]WithLen[2];
```

**Extended Session**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[22 F1]WithLen[2];
```

**NRC 0x11 专用覆盖（若参数表声明）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
```
预期：`Check DiagData[7F 22 11]Within[50]ms;`（服务在当前会话不支持）

**NRC 0x7F 专用覆盖（若参数表声明）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
```
预期：`Check DiagData[7F 22 7F]Within[50]ms;`（服务在当前会话不支持）

**NRC 0x31 专用覆盖（若参数表声明）：**
已在 DID Range Test 中覆盖（不支持的 DID 返回 0x31）

**NRC 0x33 专用覆盖（若参数表声明）：**
已在 Secure Access Test 中覆盖（需安全等级的 DID 在未解锁时读取）

**NRC 0x14 专用覆盖（若参数表声明，0x22 专有）：**
1. 请求读取一个超长 DID 或多个 DID 组合，导致正响应总长度超出 ECU 限制
2. 预期：`Check DiagData[7F 22 14]Within[50]ms;`

**NRC 0x22 专用覆盖（若参数表声明）：**
1. 在 DID 前提条件不满足时（如车速=0 而 DID 要求车速>0）发送 0x22 请求
2. 预期：`Check DiagData[7F 22 22]Within[50]ms;`

#### 用例命名规则

- APP：`<SessionName> Session NRC priority test for service 0x22`
- Boot：`Boot <SessionName> Session NRC priority test for service 0x22`

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send/Delay/Set 操作，绝对不要写 Check 语句！**

在对应会话下，发送长度错误的 0x22 请求（如 SF_DL < 3），验证 ECU 优先返回 NRC 0x13 而非其他 NRC。

**Default Session**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[22 F1]WithLen[2];
```

**Extended Session**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[22 F1]WithLen[2];
```

#### Check 规则（expected_output）

**Default Session：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[7F 22 13]Within[50]ms;`

**Extended Session：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：`Check DiagData[7F 22 13]Within[50]ms;`

#### 特殊规则

1. NRC 0x13（消息长度错误）的优先级高于 NRC 0x31（DID 不支持）等
2. 此用例验证 ECU 正确的 NRC 优先级处理
3. APP 域在各支持会话下生成；Boot 域仅在 Default Session 下生成
4. **【强制】NRC 全量覆盖自检**：生成完所有用例后，必须逐一核对参数表 `Negative response codes` 字段声明的每一个 NRC（0x11、0x7F、0x13、0x31、0x14、0x22、0x33 等）是否都有至少一条专用测试用例。漏掉任何一个已声明 NRC 均为不合格输出。

---

## 功能寻址用例生成规则

当 `Functional Request = 支持` 时：
1. 将所有 Physical 用例复制一份（完整镜像，不可简化为代表性子集）
2. 发送函数中 `[Physical]` 改为 `[Function]`
3. Case ID 中 `Phy` 改为 `Fun`，编号连续（不从001重启，接续 Physical 最后编号）
4. DID 遍历功能寻址版同样使用 `DIDTraversalBy[Function]`
5. **安全访问混合寻址**：功能寻址用例中，Session 进入和 DID 读取使用 `[Function]`，但 SecurityAccess（Seed/Key）步骤仍使用 `[Physical]`，因为安全访问通常要求物理寻址

当 `Functional Request = 不支持` 时：
- **仍需生成功能寻址用例集**，分 APP 域和 Boot 域两部分：
- **APP 域功能寻址**（分以下 3 个子类）：
  1. **代表性 DID 读取**（Default 会话，选取 2-3 个代表性 DID）：预期全部 No_Response
  2. **DID Range 遍历**（1 条）：`DIDTraversalBy[Function]` → 全部 No_Response
  3. **Incorrect Command**（1-2 条）：SF_DL 错误 → 全部 No_Response
- **Boot 域功能寻址（简化）**：
  1. **代表性 DID 读取**（Default 会话，选取 2-3 个代表性 Boot DID）：预期全部 No_Response
  2. **Incorrect Command**（1-2 条）：SF_DL 错误 → 全部 No_Response
- 所有 Functional 用例预期输出均为 `Check No_Response Within[1000]ms;`

---

## DID 数据填充规则

**核心要求：预期输出中的数据必须尽可能精确，尽量减少 xx 占位符的使用。Session 正响应时序参数按共享规则的编码公式计算实际值，绝对禁止使用 `XX XX XX XX`。**

优先级从高到低：

| 优先级 | 场景 | 填充方式 | 说明 |
|--------|------|---------|------|
| 1 | DID 数据为固定值 | 使用实际值 | 如 F186=当前会话号(01/03)，F160=01 |
| 2 | DID 有定义 DefaultValue（文本） | 字符串逐字节转 HEX | 如 F197="HOD" → `48 4F 44`，F18A="8DR" → `38 44 52` |
| 3 | DID 有 Default value(Phy.)（数值） | 数值按 Data Type 转 HEX | 如 F010 Default=0, ByteLen=4 → `00 00 00 00` |
| 4 | DID 参数表的 Comment 含初始值 | 从 Comment 提取并转换 | 如 "Initial value: 0x20,0x20" → `20 20` |
| 5 | DID 数据为可变值且无任何默认值 | 使用 xx 占位 | **最后手段**，仅当确实无法获取任何精确值时使用 |

**⚠️ 数值默认值转换规则（重要）：**
- `type=linear unsigned` 且 Default Value(Phy)=0, Byte Length=4 → 4 字节零值：`00 00 00 00`
- `type=linear unsigned` 且 Default Value(Phy)=0, Byte Length=2 → 2 字节零值：`00 00`
- `type=identical` 且 Default Value(Phy)=0 → 对应字节长度的零值
- **数值 0 的默认值不是 xx！必须转换为对应字节长度的 00 填充！**
- 公式 `k=1, b=0, n=1, pre=0` 表示物理值 = HEX 值（直接相等）

**重要规则**：
- ASCII 类型 DID：将字符串逐字节转换为 HEX（如 "HOD" → `48 4F 44`），不足 Byte Length 用 `20`（空格）填充
- 数值类型 DID：按 Data Type 和 Formula 计算 HEX 值，按 Byte Length 填充
- BCD 类型 DID：使用 BCD 编码填充
- 如果参数表中有多个子行（同一 DID 多个字节定义），每个字节按子行定义分别填充
- **数据长度必须精确匹配 DID 的 Byte Length**

---

## 分类汇总

| 分类 | 描述 | 用例数量公式 |
|------|------|-------------|
| 1. Session Layer (APP) | 可读 DID × 支持会话（仅正向） | `\|DIDs\| × \|支持会话\|` |
| 2. Security Access (APP+Boot) | APP 需安全等级 DID + Boot 代表性 DID（3-5条） | `\|需安全DID\| + 3~5` |
| 3. Boot Session Layer (简化) | 代表性 DID × Boot 支持会话（仅正向） | `5~8 × \|Boot支持会话\|` |
| 4. DID Range | APP 每支持会话 1 条 + Boot 1 条 | `\|APP支持会话\| + 1` |
| 5. Incorrect Command | APP 每支持会话 2 条 + Boot 2 条 | `\|APP支持会话\| × 2 + 2` |
| 6. NRC Priority | APP 每支持会话 1 条 + Boot 1 条 | `\|APP支持会话\| + 1` |
| 7. Functional Addressing | 完整镜像（Physical 所有用例） | Physical 用例总数的 1 倍 |
