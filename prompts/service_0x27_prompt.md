# Service 0x27 SecurityAccess — 用例生成规则

## 服务概述

- **Service ID**: 0x27
- **Service Name**: SecurityAccess
- **正响应 SID**: 0x67
- **负响应格式**: `7F 27 <NRC>`
- **子功能成对**: 奇数=RequestSEED, 偶数=SendKEY
- **Seed 长度**: 通常 4 字节（从参数表读取）
- **关键特性**: 复杂的安全机制，包含错误计数器、延时计时器、FAA flag
- **通常不支持功能寻址**
- **NRC 优先级链**：共享 Figure 6，追加 0x35 > 0x36 > 0x37（InvalidKey > ExceededAttempts > TimeDelay）
- **完整链**: 0x13 > 0x12 > 0x7E > 0x33 > 0x24 > 0x35 > 0x36 > 0x37

### 正响应格式

- Seed 响应: `67 <SeedSub> <Seed_H> ... <Seed_L>`（seed 长度按参数定义，通常 4 字节）
- Key 响应: `67 <KeySub>`（仅确认，无额外数据）
- 已解锁态 Seed: `67 <SeedSub> 00 00 00 00`（全零表示已解锁）

### 安全等级与 Seed/Key 映射

| 等级 | Seed 子功能 | Key 子功能 | 说明 |
|------|-----------|-----------|------|
| L1 | 0x01 | 0x02 | Level 1 |
| L2 | 0x03 | 0x04 | Level 2 |
| L3 | 0x05 | 0x06 | Level 3 |
| L4 | 0x07 | 0x08 | Level 4 |
| L5 | 0x09 | 0x0A | Level 5 |

### 典型 NRC — 均在共享 NRC 编码速查表中，此处仅列出 0x27 专有补充

| NRC  | 含义 | 触发条件 |
|------|------|---------|
| 0x35 | InvalidKey | 密钥错误（0x27 专有） |
| 0x36 | ExceededNumberOfAttempts | 超过最大尝试次数（通常 3 次，0x27 专有） |
| 0x37 | RequiredTimeDelayNotExpired | 锁定延时未到期（0x27 专有） |

### 特殊参数

- **FAAflag**: 决定安全计数器在复位后是否保留
  - FAAflag=True: 硬件复位后安全计数器保留（仍为锁定态）
  - FAAflag=False: 硬件复位后安全计数器清零（可重新请求 seed）
- **最大尝试次数**: 通常为 3 次（从参数表读取）
- **锁定延时**: 通常 10 秒（从参数表读取）
- **SPRMIB**: 0x27 通常不支持（0x83/0x84 → NRC 0x12）

---

## 软件域规则（共享规则补充）

- Boot 域的安全等级可能与 APP 域完全不同（如 APP 使用 L1/L2，Boot 使用 LevelFBL）
- Boot 域需要完整镜像 APP 域的 Security Mechanism 测试
- 其余通用规则（APP/Boot 独立生成、用 `---` 分隔、参数表读取）见共享文件

## 寻址规则

- **Physical 寻址**：生成完整测试集
- **Functional 寻址**：0x27 通常不支持功能寻址
  - APP Functional：生成 2 条 No_Response 验证用例（代表性会话）
  - Boot Functional：生成 3 条 No_Response 验证用例（Default/Programming/Extended 各 1 条）

---

## 生成分类（共 10 类）

按以下固定顺序逐类生成，每个分类使用 `## N.N` 作为标题（如 `## 1.1 Session Layer Test`）。

---

### 分类 1: Session Layer Test (APP)
#### 用例数量规则

- 每个会话 × 每个安全等级各 1 条（正向或负向）
- **总数 = Nsession × Nlevel**（通常 Default×L1 + Programming×L1 + Extended×L1 + Extended×L2 + ... ）

#### 用例命名规则

- 负向（会话不支持）：`<CurrentSessionName> Session nonsupport 0x27 Service security access level <LevelName> Negativecase-$27`
  - 示例：`Default Session nonsupport 0x27 Service security access level 1 Negativecase-$27`
- 正向：`<CurrentSessionName> Session support 0x27 Service security access level <LevelName> PositiveResponsecase-$27`

#### 测试步骤模板

**A. 不支持的会话 + 等级**
```
1. 进入 <CurrentSession>
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[<ExpectedResp>];
```

**B. 支持的会话正向**
```
1. 进入 <CurrentSession>
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
3. Send Security Right KeyBy[Physical]Level[<KeySub>];
```

#### Check 规则

> **种子请求的 Check 规则（强制）**：所有种子请求（27 01/03/05/07/09/11）必须使用 `AndCheckResp[PositiveResponse]` 语法，**不在 expected_output 中单独写 Check**——`AndCheckResp` 已内含正响应检查。种子数据为随机值不可预测，禁止写 `Check DiagData[67 XX XX XX XX XX]`。

**A. 不支持的会话：**
- `AndCheckResp` 中使用对应的 NRC 码（`0x7F` 或 `0x7E`），不单独写 Check

**B. 支持的会话正向：**
- 第 2 步（种子）：不单独写 Check（AndCheckResp 已内含检查）
- 第 3 步（密钥）：`Check DiagData[67 <KeySub>]Within[50]ms;`

---

### 分类 2: Secure Access Process Test (APP)
#### 用例数量规则

**固定 ~7 条**

| 序号 | 场景 | 描述 |
|------|------|------|
| 1 | 仅请求 seed，不发 key | 验证未完成解锁流程 |
| 2 | 直接发 key（不请求 seed） | NRC 0x24（序列错误） |
| 3 | 正确流程：seed → key | 完整解锁正向 |
| 4 | 错误流程：key → seed（不可逆） | NRC 序列错误 |
| 5 | 错误流程：key → seed（不同等级） | 交叉等级序列错误 |
| 6 | 重复请求 seed 返回相同数据 | 连续两次请求 seed，ECU 回复相同 seed |
| 7 | 解锁成功后请求 seed 返回全零 | 解锁后再次请求，验证全零 seed |

#### 用例命名规则

描述性命名，如：
- `Does not meet the secure access process, only requests seeds, a negative test case where secure access cannot be unlocked`
- `Does not meet the secure access process, only sending the key; a negative test case`
- `Meet the secure access process: request the seed first, then send the key – a PositiveResponse use case`
- `Failure to comply with the secure access process: sending the key first, then requesting the seed`
- `Repeated seed requests return the same seed data - PositiveResponse`
- `After successful unlock, request seed returns all zeros - PositiveResponse`

#### 测试步骤模板

**A. 仅请求 seed：**
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
```
> 种子请求使用 `AndCheckResp[PositiveResponse]`，不在 expected_output 中单独写 Check。

**B. 直接发 key：**
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 <KeySub>];
```
Check: `Check DiagData[7F 27 24]Within[50]ms;`

**C. 正确流程：**
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
3. Send Security Right KeyBy[Physical]Level[<KeySub>];
```
Check: `Check DiagData[67 <KeySub>]Within[50]ms;`

**D. 错误流程（key→seed）：**
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 <KeySub>];
3. Send DiagBy[Physical]Data[27 <SeedSub>];
```
Check: 第 2 步 NRC，第 3 步也可能 NRC

**E. 重复请求 seed 返回相同数据：**
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
3. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
```
Check: 第 2 步和第 3 步 ECU 返回的 seed 数据完全相同（`67 <SeedSub> <SeedData>` 一致）

**F. 解锁成功后请求 seed 返回全零：**
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
3. Send Security Right KeyBy[Physical]Level[<KeySub>];
4. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
```
> 步骤 2/4 为种子请求，使用 `AndCheckResp[PositiveResponse]` 已内含检查，不在 expected_output 中单独写 Check。步骤 4 的 expected_output 中**不写** `Check DiagData[67 XX XX XX XX XX]`。

---

### 分类 3: Security Access Mechanism Test (APP)

> 最复杂的分类，验证安全机制的完整行为。分两条路径测试：
> - **路径 A: 错误密钥路径**（WrongKey → FAAcounter → TimerLocked）
> - **路径 B: 连续请求 seed 路径**（RequestSeed × N → FAAcounter → TimerLocked）

#### 用例数量规则

**路径 A（错误密钥）和路径 B（连续 seed）各生成一套完整测试：**

| 子类 | 每条路径数量 | 描述 |
|------|-----------|------|
| A1/B1: 最大尝试次数触发 | 1 | 3次错误/seed → NRC 0x36（第3次）/ 0x37（之后） |
| A2/B2: 锁定后等待延时 | 1 | 等待 10s 后可重新请求 |
| A3/B3: 锁定后不等待延时 | 1 | 不等待 10s → NRC 0x37 |
| A4/B4: 锁定后成功解锁重置 | 1 | 成功解锁 1 次 → counter 清零 |
| A5/B5: FAAflag=True 复位后 counter 保留 | 1 | Power Reset 后 counter=3 |
| A6/B6: FAAflag=False 复位后 counter 清零 | 1 | Power Reset 后 counter=0 |
| A7/B7: Hardware Reset + 延时 | 1 | 复位后延时到可请求 |
| A8/B8: 连续第 N 次触发锁定 | 1 | 第 4 次触发 |

**每条路径 ~8 条，两条路径共 ~16 条**

#### 用例命名规则

**路径 A（错误密钥）：**
- `Meets the maximum of 3 failed attempts; does not meet the reverse test case with a lockout time of 10 seconds`
- `A PositiveResponse test case that meets a maximum of 3 failed attempts and a lockout duration of 10 seconds`
- `A negative test case where the maximum number of secure access attempts (with incorrect keys) is reached and the 10-second delay has not expired`
- `When the maximum number of safe access attempts (wrong key) = 4 is reached, successfully unlock once`
- `SAcounter equals 3 after reset when FAAflag = True - PositiveResponse`
- `SAcounter after reset when FAAflag = False - PositiveResponse`
- `Hardware reset enabled 10s delay time - PositiveResponse`
- `Reverse test case for reaching the maximum number of safe access attempts (wrong key) and the 10-second delay`

**路径 B（连续 seed）：类似命名，将 "wrong key" 替换为 "request seed"**

#### 测试步骤模板

**路径 A: 错误密钥**

A1: 最大尝试次数触发
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
3. Send Security Wrong KeyBy[Physical]Level[<KeySub>];（第1次错误）
4. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
5. Send Security Wrong KeyBy[Physical]Level[<KeySub>];（第2次错误）
6. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
7. Send Security Wrong KeyBy[Physical]Level[<KeySub>];（第3次错误 → 0x36）
8. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[0x37];（锁定后 → 0x37）
```

A2: 等待延时后可请求
```
（接 A1 之后）
Delay[10000]ms;
Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];（→ 正常返回 seed）
```

A5: FAAflag=True 复位
```
1. 触发 3 次错误密钥
2. Set Voltage[0]V; Delay[1000]ms;
3. Set Voltage[12]V; Delay[1000]ms;
4. 进入会话
5. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[0x37];（→ 0x37，counter 保留）
```

A6: FAAflag=False 复位
```
同 A5，但第 5 步 → 正常返回 seed（counter 清零）
5. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
```

**路径 B: 连续 seed 请求**

B1: 最大 seed 请求次数
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];（第1次，正常）
3. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];（第2次，正常）
4. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];（第3次，正常）
5. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[0x36];（第4次 → 0x36）
```

B2-B8: 类似 A2-A8 但使用连续 seed 请求路径

#### Check 规则

> **种子/密钥步骤均使用 AndCheckResp 语法，不在 expected_output 中单独写 Check。**

- 第 1-2 次错误密钥：AndCheckResp 内含 `7F 27 35`（InvalidKey），不单独写 Check
- 第 3 次错误密钥：AndCheckResp 内含 `7F 27 36`（ExceededAttempts），不单独写 Check
- 锁定后请求种子：AndCheckResp 内含 `7F 27 37`（TimeDelay），不单独写 Check
- 延时到期后请求种子：AndCheckResp 内含 `PositiveResponse`（正常返回 seed），不单独写 Check
- FAAflag=True 复位后请求种子：AndCheckResp 内含 `7F 27 37`（counter 保留），不单独写 Check
- FAAflag=False 复位后请求种子：AndCheckResp 内含 `PositiveResponse`（正常返回 seed），不单独写 Check

---

### 分类 4: Secure Access Time Test (APP)

#### 用例数量规则

**固定 1 条**（解锁后安全状态持续时间）

#### 用例命名规则

`Duration after unlocking: 5s - PositiveResponse Response Case-$27`

#### 测试步骤模板

```
1. 进入 Extended 会话
2. 完成 seed/key 解锁
3. Delay[<S3 - delta>]ms;（如 4900ms）
4. Send DiagBy[Physical]Data[3E 00];（TesterPresent 维持会话）
5. Delay[<S3 - delta>]ms;
6. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];（检查安全状态）
```

#### Check 规则

- 第 6 步（种子）：不单独写 Check（AndCheckResp 已内含检查）——**禁止**写 `Check DiagData[67 <SeedSub> 00 00 00 00]`

---

### 分类 5: ECU Reset Test (APP)

#### 用例数量规则

**固定 4 条**

| 复位方式 | 数量 |
|---------|------|
| Power Reset | 1 |
| Hardware Reset(11 01) | 1 |
| Session Switch（10 01） | 1 |
| Software Reset(11 03) | 1 |

#### 用例命名规则

- Power: `ECU power reset Session returns to the DefaultSession PositiveResponseCase-$27`
- Hardware: `ECU Hardware reset Session returns to the DefaultSession PositiveResponseCase-$27`
- Session Switch: `Switch default Session 0x27 Security access level reset NegativeCase-$27`
- Software Reset: `Software reset, security access function normal request to the seed PositiveResponsecase-$27`

#### 测试步骤模板

**A. Power Reset：**
```
1. 进入 Extended 会话
2. 完成 seed/key 解锁
3. Set Voltage[0]V; Delay[1000]ms;
4. Set Voltage[12]V; Delay[1000]ms;
5. 进入 Extended 会话
6. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[<ExpectedResp>];
```
> 根据 FAAflag 安全状态，`<ExpectedResp>` 为 `PositiveResponse`（FAAflag=False，counter 清零）或 `0x37`（FAAflag=True，counter 保留）。

**B. Hardware Reset(11 01)：**
```
1. 进入 Extended 会话
2. 完成 seed/key 解锁
3. Send DiagBy[Physical]Data[11 01]; Delay[2000]ms;
4. 进入 Extended 会话
5. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[<ExpectedResp>];
```
> 同 Power Reset，`<ExpectedResp>` 根据 FAAflag 取值。

**C. Session Switch：**
```
1. 进入 Extended 会话
2. 完成 seed/key 解锁
3. Send DiagBy[Physical]Data[10 01];（切回 Default → 安全状态重置）
4. Send DiagBy[Physical]Data[10 03];
5. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];（→ 非全零 seed，已锁定）
```

**D. Software Reset(11 03)：**
```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];（验证正常请求 seed）
```

---

### 分类 6: SPRMIB Test (APP)
#### 用例数量规则

**固定 1 条**（0x27 不支持 SPRMIB）

#### 用例命名规则

`The 0x27 nonsupport SPRMIB Negativecase-$27`

#### 测试步骤

```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 83];（SPRMIB 版本）
3. Send DiagBy[Physical]Data[27 84];
```

Check: `Check DiagData[7F 27 12]Within[50]ms;`（子功能不支持）

---

### 分类 7: Incorrect Diagnostic Command Test (APP)
#### 用例数量规则

**固定 2 条**

| 序号 | 错误类型 | 描述 |
|------|---------|------|
| 1 | SF_DL > 2 | 有效负载长度大于合法值 |
| 2 | SF_DL < 2 | 有效负载长度小于合法值 |

#### 用例命名规则

1. `Valid SF_DL=2, invalid SF_DL > 2, and those with invalid equivalence class SF_DL=3 NegativeCase-$27`
2. `Valid SF_DL=2, invalid SF_DL < 2, and those with invalid equivalence class SF_DL=1 NegativeCase-$27`

#### 测试步骤模板

**前置步骤：** 进入 Extended 会话

**A. SF_DL > 2**
```
Send DiagBy[Physical]Data[27 03]WithLen[3];
```

**B. SF_DL < 2**
```
Send DiagBy[Physical]Data[27]WithLen[1];
```

#### Check 规则

| 错误类型 | Expected Output |
|---------|----------------|
| SF_DL > 2 | `Check DiagData[7F 27 13]Within[50]ms;` |
| SF_DL < 2 | `Check DiagData[7F 27 13]Within[50]ms;` |

---

### 分类 8: NRC Priority Test (APP)
#### 用例数量规则

**固定 1 条**

#### 用例命名规则

`NRC 13>12>37>22`

#### 测试步骤

```
1. 进入 Extended 会话
2. Send DiagBy[Physical]Data[27 01]WithLen[1];（长度错误 + 不支持的子功能组合）
```

#### Check 规则

- `Check DiagData[7F 27 13]Within[50]ms;`（NRC 0x13 优先于 0x12）

---

### 分类 9: Boot Domain Test

Boot 域生成与 APP 域类似结构的测试集，但有以下差异：

#### Boot 域差异

| 项目 | APP 域 | Boot 域 |
|------|--------|---------|
| 安全等级 | 从参数表读取（如 L1/L2） | 从 Boot 参数表读取（如 L2/L4） |
| 会话支持 | Default(不支持) + Extended(支持) | Default/Programming/Extended 可能不同 |
| 进入路径 | `10 03` 直接进入 Extended | `10 03 → 31 01 02 03 → 10 02` 进入 Programming |

#### Boot 域子分类

1. **Boot Session Layer**: 每个会话 × 每个安全等级
   - 不支持的会话/等级组合 → NRC
   - 支持的组合 → seed/key 正向
2. **Boot SPRMIB**: 固定 1 条（0x27 不支持 SPRMIB）
3. **Boot Secure Access Process**: 与 APP 相同结构（seed-only, key-only, correct flow, wrong flow）
4. **Boot Security Mechanism**: 与 APP 相同的两条路径（错误密钥 + 连续 seed），但使用 Boot 安全等级
5. **Boot Secure Access Time**: 1 条
6. **Boot ECU Reset**: 4 条（Power/Hardware/SessionSwitch/InvalidKey）
7. **Boot Incorrect Command**: 2 条 SF_DL
8. **Boot NRC Priority**: 1 条

#### Boot Session Layer 测试步骤示例

**Default Session（不支持）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[0x7F];
```

**Programming Session（如不支持 L1）：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Send DiagBy[Physical]Data[31 01 02 03];
3. Send DiagBy[Physical]Data[10 02];
4. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[0x12];
```

**Extended Session（支持 L2）：**
```
1. Send DiagBy[Physical]Data[10 03];
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];
3. Send Security Right KeyBy[Physical]Level[<KeySub>];
```

---

### 分类 10: Functional Addressing Test

#### APP Functional

**固定 2 条**（0x27 通常不支持功能寻址）

```
1. Default Session: Send DiagBy[Function]Data[27 01]; → No_Response
2. Extended Session: Send DiagBy[Function]Data[27 03]; → No_Response
```

#### Boot Functional

**固定 3 条**（Default/Programming/Extended 各 1 条）

```
1. Default: Send DiagBy[Function]Data[27 <SeedSub>]; → No_Response
2. Programming: Send DiagBy[Function]Data[27 <SeedSub>]; → No_Response
3. Extended: Send DiagBy[Function]Data[27 <SeedSub>]; → No_Response
```

#### Check 规则

- 所有 Functional 用例：`Check No_Response Within[1000]ms;`

---

## 会话进入标准路径

见共享文件。0x27 无额外覆盖规则。

---

## 输出格式要求

见共享文件。额外规则：**每个分类标题使用 `## N.N` 格式**，如 `## 1.1 Session Layer Test`、`## 1.2 Secure Access Process Test`。

### 步骤序号强制规则（重要）

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

**正确格式示例（以 session 进入 + seed/key 解锁为例）：**
```
test_procedure:
  1.Send DiagBy[Physical]Data[10 01];
  2.Delay[1000]ms;
  3.Send DiagBy[Physical]Data[10 03];
  4.Send DiagBy[Physical]Data[27 01]AndCheckResp[PositiveResponse];
  5.Send Security Right KeyBy[Physical]Level[02];

expected_output:
  1.Check DiagData[50 01 XX XX XX XX]Within[50]ms;
  3.Check DiagData[50 03 XX XX XX XX]Within[50]ms;
  5.Check DiagData[67 02]Within[50]ms;
```
说明：步骤 2（Delay）无 Check 跳过；步骤 4 为种子请求使用 `AndCheckResp` 已内含检查，不在 expected_output 中单独列出；步骤 5 为密钥请求，Check 写 `67 <KeySub>`（仅 1 字节确认）。序号 1/3/5 对应 test_procedure 中对应步骤编号。

### 种子请求（Seed）处理规则（强制）

> **所有种子请求（27 <SeedSub>，即 27 01 / 27 03 / 27 05 / 27 07 / 27 09 / 27 11）必须使用 `AndCheckResp[PositiveResponse]` 或 `AndCheckResp[<NRC>]` 语法，**严禁**在 expected_output 中单独写 Check 检查种子响应数据。**

**原因**：种子数据由 ECU 随机生成（通常 4 字节），测试端不可预测其具体值，无法精确写入 `Check DiagData[67 XX XX XX XX XX]`。

**规则：**
1. 种子请求正响应：`Send DiagBy[Physical]Data[27 01]AndCheckResp[PositiveResponse];`
2. 种子请求负响应：`Send DiagBy[Physical]Data[27 01]AndCheckResp[0x37];`（示例：锁定后返回 0x37）
3. expected_output 中**不出现**种子步骤的 Check 行（编号跳过）

**禁止格式示例（错误）：**
- `test_procedure: 2.Send DiagBy[Physical]Data[27 01];` 配合 `expected_output: 2.Check DiagData[67 01 XX XX XX XX]Within[50]ms;`（**严禁**：种子数据不可预测，且 AndCheckResp 已处理）

**正确格式示例：**
- `test_procedure: 2.Send DiagBy[Physical]Data[27 01]AndCheckResp[PositiveResponse];` → expected_output 中**不写**第 2 步的 Check
- `test_procedure: 5.Send DiagBy[Physical]Data[27 03]AndCheckResp[0x37];` → expected_output 中**不写**第 5 步的 Check
**错误格式示例（禁止）：**
- `test_procedure` 中混入 Check 语句（如 `2.Check DiagData[...]`）——Check 必须在 `expected_output`
- `expected_output` 只写最后一条 Check，忽略前面所有步骤的 Check
- 使用 `Step1:` 格式（禁止，必须用 `1.`）
- 序号与内容之间有空格（`1. Send` 禁止，必须是 `1.Send`）

## 生成注意事项

> 通用规则（Case ID 不可重复、pipe table 格式、`<br>` 换行、每 Send 有 Check 等）见共享文件。

1. **编号从 001 开始**，顺序为：APP Physical → APP Functional → Boot Physical → Boot Functional
2. **安全等级映射必须从参数表读取**，不写死
3. **错误密钥序列**: 35 → 35 → 36 → 37（2 次 InvalidKey 后第 3 次 ExceededAttempts）
4. **SPRMIB 0x83/0x84 返回 NRC 0x12**
5. **FAAcounter = 3 后锁定，只有成功 Unlock 或 TimerLocked 超时才能清零**
6. **Boot 域必须完整镜像 APP 域的 Security Mechanism 测试**
7. **ECU Reset 包含 Software Reset(11 03)**

---

## 分类汇总

| 分类 | 描述 | APP Physical | APP Functional | Boot Physical | Boot Functional |
|------|------|-------------|---------------|--------------|----------------|
| 1. Session Layer | 会话 × 等级 | ~6 | - | ~6 | - |
| 2. Secure Access Process | seed/key 流程 | ~7 | - | ~7 | - |
| 3. Security Mechanism | 错误密钥 + 连续 seed（双路径） | ~16 | - | ~16 | - |
| 4. Secure Access Time | 解锁后持续时间 | 1 | - | 1 | - |
| 5. ECU Reset | 4种复位 | 4 | - | 4 | - |
| 6. SPRMIB | 不支持 SPRMIB | 1 | - | 1 | - |
| 7. Incorrect Command | SF_DL 错误 | 2 | - | 2 | - |
| 8. NRC Priority | NRC 优先级 | 1 | - | 1 | - |
| 9. Boot Domain | Boot 完整测试 | - | - | (above) | - |
| 10. Functional | No_Response | - | 2 | - | 3 |
| **小计** | | **~40** | **2** | **~39** | **3** |
| **总计** | **~84 条** | | | | |
