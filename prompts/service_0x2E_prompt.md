# Service 0x2E WriteDataByIdentifier — 用例生成规则

## 服务概述

- **Service ID**: 0x2E
- **Service Name**: WriteDataByIdentifier
- **请求格式**: `2E <DID_H> <DID_L> <WriteData...>`
- **无 Subfunction**（DID 替代子功能角色）
- **合法 SF_DL**: 3 + ByteLength（SID + DID + 数据）
- **关键特性**: 不存在 NRC 0x12；写入数据需用 DefaultValue 填充；0x20 填充未使用字节
- **NRC 优先级链（服务级，Figure 0x2E 专用）**:

> **关键规则**：以下为 0x2E 服务的**完整** NRC 优先级链模板。实际生成时必须从参数表 `Negative response codes` 字段读取精确的 NRC 列表和顺序，**参数表声明了哪些 NRC 就覆盖哪些**。

| 优先级 | NRC | 触发条件 |
|--------|-----|---------|
| 1 | 0x13 | 长度错误（最小长度/总长度不匹配） |
| 2 | 0x11 | 服务不支持（ECU 全局不支持 0x2E 服务时） |
| 3 | 0x7F | 服务在当前会话不支持 |
| 4 | 0x31 | DID 不支持写入 / 数据记录内容无效 |
| 5 | 0x33 | 安全访问未解锁 |
| 6 | 0x22 | DID 前提条件不满足 |
| 7 | 0x72 | 写入服务器内存失败（0x2E 专有） |
| 8 | 0xXX | 厂商/供应商自定义 |

**NRC 全覆盖要求**：参数表 `Negative response codes` 字段中列出的**每一个** NRC 都必须有至少一条专用测试用例。常用覆盖策略：
- **0x13**：Incorrect Diagnostic Command（分类 4）覆盖
- **0x11**：若参数表声明，Session Layer 覆盖（服务不支持）
- **0x7F**：Session Layer 覆盖（当前会话不支持 0x2E 服务）
- **0x31**：Session Layer 覆盖（不可写的 DID，Write Support=N）
- **0x33**：Session Layer 覆盖（未解锁时写入需安全等级的 DID）
- **0x22**：DID 前提条件不满足时覆盖
- **0x72**：写入服务器内存失败时覆盖（如写入超出允许范围的数据）

### 正响应格式

- `6E <DID_H> <DID_L>`（仅确认，不回显数据）

---

### 负响应格式

- `7F 2E <NRC>`（UDS 标准负响应）

---

## 预期输出格式规则（强制）

> **关键规则**：`expected_output` 字段必须使用完整的 `Check` 函数格式，**绝对禁止**使用裸 hex 字节或 `StepX:` 简化格式。

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
1. Check DiagData[50 03 00 32 01 F4]Within[50]ms;<br>4. Check DiagData[6E F1 0A]Within[50]ms;<br>6. Check DiagData[62 F1 0A 11 11 11 ...]Within[50]ms;
```

**错误格式示例（禁止）：**
- `Step2: 50 03 00 32 01 F4` ❌ — 禁止 `StepX:` 前缀
- `2. 50 03 00 32 01 F4` ❌ — 缺少 `Check DiagData[...]Within[50]ms;` 包装
- `step2: 7F 2E 33` ❌ — 禁止 `stepX:` 前缀 + 缺少 Check 包装
- `2.Check DiagData[50 03...]` ❌ — 序号与内容之间必须有空格（如 `2. Check...`）

---

## 生成分类（共 4 类）

按以下固定顺序逐类生成，每个分类使用 `## N.N` 作为标题（如 `## 1.1 Session Layer Test`）。

---

### 分类 1: Session Layer Test

#### 用例数量规则

- `Npos` = 可写 DID × 支持的会话数（Write Support = Y 的 DID）
- `Nneg_did` = 不可写 DID case 数（Write Support = N）
- `Nneg_sess` = 不支持的会话 case 数
- **总数 = Npos + Nneg_did + Nneg_sess**

#### 用例命名规则

- 正向：`<CurrentSessionName> Session support the 0x2E service write DID 0x<DID>`
  - 示例：`Extended Session support the 0x2E service write DID 0xF101`
- 负向（DID 不可写）：`DID 0x<DID> does not support write operation`
- 负向（会话不支持）：`<CurrentSessionName> Session nonsupport 0x2E service write DID 0x<DID>`

#### 测试步骤模板

**A. 不支持的会话（如 Default）**
```
1. 进入 Default 会话
2. Send DiagBy[Physical]Data[2E <DID_H> <DID_L> <WriteData>];
```

**B. 支持会话但未解锁（Access Level 限制）**
```
1. 进入支持的会话（Extended）
2. Send DiagBy[Physical]Data[2E <DID_H> <DID_L> <WriteData>];
```

**C. 不可写的 DID（Write Support = N）**
```
1. 进入支持的会话
2. Send DiagBy[Physical]Data[2E <DID_H> <DID_L> <WriteData>];
```

#### Check 规则

**A. 不支持的会话：**
- `Check DiagData[7F 2E 7F]Within[50]ms;`

**B. 支持会话但未解锁：**
- `Check DiagData[7F 2E 33]Within[50]ms;`（Security Access Denied）

**C. 不可写的 DID：**
- `Check DiagData[7F 2E 31]Within[50]ms;`（Request Out Of Range）

#### 数据填充规则

| 场景 | 填充方式 |
|------|---------|
| DID 有 DefaultValue | 使用 DefaultValue（如 0x11 重复 ByteLength 次） |
| DID 有未使用位 | 使用 0x20（空格）填充 |
| 示例 DID 0xF101 | 17 字节，写入数据 = `11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11` |

---

### 分类 2: Secure Access Test

#### 用例数量规则

- 仅对 Write Access Level 包含安全限制的 DID 生成
- **总数 = N_did_write_need_security**

#### 用例命名规则

`Security access Lx unlock supports 0x2E service write DID 0x<DID>`
- 示例：`Security access L2 unlock supports 0x2E service write DID 0xF101`

#### 测试步骤模板

```
1. 进入支持的会话（通常 Extended）
2. Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PostiveResponse];
3. Send Security Right KeyBy[Physical]Level[<KeySub>];
4. Send DiagBy[Physical]Data[2E <DID_H> <DID_L> <WriteData>];
5. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
```

#### Check 规则

- 第 3 步：`Check DiagData[67 <KeySub>]Within[50]ms;`
- 第 4 步：`Check DiagData[6E <DID_H> <DID_L>]Within[50]ms;`
- 第 5 步：`Check DiagData[62 <DID_H> <DID_L> <WrittenData>]Within[50]ms;`（读回验证数据一致）

#### 特殊规则

1. 安全等级从 DID 表的 Write Access Level 字段读取
2. 写入后应使用 0x22 读回验证数据一致性
3. 仅对 Write Support = Y 的 DID 生成

---

### 分类 3: DID Storage Test（写入持久化验证）

#### 用例数量规则

- 仅对 Storage = EEPROM/FLASH（非易失性存储）的 DID 生成
- **总数 = N_did_nonvolatile**

#### 用例命名规则

`DID 0x<DID> write data persistence after power reset`
- 示例：`DID 0xF101 write data persistence after power reset`

#### 测试步骤模板

```
1. 进入支持的会话（Extended）
2. 完成安全解锁
3. Send DiagBy[Physical]Data[2E <DID_H> <DID_L> <TestData>];
4. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
5. Set Voltage[0]V;
6. Delay[1000]ms;
7. Set Voltage[12]V;
8. Delay[1000]ms;
9. Send DiagBy[Physical]Data[10 03];
10. Send DiagBy[Physical]Data[22 <DID_H> <DID_L>];
```

#### Check 规则

- 第 3 步：`Check DiagData[6E <DID_H> <DID_L>]Within[50]ms;`
- 第 4 步：`Check DiagData[62 <DID_H> <DID_L> <TestData>]Within[50]ms;`（写入后读回一致）
- 第 10 步：`Check DiagData[62 <DID_H> <DID_L> <TestData>]Within[50]ms;`（断电后仍一致）

#### 特殊规则

1. 仅对非易失性存储（EEPROM/FLASH）的 DID 才需要此测试
2. RAM 存储的 DID 断电后数据丢失，不做持久化验证
3. 测试完成后必须写回原始值（恢复出厂值）
4. 步骤 5-8 为电源复位，步骤 9 重新进入会话

---
### 分类 4: NRC Coverage & Priority Test（NRC全覆盖与优先级测试）

> **【强制】NRC 全量覆盖**：参数表 `Negative response codes` 字段声明的**每一个 NRC** 都必须有至少一条专用测试用例。本分类负责验证 NRC 优先级链中相邻 NRC 的优先级关系，并确保未被其他分类覆盖的 NRC 有独立用例。

#### 用例数量规则

- **NRC 优先级链中相邻 NRC 对的数量** + **未被其他分类独立覆盖的 NRC 数量**
- 每个相邻 NRC 对生成 1 条用例

#### 测试步骤模板

**NRC 优先级验证（以完整链 `13>11>7F>31>33>22>72` 为例，实际按参数表筛选）：**

**用例 1：验证 0x13 > 0x31**
```
1. 进入支持的会话（Extended）
2. Send DiagBy[Physical]Data[2E <DID_H>]WithLen[2];（长度错误 + DID 可选不支持）
```
预期：`Check DiagData[7F 2E 13]Within[50]ms;`

**NRC 0x72 专用覆盖（若参数表声明）：**
```
1. 进入支持的会话（Extended）
2. 完成安全解锁
3. Send DiagBy[Physical]Data[2E <DID_H> <DID_L> <InvalidWriteData>];（写入非法数据）
```
预期：`Check DiagData[7F 2E 72]Within[50]ms;`

**NRC 0x11 专用覆盖（若参数表声明）：**
```
1. 进入不支持 0x2E 服务的会话
2. Send DiagBy[Physical]Data[2E <DID_H> <DID_L> <WriteData>];
```
预期：`Check DiagData[7F 2E 11]Within[50]ms;`

**NRC 0x7F 专用覆盖（若参数表声明）：**
```
1. 进入不支持 0x2E 服务的会话
2. Send DiagBy[Physical]Data[2E <DID_H> <DID_L> <WriteData>];
```
预期：`Check DiagData[7F 2E 7F]Within[50]ms;`

**NRC 0x22 专用覆盖（若参数表声明）：**
```
1. 进入支持的会话（Extended）
2. 在 DID 前提条件不满足时（如车速=0 而要求车速>0）发送写入请求
```
预期：`Check DiagData[7F 2E 22]Within[50]ms;`

#### Check 规则

- 每条 NRC 优先级用例验证一对相邻 NRC，同时触发两个条件时返回优先级更高的 NRC
- 独立 NRC 覆盖用例验证单一 NRC 可被正确触发

---

## 功能寻址用例生成规则

当 `Functional Request = 支持` 时：
1. 将所有 Physical 用例复制一份,物理寻址不需要回复NRC包含[0x11 (服务不支持),0x12 (子功能不支持),0x7F (当前会话服务不支持),0x7E (当前会话子功能不支持),0x31 (请求超出范围)]，此时不需要响应 <Check No_Response within [P2 server]ms;>
2. 发送函数中 `[Physical]` 改为 `[Function]`
3. Case ID 中 `Phy` 改为 `Fun`，编号重新从 001 开始

当 `Functional Request = 不支持` 时（0x2E 典型情况）：
- 仅生成 1 条 No_Response 验证用例

---

## DID 写入数据填充规则

| 场景 | 填充方式 |
|------|---------|
| DID 有 DefaultValue | 使用 DefaultValue |
| DID 未使用位 | 使用 0x20（空格 ASCII）填充 |
| 字符串型 DID | 使用 0x11 或实际字符串 |
| 数值型 DID | 使用实际值或 xx |

---

## 生成注意事项

1. **写入后必须用 0x22 读回验证**，确认数据一致性
2. **【强制】DID 列表必须且仅能从 DID 表读取**，Write Support = Y 的 DID 才生成正向写入 case。DID 表是 0x2E 服务的唯一合法数据源，**绝对禁止从 Routine Control 表或其他 Sheet 交叉引用标识符**
3. **【强制】绝对禁止使用 DID 表中未声明的 DID 发送写入请求并设置预期响应**——包括正向用例和负向用例。不支持的 DID 测试（NRC 0x31）只能使用 `0xFFFF` 或 `0x0000` 等明显非法值，禁止使用表中不存在的"看起来合法"的 DID
4. **0x2E 无子功能概念**，不存在 NRC 0x12，不可写的 DID 返回 NRC 0x31
5. **未解锁写入返回 NRC 0x33**（Security Access Denied）
6. **持久化测试后必须恢复原始值**
7. **App 域和 Boot 域的 DID 列表必须分别从各自域的参数表读取**，不得混用
8. **若 DID 表为空或无 Write Support = Y 的 DID，则所有正向用例数为 0**，仅生成 Incorrect Command / NRC Priority 等不依赖具体 DID 的用例
9. **【强制】NRC 全量覆盖自检**：生成完所有用例后，必须逐一核对参数表 `Negative response codes` 字段声明的每一个 NRC（0x11、0x7F、0x13、0x31、0x33、0x72、0x22 等）是否都有至少一条专用测试用例。漏掉任何一个已声明 NRC 均为不合格输出。
