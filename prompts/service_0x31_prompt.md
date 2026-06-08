# Service 0x31 RoutineControl — 用例生成规则

## 服务概述

- **Service ID**: 0x31
- **Service Name**: RoutineControl
- **子功能**: 01(StartRoutine), 02(StopRoutine), 03(RequestRoutineResults)
- **请求格式**: `31 <Sub> <RID_H> <RID_L> [+ Routine Option 数据]`
- **合法 SF_DL**: 4 + Option 数据长度（最小 4：SID + Sub + RID 2 字节）
- **关键特性**: 每个 RID + 每个 Subfunction 组合原则上各一条用例；正响应含 StatusByte
- **NRC 优先级链（服务级，Figure 0x31 专用）**:

| 优先级 | NRC | 触发条件 |
|--------|-----|---------|
| 1 | 0x13 | 长度错误（最小长度/总长度不匹配） |
| 2 | 0x31 | RID 不支持 |
| 3 | 0x33 | 安全访问未解锁 |
| 4 | 0x12 | SubFunction 对该 RID 不支持 |
| 5 | 0x31 | OptionRecord 数据无效 |
| 6 | 0x22 | 前提条件不满足 |
| 7 | 0x24 | RID 请求序列错误 |
| 8 | 0xXX | 厂商/供应商自定义 |

### 正响应格式

- `71 <Sub> <RID_H> <RID_L> [+ Routine Status / Response 数据]`
- StatusByte 解读需从 RID 的 Response 参数定义中读取
  - 如 CheckProgrammingPreCondition: 0x00=正常, 0x01=异常
  - 如 DimmingControl: 0x00=correct, 0x01=incorrect

---


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


## 生成分类（共 5 类）

按以下固定顺序逐类生成，每个分类使用 `## N.N` 作为标题（如 `## 1.1 Session Layer Test`）。

---

### 分类 1: Session Layer Test

#### 用例数量规则

- `Npos` = 支持的 RID × 支持的 Subfunction × 支持的会话数
- `Nneg_sf` = 不支持的子功能 case 数
- `Nneg_sess` = 不支持的会话 case 数
- **总数 = Npos + Nneg_sf + Nneg_sess**

#### 用例命名规则

- 正向：`<CurrentSessionName> Session support the 0x31 service 0x<Sub> subfunction RID 0x<RID>`
  - 示例：`Extended Session support the 0x31 service 0x01 subfunction RID 0x0200`
- 负向（会话不支持）：`<CurrentSessionName> Session nonsupport 0x31 services`
- 负向（子功能不支持）：`0x31 service RID 0x<RID> nonsupport 0x<Sub> subfunction`

#### 测试步骤模板

**A. 不支持的会话（如 Default）**
```
1. 进入 Default 会话
2. Send DiagBy[Physical]Data[31 <Sub> <RID_H> <RID_L>];
```

**B. 支持会话正向（StartRoutine）**
```
1. 进入支持的会话（通常 Extended）
2. Send DiagBy[Physical]Data[31 01 <RID_H> <RID_L> <OptionData>];
```

**C. 支持会话正向（StopRoutine / RequestRoutineResults）**
```
1. 进入支持的会话
2. Send DiagBy[Physical]Data[31 <Sub> <RID_H> <RID_L>];
```

**D. 子功能不支持**
```
1. 进入支持的会话
2. Send DiagBy[Physical]Data[31 <UnsupportedSub> <RID_H> <RID_L>];
```

#### Check 规则

**A. 不支持的会话：**
- `Check DiagData[7F 31 7F]Within[50]ms;`

**B. 支持会话正向（StartRoutine）：**
- `Check DiagData[71 01 <RID_H> <RID_L> <StatusByte>]Within[50]ms;`
- StatusByte 含义从 RID 定义读取

**C. 支持会话正向（Stop/Results）：**
- `Check DiagData[71 <Sub> <RID_H> <RID_L> [<ResponseData>]]Within[50]ms;`

**D. 子功能不支持：**
- `Check DiagData[7F 31 12]Within[50]ms;`

#### 特殊规则

1. 每个 RID + 每个 Subfunction 组合原则上各一条用例
2. StartRoutine(01) 可能需要附带 Option 数据（如 DimmingControl 的 Level 值）
3. StopRoutine(02) 和 RequestRoutineResults(03) 通常无附加数据
4. OptionData 从 RID 定义表的 Request 参数读取
5. StatusByte 含义从 RID 定义表的 Response 参数读取

---

### 分类 2: Secure Access Test

#### 用例数量规则

- 从参数表 RID 的 `Access Level` 字段读取安全等级
- 仅对需要安全解锁的 RID 生成
- **总数 = N_rid_need_security**

#### 用例命名规则

`Security access Lx unlock supports 0x31 service 0x<Sub> subfunction RID 0x<RID>`
- 示例：`Security access L2 unlock supports 0x31 service 0x01 subfunction RID 0x0200`

#### 测试步骤模板

```
1. 进入支持的会话（通常 Extended）
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PostiveResponse];
3. Send Security Right KeyBy[Physical]Level[<KeySub>];
4. Send DiagBy[Physical]Data[31 <Sub> <RID_H> <RID_L> <OptionData>];
```

#### Check 规则

- 第 3 步：`Check DiagData[67 <KeySub>]Within[50]ms;`
- 第 4 步：`Check DiagData[71 <Sub> <RID_H> <RID_L> <StatusByte>]Within[50]ms;`

---

### 分类 3: Routine Condition Test

#### 用例数量规则

- 仅对有 Routine Condition 或需要特定前置条件的 RID 生成
- 典型场景：

| 场景 | 数量 |
|------|------|
| 电压条件测试 | 2（异常 + 恢复） |
| 编程前置条件测试 | 2（正常 + 异常） |
| 其他条件 | 按条件数 |

#### 用例命名规则

- `RID 0x<RID> routine condition test with <Condition>`
- 示例：`RID 0x0203 CheckProgrammingPreCondition with normal voltage`
- 示例：`RID 0x0203 CheckProgrammingPreCondition with abnormal voltage`

#### 测试步骤模板

**A. 电压条件测试：**
```
1. 进入 Extended 会话
2. 完成安全解锁（若需要）
3. Set Voltage[8.5]V;（异常电压）
4. Delay[1000]ms;
5. Send DiagBy[Physical]Data[31 01 <RID_H> <RID_L>];
6. Set Voltage[12]V;（恢复正常电压）
7. Delay[1000]ms;
8. Send DiagBy[Physical]Data[31 01 <RID_H> <RID_L>];
```

**B. 编程前置条件测试：**
```
1. 进入 Extended 会话
2. 完成安全解锁（若需要）
3. （正常条件下）Send DiagBy[Physical]Data[31 01 <RID_H> <RID_L>];
4. （破坏条件）Send DiagBy[Physical]Data[31 01 <RID_H> <RID_L>];
```

#### Check 规则

**A. 电压条件：**
- 异常电压（第 5 步）：`Check DiagData[71 01 <RID> 01]Within[50]ms;`（status=异常）
- 正常电压（第 8 步）：`Check DiagData[71 01 <RID> 00]Within[50]ms;`（status=正常）

**B. 编程前置条件：**
- 条件满足：`Check DiagData[71 01 <RID> 00]Within[50]ms;`
- 条件不满足：`Check DiagData[71 01 <RID> 01]Within[50]ms;` 或 `Check DiagData[7F 31 22]Within[50]ms;`

#### 特殊规则

1. 异常电压值从 RID 定义的条件读取（典型：8.5V 欠压 或 16.5V 过压）
2. StatusByte 0x00=条件满足/正常, 0x01=条件不满足/异常
3. 编程前置条件 RID（如 CheckProgrammingPreCondition）必须有此测试

---

### 分类 4: Sub-function Traversal And RID Range Test

#### 用例数量规则

**固定 2 条**（子功能遍历 1 + RID 遍历 1）

#### 用例命名规则

- `Subfunction traversal test for 0x31 service RID 0x<RID>`
- `RID range traversal test for 0x31 service`

#### 测试步骤模板

**A. 子功能遍历：**
```
1. 进入 Extended 会话
2. Send SubTraversalBy[Physical]Service[0x31]Excluding[<SupportSubList>]AndCheckResp[0x12];
```
- Excluding 包括支持的子功能 + SPRMIB 镜像

**B. RID 遍历：**
```
1. 进入 Extended 会话
2. Send DIDTraversalBy[Physical]Service[0x31]Excluding[<SupportRIDList>]AndCheckResp[0x31];
```
- Excluding 包括所有支持的 RID

#### Check 规则

- 不支持的子功能 → `7F 31 12`
- 不支持的 RID → `7F 31 31`

---

### 分类 5: Incorrect Diagnostic Command Test

#### 用例数量规则

**固定 4 条**

| 序号 | 错误类型 | 描述 |
|------|---------|------|
| 1 | DLC < 8 | CAN 帧 DLC 不足 8 字节 |
| 2 | DLC > 8 | CAN 帧 DLC 超过 8 字节 |
| 3 | SF_DL > 合法值 | 有效负载长度大于合法值 |
| 4 | SF_DL < 合法值 | 有效负载长度小于合法值 |

注意：0x31 的合法 SF_DL 最小为 4（SID + Sub + RID 2 字节），含 Option 数据时更长。

#### 用例命名规则

1. `When a diagnostic message with DLC < 8 is sent, ECU does not respond`
2. `When a diagnostic message with DLC > 8 is sent, ECU responds normally`
3. `Valid SF_DL=<legal>, invalid SF_DL > <legal> triggers NRC 0x13`
4. `Valid SF_DL=<legal>, invalid SF_DL < <legal> triggers NRC 0x13`

#### 测试步骤模板

选择一个代表性 RID 进行测试。

**前置步骤：** 进入支持 0x31 的当前会话（通常 Extended）

**A. DLC < 8**
```
Send Msg[<ReqCANID>]Data[04 31 01 <RID_H> <RID_L>]WithDLC[7];
```

**B. DLC > 8**
```
Send Msg[<ReqCANID>]Data[04 31 01 <RID_H> <RID_L>]WithDLC[9];
```

**C. SF_DL > 合法值**
```
Send DiagBy[Physical]Data[31 01 <RID_H> <RID_L>]WithLen[5];
```

**D. SF_DL < 合法值**
```
Send DiagBy[Physical]Data[31 01 <RID_H>]WithLen[3];
```

#### Check 规则

| 错误类型 | Expected Output |
|---------|----------------|
| DLC < 8 | `Check No_Response Within[1000]ms;` |
| DLC > 8 | `Check DiagData[71 01 <RID> <Status>]Within[50]ms;` |
| SF_DL 异常 | `Check DiagData[7F 31 13]Within[50]ms;` |

---

## 功能寻址用例生成规则

当 `Functional Request = 支持` 时：
1. 将所有 Physical 用例复制一份
2. 发送函数中 `[Physical]` 改为 `[Function]`
3. Case ID 中 `Phy` 改为 `Fun`，编号重新从 001 开始

当 `Functional Request = 不支持` 时（0x31 典型情况）：
- 仅生成 1 条 No_Response 验证用例

---

## 生成注意事项

1. **RID 列表从 Routine Control 表（Sheet 含 "Routine"/"0x31"）读取**
2. **每个 RID + 每个 Subfunction 组合各一条用例**（除非不支持）
3. **OptionData 从 RID 的 Request 参数定义读取**，StartRoutine 通常需要
4. **StatusByte 含义从 RID 的 Response 参数定义读取**
5. **有前置条件的 RID 必须生成 Condition Test**
