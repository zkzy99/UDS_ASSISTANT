# Service 0x3E TesterPresent — 用例生成规则

## 服务概述

- **Service ID**: 0x3E
- **Service Name**: TesterPresent
- **子功能**: 0x00(ZeroSubFunction)
- **SPRMIB**: 支持 0x80（0x3E 80 → 无响应）
- **请求格式**: `3E 00` 或 `3E 80`
- **合法 SF_DL**: 2 字节
- **关键特性**: 用于维持非默认会话（防止 S3 超时）；支持物理和功能寻址
- **通常在 Default、Extended 和 Programming 会话下都支持**
- **NRC 优先级链（服务级，0x3E 专用）**:

> **关键规则**：以下为 0x3E 服务的**完整** NRC 优先级链模板。实际生成时必须从参数表 `Negative response codes` 字段读取精确的 NRC 列表和顺序，**参数表声明了哪些 NRC 就覆盖哪些**。

| 优先级 | NRC | 触发条件 |
|--------|-----|---------|
| 1 | 0x13 | 长度错误（SF_DL≠2） |
| 2 | 0x11 | 服务不支持（ECU 全局不支持 0x3E 服务时） |
| 3 | 0x7F | 服务在当前会话不支持 |
| 4 | 0x12 | 子功能不支持（非 0x00/0x80） |
| 5 | 0x22 | 前提条件不满足 |

**NRC 全覆盖要求**：参数表 `Negative response codes` 字段中列出的**每一个** NRC 都必须有至少一条专用测试用例。常用覆盖策略：
- **0x13**：Incorrect Diagnostic Command（分类 7）覆盖
- **0x11**：若参数表声明，Session Layer 覆盖（服务不支持）
- **0x7F**：Session Layer 覆盖（当前会话不支持 0x3E 服务）
- **0x12**：Sub-function Traversal（分类 6）+ NRC Priority（分类 8）覆盖
- **0x22**：NRC Priority Test 覆盖（前提条件不满足）

### 正响应格式

- `7E 00`（仅确认，无额外 payload）
- SPRMIB 模式（3E 80）：无响应

---

## 预期输出格式规则（强制）

> **关键规则**：`expected_output` 字段必须使用完整的 `Check` 函数格式，**绝对禁止**使用裸 hex 字节简化格式。

### 两个字段的职责划分

| 字段 | 写什么 | 不写什么 |
|------|--------|---------|
| `test_procedure` | Send / Delay / Set / Change 等**操作** | 不写 Check（Check 放到 expected_output） |
| `expected_output` | Check DiagData / Check No_Response 等**检查** | 不写 Send / Delay / Set |

### expected_output 格式规范

- 每条 Check 必须使用完整函数格式：`N. Check DiagData[<hex_bytes>]Within[<time>]ms;`
- 无响应检查使用：`N. Check No_Response Within[<time>]ms;`
- 序号 `N` 与 `test_procedure` 中对应 Send 步骤的编号一致
- Delay、Set Voltage、已带 `AndCheckResp` 的步骤不在 expected_output 中出现
- 多个 Check 用 `<br>` 分隔

**正确格式示例：**
```
2. Check DiagData[50 03 00 32 01 F4]Within[50]ms;<br>5. Check DiagData[67 06]Within[50]ms;<br>8. Check DiagData[7E 00]Within[50]ms;<br>11. Check DiagData[62 F1 86 03]Within[50]ms;
```

**错误格式示例（禁止）：**
- `2. 50 03 00 32 01 F4<br>5. 67 06` ❌ — 缺少 `Check DiagData[...]Within[50]ms;` 包装
- `Step2: 7E 00` ❌ — 禁止 `StepX:` 前缀 + 缺少 Check 包装
- `2.No_Response` ❌ — 必须使用完整格式 `2. Check No_Response Within[1000]ms;`
- `2.Check DiagData[50 03...]` ❌ — 序号与内容之间必须有空格（如 `2. Check...`）

---

## 生成分类（共 9 类）

按以下固定顺序逐类生成，每个分类使用 `## N.N` 作为标题（如 `## 1.1 Session Layer Test`）。

---

### 分类 1: Session Layer Test (APP)

#### 用例数量规则

- 对每个支持的会话（Default、Extended、Programming）各 1 条
- **总数 = Nsupported_sessions**（通常 3 条）

#### 用例命名规则

- `<CurrentSessionName> Session support the 0x3E service 1Case-$3E`
  - 示例：`Default Session support the 0x3E service 1Case-$3E`
  - 示例：`Extended Session support the 0x3E service 1Case-$3E`
  - 示例：`Programming Session support the 0x3E service 1Case-$3E`

#### 测试步骤模板

**Default Session：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[3E 00];
```

**Extended Session：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Send DiagBy[Physical]Data[3E 00];
```

**Programming Session：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Send DiagBy[Physical]Data[31 01 02 03];
3. Send DiagBy[Physical]Data[10 02];
4. Send DiagBy[Physical]Data[3E 00];
```

#### Check 规则

- 第 2/4 步：`Check DiagData[7E 00]Within[50]ms;`

---

### 分类 2: SPRMIB Test (APP)

#### 用例数量规则

- 对每个支持的会话各 1 条
- **总数 = Nsupported_sessions**（通常 3 条）

#### 用例命名规则

- `<CurrentSessionName> Session support the 0x3E service with SPRMIB 1Case-$3E`

#### 测试步骤模板

**Default Session：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[3E 80];
```

**Extended Session：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Send DiagBy[Physical]Data[3E 80];
```

**Programming Session：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Send DiagBy[Physical]Data[31 01 02 03];
3. Send DiagBy[Physical]Data[10 02];
4. Send DiagBy[Physical]Data[3E 80];
```

#### Check 规则

- `Check No_Response Within[1000]ms;`

---

### 分类 3: Secure Access Test (APP)

#### 用例数量规则

**固定 2 条**（3E 00 和 3E 80 各 1 条）

#### 用例命名规则

`0x3E service keeps the 0x27 service unlocked state 1Case-$3E`

#### 测试步骤模板

**A. 3E 00 维持安全状态：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Send DiagBy[Physical]Data[27 01]AndCheckResp[1];
3. Send Security Right KeyBy[Physical]Level[0x2];
4. Delay[1000]ms;
5. Send DiagBy[Physical]Data[3E 00];
6. Delay[<S3 - delta>]ms;（如 4900ms）
7. Send DiagBy[Physical]Data[22 F1 86];
```

**B. 3E 80 维持安全状态：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Send DiagBy[Physical]Data[27 01]AndCheckResp[1];
3. Send Security Right KeyBy[Physical]Level[0x2];
4. Delay[1000]ms;
5. Send DiagBy[Physical]Data[3E 80];
6. Delay[<S3 - delta>]ms;（如 4900ms）
7. Send DiagBy[Physical]Data[22 F1 86];
```

#### Check 规则

**A. 3E 00：**
- 第 3 步：`Check DiagData[67 02]Within[50]ms;`
- 第 5 步：`Check DiagData[7E 00]Within[50]ms;`
- 第 7 步：`Check DiagData[62 F1 86 03]Within[50]ms;`（会话仍为 Extended）

**B. 3E 80：**
- 第 3 步：`Check DiagData[67 02]Within[50]ms;`
- 第 5 步：`Check No_Response Within[50]ms;`
- 第 7 步：`Check DiagData[62 F1 86 03]Within[50]ms;`（会话仍为 Extended）

#### 特殊规则

1. 验证 0x3E TesterPresent 能维持安全解锁状态
2. S3 - delta 使用边界值 4900ms（S3=5000ms 时）
3. 验证方式：延时后读取 DID F186（Active Diagnostic Session），确认仍为 Extended

---

### 分类 4: S3 Server Timer Test (APP)

#### 用例数量规则

**固定 4 条**，使用边界值测试

| 序号 | 场景 | 描述 |
|------|------|------|
| 1 | S3=4900ms（有效） + 3E 00 | 延时 4900ms 后发送 3E 00，会话保持 Extended |
| 2 | S3=5100ms（无效） + 3E 00 | 延时 5100ms 后发送 3E 00，会话回退 Default |
| 3 | S3=4900ms（有效） + 3E 80 | SPRMIB 版本，会话保持 Extended |
| 4 | S3=5100ms（无效） + 3E 80 | SPRMIB 版本，会话回退 Default |

#### 用例命名规则

1. `Valid equivalence class S3server=4900ms,0x3E service keeping extended Session 1Case-$3E`
2. `Invalid equivalence class S3server=5100ms,0x3E service does not keeping extended Session NegativeCase-$3E`
3. `Valid equivalence class S3server=4900ms,0x3E service with SPRMIB keeping extended Session 1Case-$3E`
4. `Invalid equivalence class S3server=5100ms,0x3E service with SPRMIB does not keeping extended Session NegativeCase-$3E`

#### 测试步骤模板

**场景 1: S3=4900ms + 3E 00**
```
1. Send DiagBy[Physical]Data[10 03];
2. Delay[1000]ms;
3. Send DiagBy[Physical]Data[3E 00];
4. Delay[4900]ms;
5. Send DiagBy[Physical]Data[22 F1 86];
```

**场景 2: S3=5100ms + 3E 00**
```
1. Send DiagBy[Physical]Data[10 03];
2. Delay[1000]ms;
3. Send DiagBy[Physical]Data[3E 00];
4. Delay[5100]ms;
5. Send DiagBy[Physical]Data[22 F1 86];
```

**场景 3/4: SPRMIB 版本，同上但用 3E 80**

#### Check 规则

**场景 1（有效）：**
- 第 3 步：`Check DiagData[7E 00]Within[50]ms;`
- 第 5 步：`Check DiagData[62 F1 86 03]Within[50]ms;`（仍为 Extended）

**场景 2（无效）：**
- 第 3 步：`Check DiagData[7E 00]Within[50]ms;`
- 第 5 步：`Check DiagData[62 F1 86 01]Within[50]ms;`（已回 Default）

**场景 3（SPRMIB 有效）：**
- 第 3 步：`Check No_Response Within[50]ms;`
- 第 5 步：`Check DiagData[62 F1 86 03]Within[50]ms;`

**场景 4（SPRMIB 无效）：**
- 第 3 步：`Check No_Response Within[50]ms;`
- 第 5 步：`Check DiagData[62 F1 86 01]Within[50]ms;`

#### 特殊规则

1. **使用边界值**：有效=4900ms（S3-100ms），无效=5100ms（S3+100ms）
2. S3 时间从参数表 `S3 Server Time` 读取，边界值按 S3±100ms 计算
3. F1 86 = Active Diagnostic Session DID：01=Default, 03=Extended
4. 0x3E 在延时前发送一次，然后等待延时结束验证会话状态

---

### 分类 5: ECU Reset Test (APP)

#### 用例数量规则

**固定 3 条**

| 复位方式 | 数量 |
|---------|------|
| Power Reset | 1 |
| Hardware Reset(11 01) | 1 |
| Session Switch（10 01） | 1 |

#### 用例命名规则

`<ResetType> the 0x3E service to keep the Session back from the extended Session to the default Session NegativeCase-$3E`

#### 测试步骤模板

**A. Power Reset：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Delay[1000]ms;
3. Send DiagBy[Physical]Data[3E 00];
4. Delay[1000]ms;
5. Set Voltage[0]V;
6. Delay[1000]ms;
7. Set Voltage[12]V;
8. Delay[1000]ms;
9. Send DiagBy[Physical]Data[22 F1 86];
```

**B. Hardware Reset(11 01)：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Delay[1000]ms;
3. Send DiagBy[Physical]Data[3E 00];
4. Delay[1000]ms;
5. Send DiagBy[Physical]Data[11 01];
6. Delay[1000]ms;
7. Send DiagBy[Physical]Data[22 F1 86];
```

**C. Session Switch（10 01）：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Delay[1000]ms;
3. Send DiagBy[Physical]Data[3E 00];
4. Delay[1000]ms;
5. Send DiagBy[Physical]Data[10 01];
6. Delay[1000]ms;
7. Send DiagBy[Physical]Data[22 F1 86];
```

#### Check 规则

- 第 3 步：`Check DiagData[7E 00]Within[50]ms;`（3E 响应）
- 最后一步：`Check DiagData[62 F1 86 01]Within[50]ms;`（复位后回到 Default）

---

### 分类 6: Sub-function Traversal Test (APP)

#### 用例数量规则

**固定 1 条**

#### 用例命名规则

`0x3E service Subfunction traversal test NegativeCase-$3E`

#### 测试步骤模板

```
1. 进入支持的会话（Extended）
2. Send SubTraversalBy[Physical]Service[0x3E]Excluding[00 80]AndCheckResp[0x12];
```

#### Check 规则

- 第 2 步：不支持的子功能 → `7F 3E 12`

---

### 分类 7: Incorrect Diagnostic Command Test (APP)

#### 用例数量规则

**固定 2 条**

| 序号 | 错误类型 | 描述 |
|------|---------|------|
| 1 | SF_DL > 2 | 有效负载长度大于合法值 |
| 2 | SF_DL < 2 | 有效负载长度小于合法值 |

#### 用例命名规则

1. `Valid SF_DL=2, invalid SF_DL > 2, and those with invalid equivalence class SF_DL=3 NegativeCase-$3E`
2. `Valid SF_DL=2, invalid SF_DL < 2, and those with invalid equivalence class SF_DL=1 NegativeCase-$3E`

#### 测试步骤模板

**A. SF_DL > 2**
```
Send DiagBy[Physical]Data[3E 00]WithLen[3];
```

**B. SF_DL < 2**
```
Send DiagBy[Physical]Data[3E 00]WithLen[1];
```

#### Check 规则

| 错误类型 | Expected Output |
|---------|----------------|
| SF_DL > 2 | `Check DiagData[7F 3E 13]Within[50]ms;` |
| SF_DL < 2 | `Check DiagData[7F 3E 13]Within[50]ms;` |

---

### 分类 8: NRC Priority Test (APP)

#### 用例数量规则

- **【强制】NRC 全量覆盖**：优先级链必须包含参数表 `Negative response codes` 字段声明的**所有 NRC**。每个已声明的 NRC 必须至少有一条专用用例覆盖。
- **固定 2 条** + 参数表额外声明的 NRC 覆盖用例

| 序号 | 场景 | 描述 |
|------|------|------|
| 1 | NRC 13 > 12 | 发送长度错误的 0x3E，验证返回 0x13 |
| 2 | NRC 12 | 发送不支持的子功能，验证返回 0x12 |

#### 用例命名规则

1. `NRC 13>12>22 NegativeCase-$3E`
2. `NRC 12 NegativeCase-$3E`

#### 测试步骤

**用例 1（NRC 13 优先）：**
```
1. Send DiagBy[Physical]Data[3E 01]WithLen[1];
```
预期：`Check DiagData[7F 3E 13]Within[50]ms;`

**用例 2（NRC 12）：**
```
1. Send DiagBy[Physical]Data[3E 0A];
```
预期：`Check DiagData[7F 3E 12]Within[50]ms;`

**NRC 0x11 专用覆盖（若参数表声明）：**
```
1. 进入不支持 0x3E 服务的会话，发送 3E 00
```
预期：`Check DiagData[7F 3E 11]Within[50]ms;`

**NRC 0x7F 专用覆盖（若参数表声明）：**
```
1. 进入不支持 0x3E 服务的当前会话，发送 3E 00
```
预期：`Check DiagData[7F 3E 7F]Within[50]ms;`

**NRC 0x22 专用覆盖（若参数表声明）：**
```
1. 在前提条件不满足时发送 3E 00
```
预期：`Check DiagData[7F 3E 22]Within[50]ms;`

#### Check 规则

- 每条用例验证一对相邻 NRC 的优先级关系或独立 NRC 触发

---

### 分类 9: Boot Domain Test

Boot 域生成与 APP 域完全相同结构的测试集，但有以下差异：

#### Boot 域差异

| 项目 | APP 域 | Boot 域 |
|------|--------|---------|
| 会话进入路径 | `10 03` 直接进入 Extended | `10 03 → 31 01 02 03 → 10 02` 进入 Programming |
| 安全等级 | L1（27 01 / 27 02） | LevelFBL（27 11 / 27 12） |
| S3 验证方式 | `22 F1 86`（读 DID） | `31 01 FF 01`（RoutineControl） |
| 会话验证值 | `62 F1 86 03`（Extended） | `71 01 FF 01 00`（正响应）或 `7F 31 31`（负响应） |

#### Boot 域子分类（与 APP 域完全对应）

Boot 域按以下顺序生成，每个子分类与 APP 域结构相同：

1. **Boot Physical - Session Layer**: Default/Programming/Extended 各 1 条
2. **Boot Physical - SPRMIB**: Default/Programming/Extended 各 1 条
3. **Boot Physical - Secure Access**: 使用 LevelFBL（27 11/12），在 Programming 会话下
4. **Boot Physical - S3 Timer**: 使用 `31 01 FF 01` 验证，边界值 4900ms/5100ms
5. **Boot Physical - ECU Reset**: Power Reset / HardReset / Session Switch
6. **Boot Physical - Sub-function Traversal**: 同 APP
7. **Boot Physical - Incorrect Command**: 同 APP（2 条 SF_DL）
8. **Boot Physical - NRC Priority**: 同 APP（2 条）
9. **Boot Functional**: Physical 的完整镜像，所有输出为 `Check No_Response Within[1000]ms;`

#### Boot Secure Access 测试步骤模板

```
1. Send DiagBy[Physical]Data[10 03];
2. Send DiagBy[Physical]Data[31 01 02 03];
3. Send DiagBy[Physical]Data[10 02];
4. Send DiagBy[Physical]Data[27 11]AndCheckResp[1];
5. Send Security Right KeyBy[Physical]Level[0x12];
6. Delay[1000]ms;
7. Send DiagBy[Physical]Data[3E 00];（或 3E 80）
```

#### Boot S3 Timer 测试步骤模板

```
1. Send DiagBy[Physical]Data[10 03];
2. Send DiagBy[Physical]Data[31 01 02 03];
3. Send DiagBy[Physical]Data[10 02];
4. Send DiagBy[Physical]Data[27 11]AndCheckResp[1];
5. Send Security Right KeyBy[Physical]Level[0x12];
6. Delay[1000]ms;
7. Send DiagBy[Physical]Data[3E 00];（或 3E 80）
8. Delay[4900]ms;（或 5100ms）
9. Send DiagBy[Physical]Data[31 01 FF 01];
```

#### Boot S3 Timer Check 规则

**有效（4900ms）：**
- 第 9 步：`Check DiagData[71 01 FF 01 00]Within[50]ms;`（仍在 Programming）

**无效（5100ms）：**
- 第 9 步：`Check DiagData[7F 31 31]Within[50]ms;`（已退出 Programming）

---

## 生成注意事项

1. **0x3E 通常在 Default、Extended 和 Programming 会话下都支持**，具体支持哪些会话必须从参数表 `Diagnostic Services` 中 0x3E 条目的 `Supported Session` 字段精确读取
2. **S3 时间从参数表读取**，边界值按 S3±100ms 计算（如 S3=5000ms → 有效 4900ms，无效 5100ms）
3. **【强制】DID F1 86（Active Diagnostic Session）用于 APP 域读取当前会话号**，该 DID **必须存在于参数表 DID 表中**才可使用。若 DID 表中不存在 F1 86，则 APP 域 S3 Timer、ECU Reset、Secure Access 等依赖该 DID 的测试步骤**必须跳过**，改用其他可从参数表获取的方式验证会话状态（如发送 0x22 读取参数表中已存在的某个代表性 DID，或仅依赖 0x3E 自身响应判断）
4. **【强制】Boot 域使用 `31 01 FF 01`（RID 0xFF01）验证会话状态**，该 RID **必须存在于参数表 Routine Control 表中**才可使用。若 Routine Control 表中不存在 RID 0xFF01，则 Boot 域 S3 Timer、ECU Reset、Secure Access 等依赖该 RID 的测试步骤**必须跳过**，改用其他可从参数表获取的方式验证
5. **【强制】绝对禁止使用参数表中未声明的 DID/RID 发送请求并设置预期响应**。所有跨服务引用的标识符（如 0x3E 用例中使用的 0x22 读取 DID、0x31 调用 RID）必须从对应参数表（DID 表、Routine Control 表）中验证存在性
6. **Boot 域安全等级为 LevelFBL（27 11/27 12）**，不同于 APP 域的 L1（27 01/27 02），安全等级必须从参数表 `0x27 Security Access` 表读取确认
7. **SPRMIB (3E 80) 无响应但仍刷新 S3**
8. **若用于验证的 DID/RID 在参数表中不存在**，相关分类直接输出 `> 无符合条件的用例（参数表中无 F1 86 DID / FF 01 RID）。` 并跳过该分类
9. **【强制】NRC 全量覆盖自检**：生成完所有用例后，必须逐一核对参数表 `Negative response codes` 字段声明的每一个 NRC（0x11、0x7F、0x13、0x12、0x22 等）是否都有至少一条专用测试用例。漏掉任何一个已声明 NRC 均为不合格输出。

---

## 分类汇总

| 分类 | 描述 | APP Physical | APP Functional | Boot Physical | Boot Functional |
|------|------|-------------|---------------|--------------|----------------|
| 1. Session Layer | 各会话测试 | 3 | 3 | 3 | 3 |
| 2. SPRMIB | 各会话 SPRMIB | 3 | 3 | 3 | 3 |
| 3. Secure Access | 维持 0x27 解锁 | 2 | 2 | 2 | 2 |
| 4. S3 Timer | 边界值测试 | 4 | 4 | 4 | 4 |
| 5. ECU Reset | 复位后状态 | 3 | 3 | 3 | 3 |
| 6. Sub Traversal | 子功能遍历 | 1 | 1 | 1 | 1 |
| 7. Incorrect Command | SF_DL 错误 | 2 | 2 | 2 | 2 |
| 8. NRC Priority | NRC 优先级 | 2 | - | 2 | - |
| **小计** | | **20** | **18** | **20** | **18** |
| **总计** | **76 条** | | | | |
