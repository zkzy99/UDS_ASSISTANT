# Service 0x11 ECUReset — 用例生成规则

## 服务概述

- **Service ID**: 0x11
- **Service Name**: ECUReset
- **正响应 SID**: 0x51（0x11 + 0x40）
- **负响应格式**: `7F 11 <NRC>`
- **子功能**: 通常包含 01（HardReset）、02（KeyOffOnReset）、03（SoftReset），具体以参数表为准
- **关键特性**: 先回正响应，再执行复位；复位期间 ECU 不响应其它请求
- **NRC 优先级链（服务级，0x11 专用）**:

| 优先级 | NRC | 触发条件 |
|--------|-----|---------|
| 1 | 0x13 | 长度错误（SF_DL≠2） |
| 2 | 0x12 | 子功能不支持 |
| 3 | 0x7E | 子功能在当前会话不支持 |
| 4 | 0x22 | 前提条件不满足 |

### 正响应格式

- 若 `reset_time Support = N`：`51 <Subfunction>`
- 若 `reset_time Support = Y`：`51 <Subfunction> <ResetTime_H> <ResetTime_L>`
- `reset_time` 是否支持从参数表 `1.Basic Diagnostic Infomation -> $11 Timing parameters` 读取

### 典型 NRC

| NRC  | 含义 | 触发条件 |
|------|------|---------|
| 0x12 | Subfunction Not Supported | 发送了 0x11 不支持的子功能 |
| 0x13 | Incorrect Message Length Or Invalid Format | 报文长度错误（WithLen）或 DLC 异常 |
| 0x22 | Conditions Not Correct | 前置条件不满足 |
| 0x7E | Subfunction Not Supported In Active Session | 该子功能在当前会话下不支持 |
| 0x7F | Service Not Supported In Active Session | 当前会话下整体不支持 0x11 服务（客户口径） |

---

## 整体结构要求

每个软件域（App / Boot）每种寻址方式（Physical / Functional）必须独立生成完整用例集。

生成顺序：
1. **App Physical** — 标题 `1.Application Service_Physical Addressing`
2. **App Functional** — 标题 `2.Application Service_Functional Addressing`（仅当 Functional=Y）
3. **Boot Physical** — 标题 `3.Boot Service_Physical Addressing`
4. **Boot Functional** — 标题 `4.Boot Service_Functional Addressing`（仅当 Functional=Y）

每组内部包含以下分类（按顺序），每个分类使用 `## N.N` 作为标题（如 `## 1.1 Session Layer Test`）：
1. Session Layer Test
2. SPRMIB Test
3. Secure Access Test（即使无安全限制也必须生成验证用例）
4. Reset Effect Test（客户扩展）
5. Sub-function Traversal Test
6. Incorrect Diagnostic Command & NRC Priority Test（仅 Physical 寻址生成 NRC Priority 部分）
7. Functional Addressing Test（仅当 Functional 不支持时）

### 输出格式要求

1. **顶级标题使用 `#`**：如 `# 1. Application Service_Physical Addressing`、`# 2. Application Service_Functional Addressing`、`# 3. Boot Service_Physical Addressing`、`# 4. Boot Service_Functional Addressing`
2. **分类标题使用 `##`**：如 `## 1.1 Session Layer Test`、`## 1.2 SPRMIB Test`、`## 1.3 Secure Access Test` 等
3. **各大组之间用 `---` 分隔**
4. **无符合条件的用例时使用 `>` 引用**：如 `> App 域 0x11 所有子功能... 无符合条件的用例。`
5. **输出格式严格为 pipe table**，列顺序：`| Case ID | Case名称 | 测试步骤 | 预期输出 |`
6. **步骤中换行使用 `<br>` 标记**，不用 `\n`
7. **不要生成任何"参数提取结果"或"分析"段落**，直接输出测试用例表格

#### 步骤序号强制规则（重要）

#### 两个字段的职责划分

> **`test_procedure` 只写"操作动作"，`expected_output` 只写"Check 检查"，两者共用同一套序号，Check 的序号与对应 Send 步骤编号一致。**

| 字段 | 写什么 | 不写什么 |
|------|--------|---------|
| `test_procedure` | Send / Delay / Set / Change 等**操作** | 不写 Check（Check 放到 expected_output） |
| `expected_output` | Check DiagData / Check No_Response 等**检查** | 不写 Send / Delay / Set |

**序号规则：**
- `test_procedure` 步骤按 `1.` `2.` `3.` ... 顺序编号
- `expected_output` 的 Check 编号与 `test_procedure` 中对应 Send 步骤编号**完全一致**
- 没有 Check 的步骤（`Delay`、`Set Voltage` 等）在 `expected_output` 中跳过，序号不连续是正常的
- `AndCheckResp[...]` 步骤在 `test_procedure` 中计入序号，但**不在** `expected_output` 中单独出现（已内含检查）

**错误格式示例（禁止）：**
- `test_procedure` 中混入 Check 语句（如 `2.Check DiagData[...]`）——Check 必须在 `expected_output`
- `expected_output` 只写最后一条 Check，忽略前面所有步骤的 Check
- 使用 `Step1:` 格式（禁止，必须用 `1.`）
- 序号与内容之间有空格（`1. Send` 禁止，必须是 `1.Send`）

> **`test_procedure` 和 `expected_output` 字段中，每一行都必须以 `N.` 序号开头，序号与内容之间无空格，行与行之间用 `<br>` 分隔。**

**错误格式示例（禁止）：**
- `Step1: Send DiagBy[Physical]Data[10 03];`（**严禁使用 `Step1:` 格式**）
- `Send DiagBy[Physical]Data[10 03];<br>Check DiagData[...]Within[50]ms;`（缺少序号）
- `1. Send DiagBy[Physical]Data[10 03];`（序号与内容之间不得有空格）

规则细则：
1. 序号从 `1.` 开始递增，格式为 `1.` `2.` `3.` ...，**中间无空格、无冒号、无其他字符**
2. 每个 Send / Check / Delay / Set 等操作各占一行，独立编号
3. `expected_output` 序号与 `test_procedure` 中对应步骤编号一致；仅一行时也必须写 `1.`
4. `AndCheckResp[...]` 步骤不在 `expected_output` 中单独列出，但在 `test_procedure` 中计入序号
5. `Delay[...]ms;` 步骤计入 `test_procedure` 序号，不在 `expected_output` 中出现

---

### 分类 1: Session Layer Test


#### 用例数量规则

必须覆盖**当前域的所有会话 × 所有子功能的完整交叉组合**（含全局不支持的子功能）。

- 对每个 (会话, 子功能) 组合：
  - 该会话支持该子功能 → 正向 case
  - 该会话不支持该子功能，但子功能全局存在 → 负向 case（NRC 0x7E）
  - 子功能全局不支持（Support=N）→ 也生成负向 case（NRC 0x12）
- **总数 = 可达会话数 × 子功能总数（含全局不支持的）**

#### 用例命名规则

- 正向：`<CurrentSessionName> Session support the 0x11 service 0x<Sub> subfunction`
  - 示例：`Extended Session support the 0x11 service 0x01 subfunction`
- 负向（会话不支持）：`<CurrentSessionName> Session nonsupport 0x11 services`
  - 示例：`Default Session nonsupport 0x11 services`
- 负向（子功能不支持）：`0x11 service nonsupport 0x<Sub> subfunction`
  - 示例：`0x11 service nonsupport 0x02 subfunction`

#### 测试步骤模板

**A. 当前会话不支持 0x11 服务（负向）**
```
1. 进入 <CurrentSessionNotSupport>（通常为 Default）
2. Send DiagBy[Physical]Data[11 <RepSupportedSub>];
```

**B. 支持子功能正向**
```
1. 进入 <CurrentSessionSupport>（通常为 Extended）
2. Send DiagBy[Physical]Data[11 <SupportSub>];
3. Delay[1000]ms;
```

**C. 子功能不支持（负向）**
```
1. 进入 <CurrentSessionSupport>（通常为 Extended）
2. Send DiagBy[Physical]Data[11 <UnsupportedSub>];
```

#### Check 规则

**A. 当前会话不支持服务：**
- `Check DiagData[7F 11 7F]Within[50]ms;`
- 注意：此处 NRC 使用 0x7F 而非 0x7E，为客户当前模板口径

**B. 支持子功能正向：**
- 若 reset_time Support = N：`Check DiagData[51 <Sub>]Within[50]ms;`
- 若 reset_time Support = Y：`Check DiagData[51 <Sub> <ResetTime_H> <ResetTime_L>]Within[50]ms;`

**C. 子功能不支持：**
- `Check DiagData[7F 11 12]Within[50]ms;`

#### 特殊规则

1. 0x11 先回正响应，再执行复位
2. Delay[500]ms 或 Delay[1000]ms 只用于等待 ECU 复位稳定，不单独写 check
3. 默认优先在 Extended 会话下做正向验证
4. 全局不支持的子功能不在 Session Layer 中出用例，放到 Sub-function Traversal Test

---

### 分类 2: SPRMIB Test


#### 用例数量规则

必须覆盖**所有会话 × 支持的子功能的 SPRMIB 变体**。

- 子功能支持 + SPRMIB=Y + 正向成功 → No_Response
- 子功能支持 + SPRMIB=N → 发送 `11 <0x80 + Sub>`，ECU 不支持抑制位，返回 NRC 0x12
- 会话不支持该子功能 → NRC 0x7E

> **关键规则**：SPRMIB Test **不生成全局不支持的子功能（Support=N）用例**。Session Layer 已覆盖 NRC 0x12 场景，SPRMIB 版本预期相同（仍是 NRC 0x12），属于重复测试。

> **SPRMIB 支持性判断规则**：从参数表 `Supported Services` sheet 的 SPRMIB 列读取：
> - 若标注为 `Y` / `TRUE (0)` / `(Response)` → ECU **支持**抑制位，正向请求预期 `No_Response`
> - 若标注为 `N` / `suppressPosRspMsgIndicationBit= TRUE (1) (No response)` → ECU **不支持**抑制位；客户端发送带 suppress bit 的请求（`11 <0x80 + Sub>`），ECU 必须回复 **NRC 0x12**（Subfunction Not Supported），预期为 `Check DiagData[7F 11 12]Within[50]ms;`

**总数 = 可达会话数 × 支持的子功能数**（不含全局不支持的）

#### 用例命名规则

在 Session Layer 对应名称后追加 `with SPRMIB`
- 示例：`Extended Session support the 0x11 service 0x01 subfunction with SPRMIB`

#### 测试步骤模板

在 Session Layer 同名 case 基础上：
1. 将最终请求 `11 <Sub>` 改为 `11 <0x80 + Sub>`
   - `11 01` → `11 81`
   - `11 02` → `11 82`
   - `11 03` → `11 83`
2. **SPRMIB=Y 正向场景**：必须追加复位后状态确认步骤（因为正向响应被抑制，需额外验证复位生效）
3. **SPRMIB=N 正向场景**：无需追加额外验证步骤，直接检查 NRC 0x12

正向且 SPRMIB=Y 完整步骤示例：
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[11 81];
3. Delay[1000]ms;
4. 验证复位后回到 Default（若支持 F186 用 22 F1 86，否则用 31 服务）
```

正向且 SPRMIB=N 完整步骤示例：
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[11 81];
```

#### Check 规则

**若原场景正向成功且 SPRMIB=Y（支持抑制位）：**
- 第 2 步：`Check No_Response Within[1000]ms;`
- 第 4 步：验证复位后回到默认会话（按优先级选择验证方式）：
  1. 若支持 DID F186：`Send DiagBy[Physical]Data[22 F1 86];` → `Check DiagData[62 F1 86 01]Within[50]ms;`
  2. 若不支持 F186：通过 31 服务 — `Send DiagBy[Physical]Data[31 01 02 03];` → `Check DiagData[7F 31 7F]Within[50]ms;`
  3. 或通过 28 服务 / 27 服务验证

**若原场景正向成功且 SPRMIB=N（不支持抑制位）：**
- 第 2 步：`Check DiagData[7F 11 12]Within[50]ms;`
- 说明：ECU 收到带 suppress bit 的请求但不支持该特性，按 NRC 优先级链应回复 NRC 0x12

**若原场景负向：**
- 仍返回负响应，规则同 Session Layer
- 会话不支持：`7F 11 7F`
- 子功能不支持：`7F 11 12`

#### 特殊规则

1. 正向且 SPRMIB=Y 场景必须追加状态确认（F186 或 31/28/27 服务），否则无法证明请求生效
2. 正向且 SPRMIB=N 场景预期为 NRC 0x12，无需追加状态确认
3. Delay 步骤不写 check
4. No_Response 只适用于成功且支持 SPRMIB（SPRMIB=Y）的场景

---

### 分类 3: Secure Access Test


#### 用例数量规则

- `Nsecure11` = 需要先解锁才允许执行的 0x11 支持子功能数
- 从参数表 `Access Level` 字段读取安全等级
- **总数 = Nsecure11**
- **始终生成**：即使参数表显示无安全限制（Level0），也要生成用例验证锁定状态下服务可用性

#### 用例命名规则

`Security access Lx unlock supports 0x11 service 0x<Sub> subfunction`
- 示例：`Security access L2 unlock supports 0x11 service 0x01 subfunction`

#### 测试步骤模板

```
1. 进入允许安全访问的会话（通常 Extended）
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
3. Send Security Right KeyBy[Physical]Level[<KeySub>];
4. Send DiagBy[Physical]Data[11 <Sub>];
5. Delay[1000]ms;
```

#### Check 规则

- 第 1 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
  - **必须将 `<P2_H> <P2_L> <P2*_H> <P2*_L>` 替换为从参数表 `Timing parameters` 提取的具体 hex 值**，禁止使用省略号 `...` 代替
- 第 2 步：不单独写 Expected Output（AndCheckResp 已内含检查）
- 第 3 步：`Check DiagData[67 <KeySub>]Within[50]ms;`
- 第 4 步：
  - reset_time Support = N：`Check DiagData[51 <Sub>]Within[50]ms;`
  - reset_time Support = Y：`Check DiagData[51 <Sub> <ResetTime_H> <ResetTime_L>]Within[50]ms;`
- 第 5 步：Delay 不写 check

#### 特殊规则

1. 安全等级不写死，必须从参数表所在软件域的 Access Level 读取
2. SeedSub/KeySub 对应关系：L2 → 27 03/27 04，L4 → 27 07/27 08，其它等级按参数表映射
3. 安全访问步骤统一使用物理寻址

---

### 分类 4: Reset Effect Test（客户扩展）

> 此分类为客户企业内控项，验证 0x11 执行后 ECU 相关运行状态是否被 reset 回初始值。

#### 用例数量规则

设 `Ns` = 支持并可正向执行的 0x11 reset 子功能数，则：

| 子类 | 数量 | 条件 |
|------|------|------|
| Service Reset | Ns | 始终生成 |
| Security Access Reset | Ns | 安全访问存在时生成 |
| Communication Control State Reset | Ns | 0x28 服务支持时生成 |
| Fault Control State Reset | Ns | 0x85/0x14/0x19 支持时生成 |

**总数 = Ns × (1 + I(sec) + I(comm) + I(fault))**

#### 命名规则

- Service Reset：`0x11 Service 0x<Sub> subfunction non-Default Session to Default Session`
- Security Access Reset：`0x11 Service 0x<Sub> subfunction Security access reset`
- Communication Control State Reset：`0x11 Service 0x<Sub> subfunction communication control state reset`
- Fault Control State Reset：`0x11 Service 0x<Sub> subfunction fault control state reset`

#### 各子类步骤与 Check

##### A. Service Reset

**步骤：**
```
1. 进入非默认会话（Extended）
2. Send DiagBy[Physical]Data[11 <Sub>];
3. Delay[1000]ms;
4. 验证会话回到 Default（见下方验证方式）
```

**Check：**
- 第 2 步：`Check DiagData[51 <Sub>]Within[50]ms;`
- 第 4 步：验证回到默认会话（按优先级选择）：
  1. 若支持 DID F186：`Send DiagBy[Physical]Data[22 F1 86];` → `Check DiagData[62 F1 86 01]Within[50]ms;`
  2. 若不支持 F186：`Send DiagBy[Physical]Data[31 01 02 03];` → `Check DiagData[7F 31 7F]Within[50]ms;`

##### B. Security Access Reset

**步骤：**
```
1. 进入允许安全访问的会话（Extended）
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
3. Send Security Right KeyBy[Physical]Level[<KeySub>];
4. Send DiagBy[Physical]Data[11 <Sub>];
5. Delay[1000]ms;
6. 验证会话回到 Default（见下方验证方式）
7. Send DiagBy[Physical]Data[27 <SeedSub>];
```

**Check：**
- 第 3 步：`Check DiagData[67 <KeySub>]Within[50]ms;`
- 第 4 步：`Check DiagData[51 <Sub>]Within[50]ms;`
- 第 6 步：验证回到默认会话（同 A）
- 第 7 步：`Check DiagData[7F 27 7F]Within[50]ms;`（验证已恢复锁定态）

##### C. Communication Control State Reset

**步骤：**
```
1. 进入非默认会话（Extended）
2. Send DiagBy[Physical]Data[28 01 01];
3. Check MsgInexist[<MonitoredMsgId>];
4. Send DiagBy[Physical]Data[11 <Sub>];
5. Delay[1000]ms;
6. Check MsgExist[<MonitoredMsgId>];
7. 验证会话回到 Default（同 A）
```

**Check：**
- 第 2 步：`Check DiagData[68 01]Within[50]ms;`
- 第 4 步：`Check DiagData[51 <Sub>]Within[50]ms;`
- 第 7 步：验证回到默认会话（同 A）
- MonitoredMsgId 默认使用 0x21F（可配置）

##### D. Fault Control State Reset

**步骤：**
```
1. 进入非默认会话（Extended）
2. Send DiagBy[Physical]Data[85 02 FF FF FF];
3. Send DiagBy[Physical]Data[14 FF FF FF];
4. Set Voltage[6.8]V;
5. Delay[3000]ms;
6. Send DiagBy[Physical]Data[19 02 FF];
7. Send DiagBy[Physical]Data[11 <Sub>];
8. Delay[1000]ms;
9. Send DiagBy[Physical]Data[19 02 FF];
10. Set Voltage[12]V;
```

**Check：**
- 第 2 步：`Check DiagData[C5 02]Within[50]ms;`
- 第 3 步：`Check DiagData[54]Within[50]ms;`
- 第 6 步：检查复位前 DTC 状态
- 第 7 步：`Check DiagData[51 <Sub>]Within[50]ms;`
- 第 9 步：检查复位后 fault control 状态是否恢复

> 此子类为强客户化模板，严格按 K 列或项目确认脚本生成。

---

### 分类 5: Sub-function Traversal Test


#### 用例数量规则

**固定 3 条**，覆盖所有可达会话：
1. Default Session — 遍历非法子功能
2. Programming Session — 遍历非法子功能
3. Extended Session — 遍历非法子功能

#### 用例命名规则

`Subfunction traversal test in the <CurrentSessionName> Session`

#### 测试步骤模板

**物理寻址：**
```
1. 进入 <CurrentSession>
2. Send SubTraversalBy[Physical]Service[0x11]Excluding[<SupportSubList>]AndCheckResp[<RespCode>];
```

**功能寻址：**
```
1. 进入 <CurrentSession>
2. Send SubTraversalBy[Function]Service[0x11]Excluding[<SupportSubList>]AndCheckResp[NoResponse];
```

其中：
- `<SupportSubList>` = 支持的子功能 + 支持 SPRMIB 的镜像子功能
  - 示例：若支持 01、03 且都支持 SPRMIB，则 Excluding 填 `01 03 81 83`

#### Check 规则

- 第 1 步：检查进入当前会话的正响应
- 第 2 步：不单独写 Expected Output（AndCheckResp 已内含检查）
  - **物理寻址**：
    - Default 场景：`<RespCode>` 取 `0x7E`
    - Extended 场景：`<RespCode>` 取 `0x12`
  - **功能寻址**：`AndCheckResp` 统一取 `NoResponse`（NRC 0x12 在功能寻址下被屏蔽）

#### 特殊规则

1. Traversal 要区分"服务在当前会话是否有效"与"子功能本身是否有效"
2. 不要把 Session Layer 中已覆盖的"支持但当前会话不允许"的子功能混到 traversal

---

### 分类 6: Incorrect Diagnostic Command & NRC Priority Test

#### 用例数量规则

**DLC 错误用例 + NRC 优先级链验证用例**

**A. DLC 错误（固定 2 条 / 每种支持的寻址方式）：**

| 序号 | 错误类型 | 描述 |
|------|---------|------|
| 1 | DLC < 8 | CAN 帧 DLC 不足 8 字节 |
| 2 | DLC > 8 | CAN 帧 DLC 超过 8 字节 |

**B. NRC 优先级验证（NRC 优先级链中相邻 NRC 对的数量 / 物理寻址 + 功能寻址）：**

每个相邻 NRC 对生成 1 条用例。例如链 `13>12>7E>22` 有 3 对，生成 3 条：
- 验证 `13(min Size) > 12`：SF_DL 不满足最小长度 + 不支持子功能 → 返回 NRC 0x13
- 验证 `12 > 13(no min size)`：SF_DL > 2 但子功能不支持 → 返回 NRC 0x12
- 验证 `7E > 22`：在当前会话不支持该子功能时请求 → 返回 NRC 0x7E

> 物理寻址和功能寻址均生成 NRC Priority 用例。功能寻址下 NRC 0x12 被屏蔽，预期为 `Check No_Response`；其他 NRC 正常返回。

**C. 前置条件测试（车速等）：**

若项目存在车速等前置条件限制（从参数表读取），需增加 1 条：
- 用 `Change MsgID[<SpeedMsg>]Data[<ZeroSpeedData>]CycleTime[<Cycle>]ms;` 设置车速为 0
- 发送 0x11 请求 → 预期 `Check DiagData[7F 11 22]Within[50]ms;`

#### 用例命名规则

**DLC 错误：**
1. `When a diagnostic message with DLC < 8 is sent, ECU does not respond`
2. `When a diagnostic message with DLC > 8 is sent, ECU responds normally`

**NRC 优先级：**
`NRC <优先级链对>` — 例如 `NRC 13(min Size)>12`、`NRC 12>13(no min size)`

**前置条件：**
`When the preset speed condition is not met, NRC: 0x22 is reported`

#### 测试步骤模板

**前置步骤（所有用例共用）：**
进入支持 0x11 的当前会话（通常 Extended）

**A. DLC < 8**
```
Send Msg[<ReqCANID>]Data[02 11 <RepSub>]WithDLC[7];
```

**B. DLC > 8**
```
Send Msg[<ReqCANID>]Data[02 11 <RepSub>]WithDLC[9];
```

**C. NRC 优先级验证（以链 `13>12>7E>22` 为例）**

**用例 1：验证 `13(min Size) > 12`**
1. 进入 Default Session
2. `Send Msg[<ReqCANID>]Data[01 11 <UnsupportedSub>]WithDLC[8];`（SF_DL=1，不满足最小长度 + 不支持子功能）
3. 预期（物理寻址）：`Check DiagData[7F 11 13]Within[50]ms;`
4. 预期（功能寻址）：`Check DiagData[7F 11 13]Within[50]ms;`（NRC 0x13 不被屏蔽）

**用例 2：验证 `12 > 13(no min size)`**
1. 进入 Default Session
2. `Send Msg[<ReqCANID>]Data[03 11 <UnsupportedSub>]WithDLC[8];`（SF_DL=3，满足最小长度但子功能不支持）
3. 预期（物理寻址）：`Check DiagData[7F 11 12]Within[50]ms;`
4. 预期（功能寻址）：`Check No_Response Within[1000]ms;`（NRC 0x12 被功能寻址屏蔽）

**用例 3：验证 `7E > 22`**
1. 进入不支持该子功能的会话
2. `Send DiagBy[<Addr>]Data[11 <SupportedSubButNotInSession>];`
3. 预期：`Check DiagData[7F 11 7E]Within[50]ms;`

**D. 前置条件验证（车速示例）**

1. 进入 Default Session
2. `Change MsgID[<SpeedMsg>]Data[<ZeroSpeedData>]CycleTime[100]ms;`
3. `Send Msg[<ReqCANID>]Data[02 11 <RepSub>]WithDLC[8];`
4. 预期：`Check DiagData[7F 11 22]Within[50]ms;`

#### Check 规则

| 错误类型 | Expected Output |
|---------|----------------|
| DLC < 8 | `Check No_Response Within[1000]ms;` |
| DLC > 8 | `Check DiagData[51 <RepSub> [resetTime]]Within[50]ms;` |
| NRC 优先级 | 每条用例验证一对相邻 NRC，同时触发两个条件时返回优先级更高的 NRC |

#### 特殊规则

1. 0x11 的合法 SF_DL 为 2 字节数据负载（SID + Subfunction）
2. DLC 错误测试使用 `Send Msg...WithDLC[...]`
3. SF_DL 错误（WithLen）已合并到 NRC Priority 验证中，不再单独生成
4. NRC 优先级链中有 N 对相邻 NRC，就生成 N 条用例
5. **物理寻址和功能寻址均生成 NRC Priority 用例**；功能寻址下 NRC 0x12 预期改为 `No_Response`
6. 若项目有车速等前置条件限制，额外生成前置条件 NRC 0x22 验证用例

---

### 分类 7: Functional Addressing Test

#### 用例数量规则

**仅当参数表 `Functional Request = 不支持` 时生成，固定 3 条：**
- 对标准子功能 {01, 02, 03} 各 1 条

若 `Functional Request = 支持`，则不使用本分类，改为像 0x10 一样复制 Session/SPRMIB/Traversal/Incorrect 的 Functional 版本（见下方"功能寻址用例生成规则"）。

#### 用例命名规则

`0x11 Service nonsupport functional addressing subfunction 0x<Sub>`
- 示例：`0x11 Service nonsupport functional addressing subfunction 0x01`

#### 测试步骤模板

```
1. 进入 Extended 会话（使用 Physical）
2. Send DiagBy[Function]Data[11 <Sub>];
3. Delay[1000]ms;
```

#### Check 规则

| 子功能 | Expected Output |
|--------|----------------|
| 11 01 | `Check No_Response Within[1000]ms;` |
| 11 02 | `Check No_Response Within[1000]ms;` |
| 11 03 | `Check No_Response Within[1000]ms;` |

> **功能寻址 NRC 0x12 屏蔽规则**：若 ECU 本应返回 NRC 0x12（Subfunction Not Supported），在功能寻址下该 NRC 被屏蔽，ECU 不回复，预期为 `Check No_Response Within[1000]ms;`。

#### 特殊规则

1. 本分类仅在 `Functional Request = 不支持` 时生成
2. 功能寻址下所有子功能均预期为 No_Response（NRC 0x12 被屏蔽）

---

## 功能寻址用例生成规则

当 `Functional Request = 支持` 时：
1. 将所有 Physical 用例复制一份（Session Layer + SPRMIB + Secure Access + Reset Effect + Traversal + Incorrect Diag Command）
2. 发送函数中 `[Physical]` 改为 `[Function]`
3. Case ID 中 `Phy` 改为 `Fun`，编号重新从 001 开始
4. 安全访问步骤（0x27 seed/key）仍使用 Physical
5. 复位后验证步骤仍使用 Physical
6. **Functional 寻址下正向 0x11 hardReset 预期为 `No_Response`**
7. **功能寻址 NRC 0x12 屏蔽规则**：若 ECU 本应返回 NRC 0x12，在功能寻址下该 NRC 被屏蔽，预期为 `Check No_Response Within[1000]ms;`。其他 NRC（如 0x7E、0x22、0x13）在功能寻址下仍正常返回
8. 功能寻址也生成 NRC Priority 用例，其中 NRC 0x12 预期改为 `Check No_Response`

当 `Functional Request = 不支持` 时：
- 仅生成分类 7（Functional Addressing Test）的 3 条锁定行为验证用例

---

## BootLoader 域规则

当软件域为 BootLoader 时：
1. 从参数表 `Supported Session in BootLoader` 读取会话支持矩阵
2. 从参数表 BootLoader 部分读取 Access Level
3. 用例命名和分类标题加 Boot 标识：`--Boot Session`
4. 规则与 App 相同，仅参数来源不同
5. **Boot 域也必须生成 Functional 用例**（当 Functional=Y 时）
6. Boot 域安全访问使用对应的 Seed/Key（通常是 27 11/27 12 即 LevelFBL）

> **重要**：Boot 域的会话支持矩阵必须从参数表精确读取，不要假设与 App 域一致。Boot 域可能和 App 域的会话支持矩阵完全不同（例如 Boot Extended 支持 0x11 而 App 不支持，或 Boot 仅支持部分子功能）。所有用例生成必须基于 Boot 域自己的参数，而非套用 App 域的规则。

---

## 生成注意事项

1. **Case ID 不可重复**，物理寻址 `Diag_0x11_Phy_001` 起递增，功能寻址 `Diag_0x11_Fun_001` 起递增
2. **编号从 001 开始**，优先编写所有 Physical 用例，再编写 Functional 用例
3. **每个 Send 都要有对应 Check**，除以下豁免：
   - `Delay[...]ms` 不写 Check
   - 带 `AndCheckResp[...]` 的发送函数不单独写 Check
   - `Check MsgInexist[...]` / `Check MsgExist[...]` 本身就是检查，不再重复
4. **步骤和 Check 的编号必须对应**
5. **不可省略任何分类**，所有分类必须全部生成（条件不满足的标明"无符合条件的用例"）
6. **输出格式严格为 pipe table**，列顺序：`| Case ID | Case名称 | 测试步骤 | 预期输出 |`
7. **步骤中换行使用 `<br>` 标记**，不用 `\n`
8. **NRC 优先级链从参数表精确读取**，不要猜测
9. **不要生成任何"参数提取结果"或"分析"段落**，直接输出测试用例表格
10. **进入 Programming 会话前必须先执行扩展会话,例如 `[10 03]`
11. **禁止在预期输出中使用省略号 `...`**：所有 hex 参数必须从参数表提取具体值后填入。例如 `[50 03 ...]` 是错误的，必须写为 `[50 03 00 32 01 F4]`（以参数表实际值为准）。又如 `[50 01 ...]` 必须写为 `[50 01 00 32 01 F4]`。

## Timing 参数提取规则

从参数表精确提取：
- P2 Server Max → 直接读取 ms 值，hex 编码公式：`P2ms / 1` → 转为 2 字节 hex
- P2* Server Max → hex 编码公式：`P2*ms / 10` → 转为 2 字节 hex
- 示例：P2=50ms → 50=0x0032 → `00 32`；P2*=5000ms → 500=0x01F4 → `01 F4`
- **正响应 Timing Bytes 用于 0x10 Session 切换响应**（`50 <Sub> 00 32 01 F4`），不直接用于 0x11 正响应

## 会话进入标准路径

| 目标会话 | 标准进入步骤 |
|---------|------------|
| Default（0x01） | `Send DiagBy[Physical]Data[10 01];` |
| Extended（0x03） | `Send DiagBy[Physical]Data[10 01];` → `Delay[1000]ms;` → `Send DiagBy[Physical]Data[10 03];` |
| Programming（0x02） | `Send DiagBy[Physical]Data[10 01];` → `Delay[1000]ms;` → `Send DiagBy[Physical]Data[10 03];` → `Send DiagBy[Physical]Data[31 01 02 03];` → `Send DiagBy[Physical]Data[10 02];` |

**重要**：进入 Programming 会话前必须先执行 RoutineControl（如 `31 01 02 03`）。

**31 服务（RoutineControl）正响应格式**：
- 请求 `31 01 02 03` → 正响应 `71 01 02 03 00`（5 字节，最后 1 字节为 routineStatus）
- **不要遗漏最后的状态字节 `00`**

### 会话进入展开规则（强制）

**会话进入必须展开为独立编号步骤，严禁使用描述性语句。**

> **禁止示例**（错误）：`1.按照01进03，03进02的顺序进入Programming会话`
> **禁止示例**（错误）：`1.进入 Extended 会话`
> 必须逐条写出每个 Send / Delay / Check，各自独立编号。

**进入 Extended 会话的正确写法（test_procedure）：**
```
1.Send DiagBy[Physical]Data[10 01];
2.Delay[1000]ms;
3.Send DiagBy[Physical]Data[10 03];
```

**进入 Programming 会话的正确写法（test_procedure）：**
```
1.Send DiagBy[Physical]Data[10 01];
2.Delay[1000]ms;
3.Send DiagBy[Physical]Data[10 03];
4.Delay[1000]ms;
5.Send DiagBy[Physical]Data[10 02];
```

**对应的 expected_output（必须填入从参数表提取的 Timing 参数）：**
```
1.Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;
3.Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;
5.Check DiagData[50 02 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;
```
**`<P2_H> <P2_L> <P2*_H> <P2*_L>` 必须替换为从参数表 `Timing parameters` 提取的 hex 值，严禁使用 `...` 省略号。如果参数为空设置为默认值`[00 32 01 F4]`**
